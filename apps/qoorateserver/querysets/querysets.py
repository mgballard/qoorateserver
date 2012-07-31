#!/usr/bin/env python
import pymysql
import json
import logging
import os
import imp

from brubeck.queryset import AbstractQueryset
import dictshield
from dictshield.fields import mongo as MongoFields
from dictshield.fields import compound as CompoundFields
from brubeckmysql.querysets import MySqlQueryset, MySqlApiQueryset

from qoorateserver.models.models import Comment, Image, User, Qoorate, CommentItem, Vote, Flag, KeyPair, Qoorate

###
### All of our application specific data interaction with any data store happens in a Queryset object
###

class CommentItemQueryset(MySqlQueryset, AbstractQueryset):
    """ This may be a bit overkill for the comments item which is simply a view
        But, we should still be in a Queryset object for standards sake
        TODO: We really wont be implementing any of the autoAPI things, or maybe we will..
        Should this be what really creates posts and the sorts? hmmm...probably not, should be in the handler
    """

    def __init__(self, settings, table_name, db_conn, **kw):
        """We may want to resuse a db_conn, not sure yet
           We need to pass the tablename since it may be different
           based on the API key
        """
        super(CommentItemQueryset, self).__init__(settings, db_conn=db_conn)
        if table_name==None:
            raise Exception('table_name required parameter for CommentItemQueryset')
        self.table_name = table_name
        self.image_queryset = ImageQueryset(settings, self.table_name + '_images', db_conn=db_conn);



    def load_comments_by_table_and_location(self, table, location=None, parentOffset=1, parentCount=0, childOffset=1, childCount=0, parentId=None, sortOrder = 'voteNumber', dateOrder = 'ASC', voteOrder = 'DESC', flagTypeId=None):
        """Loads comment"""
        self.init_db_conn()

        params_dict = dict()

        if voteOrder == None:
            voteOrder = 'DESC'

        if sortOrder == None:
            sortOrder = 'voteNumber'

        if dateOrder == None:
            dateOrder = 'ASC'

        if flagTypeId == None:
            flag_join_sql = ''
            flag_group_by_clause = ''
        else:
            flag_join_sql = "JOIN flag fl on fl.itemId=s0.id and fl.flagTypeId=%s" % flagTypeId
            flag_group_by_clause = " GROUP BY s0.id"

        # if we only want the parent, return all, we may not know the real offset
        if parentId != None:
            parentCount = 0

        logging.debug(parentOffset)
        logging.debug(parentCount)

        parentRangeTop    = 0 if parentCount == 0 else parentOffset + parentCount
        childRangeTop     = 0 if childCount == 0 else childOffset + childCount

        parent_where_clause = ''
        if parentId != None:
            parent_where_clause = " AND (parentId = %s or id = %s) " % (parentId, parentId)

        # our order options
        order = {'dateOrder': dateOrder, 'voteOrder': voteOrder}
        groupOrder = '';

        if sortOrder == 'voteNumber':
            groupOrder = """
                s0.groupVoteNumber %(voteOrder)s,
                s0.groupVoteCount %(voteOrder)s,
                s0.groupCreateDate %(dateOrder)s,
                """ % order
            childOrder = """
                s0.voteNumber %(voteOrder)s,
                s0.voteCount %(voteOrder)s,
                s0.createDate %(dateOrder)s
                """ % order
        elif sortOrder == 'createDate':
            groupOrder = """
                s0.groupCreateDate %(dateOrder)s,
                s0.groupVoteNumber %(voteOrder)s,
                s0.groupVoteCount %(voteOrder)s,
                """ % order
            childOrder = """
                s0.createDate %(dateOrder)s,
                s0.voteNumber %(voteOrder)s,
                s0.voteCount %(voteOrder)s
                """ % order

        params_dict = {
            'table': table,
            'location': location,
            'parentRangeTop': parentRangeTop,
            'parentOffset': parentOffset,
            'parentRangeTop': parentRangeTop,
            'childOffset': childOffset,
            'childRangeTop': childRangeTop,
            'parent_where_clause': parent_where_clause,
            'flag_join_sql': flag_join_sql,
            'flag_group_by_clause': flag_group_by_clause,
            'groupOrder': groupOrder,
            'childOrder': childOrder,
        }

        sql = """
            SELECT f.`parent_sequence` , f.`child_sequence` , f.`id` , f.`locationId` , f.`relatedId`,
                f.`parentId` , f.`userId` , `u`.`username`, u.`thumbnailLarge` as userThumbnailLarge,
                ur.`username` as relatedUsername, ur.`thumbnailLarge` as relatedUserThumbnailLarge, f.`type`,
                f.`name` , f.`location` ,f.`description`,
                f.`voteCount` , f.`voteNumber` , f.`votesUp` ,f.`votesDown` , f.`flagCount`,  f.`childCount`, f.`sortOrder` , f.`status`,
                f.`thumbnailSmall` ,f.`thumbnailLarge` , f.`changeDate` , f.`createDate`
            FROM (
                # this query adds the sequence fields to filter by for paging
                SELECT  s1.*, @parentrownum := convert( IF( ( parentId = 0), @parentrownum +1, @parentrownum ), UNSIGNED INTEGER) AS parent_sequence,
                @childrownum := IF( ( @lastparent = parentId), @childrownum + 1, 0 ) AS child_sequence,
                @lastparent := if( parentId=0, id, parentId ) AS dummy_used_for_last_parent
                FROM
                    # QUERY 2: this query sorts the results properly
                    (SELECT s0.* FROM
                        # QUERY 1: This query gets the results we need with calculated fields to sort by
                        # We should probably have these fields in the database so they are indexed
                        (SELECT
                        CONVERT( if( parentId = 0, @parentVoteNumber:=voteNumber,
                            @parentVoteNumber ), SIGNED INTEGER ) as groupVoteNumber,          # Will order groups using parent voteNumber
                        CONVERT( if( parentId = 0, @parentVoteCount:=voteCount,
                            @parentVoteCount ), SIGNED INTEGER ) as groupVoteCount,            # Will order groups using parent voteCount
                        CONVERT( if( parentId = 0, @parentCreateDate:=createDate,
                            @parentCreateDate ), DATETIME ) as groupCreateDate,                # Will order groups using parent createDate
                        CONVERT( if(parentId=0, id, parentId), UNSIGNED INTEGER) as groupId,   # will order groups together
                        CONVERT( if(parentId = 0, 0, 1), UNSIGNED INTEGER) as isChild,         # will order parent first in group
                        r.*
                        FROM (
                            # this just makes sure our groups are grouped in parent child order
                            SELECT * from %(table)s o WHERE o.location = '%(location)s' ORDER BY
                             if( o.relatedId = 0, o.id, o.relatedId),
                             if( o.relatedId = 0, 0, o.id )
                            ) r,
                        ( SELECT @parentVoteNumber := 0 ) pvn,
                        ( SELECT @parentVoteCount  := 0 ) pvc,
                        ( SELECT @parentCreateDate := 0 ) pcd
                        WHERE location = '%(location)s' %(parent_where_clause)s
                    ) s0
                    %(flag_join_sql)s
                    %(flag_group_by_clause)s
                    ORDER BY
                    %(groupOrder)s 
                    groupId  ASC, # first order by group
                    isChild ASC, # Then make sure the parent is first
                    %(childOrder)s
            ) s1,
            ( SELECT @parentrownum := 0 ) pr,
            ( SELECT @childrownum := 0 ) cr, 
            ( SELECT @lastparent := -1 ) lp) f
            LEFT JOIN user u on u.id = f.userId
            LEFT JOIN %(table)s r on r.id = f.relatedId
            LEFT JOIN user ur on ur.id = r.userId
            WHERE
            ((0 = %(parentRangeTop)d and parent_sequence >= %(parentOffset)d) or parent_sequence BETWEEN %(parentOffset)d AND %(parentRangeTop)d)
            AND
            ((0 = %(childRangeTop)d and child_sequence >= %(childOffset)d) or (child_sequence=0 or child_sequence BETWEEN %(childOffset)d AND %(childRangeTop)d))
        """ % params_dict


        rows = self.query(sql)

        comments = []


        for row in rows:
            #for field in row:
            #    logging.debug("%s: %s" % (field, row[field]))
 
            # logging.debug("row -> \n %s" % (row))
            comment = CommentItem(**row)
            # logging.debug("comment -> \n %s" % (comment.to_json()))
            if comment.type==1:
                #logging.debug("table, comment.id: %s, %s" % (table, comment.id))
                comment.images = self.image_queryset.load_images_by_item_id(table, comment.id)

            comments.append(comment)
 
        logging.debug("Number of comments returned: %d" % len(comments))

        return comments


class CommentQueryset(MySqlApiQueryset):

    def __init__(self, settings, table_name, db_conn, **kw):
        """We may want to resuse a db_conn, not sure yet
           We need to pass the tablename since it may be different
           based on the API key
        """
        """call our MySql __init__.
           This will create a connection for us if we need it
        """
        super(CommentQueryset, self).__init__(settings, db_conn, **kw)
        self.table_name = table_name
        if self.table_name == None:
            self.table_name = self.settings["TABLES"]["COMMENT"]["TABLE_NAME"]
        self.fields = self.settings["TABLES"]["COMMENT"]["FIELDS"]
        self.fields_muteable = self.settings["TABLES"]["COMMENT"]["FIELDS_MUTEABLE"]


    def get_parent_id(self, location, id, table):
        """Get the id for the parent of the passed id"""

        args = [];
        if location != None:
            sql = """
                SELECT relatedId FROM `%s` WHERE id = %%s AND location = %%s
            """ % table
            args = [id, location]
        else:
            sql = """
                SELECT relatedId FROM `%s` WHERE id = %%s
            """ % table
            args = [id]

        row = self.fetch(sql, args)

        if row is None:
            logging.debug("No parent found")
            return 0
        else:
            logging.debug("Parent id %d" % row['relatedId'])
            return row['relatedId']


    def get_count_by_table_and_location(self, table, location, flagType=None):
        """Get the number of contributions for a page"""

        if flagType == None:
            flag_join_sql = ''
            flag_group_by_clause = ''
        else:
            flag_join_sql = "JOIN flag fl on fl.itemId=t.id and fl.flagTypeId=%s" % flagType
            flag_group_by_clause = " GROUP BY t.id"

        sql = """
            SELECT count(*) as recordCount FROM `%s` t 
            %s
            WHERE `t`.`location` = %%s                    
            %s
        """ % (table,flag_join_sql,flag_group_by_clause)

        row = self.fetch(sql, [location])

        if row is None:
            logging.debug("No contributions")
            return 0
        else:
            logging.debug("Number of contributions %s" % row['recordCount'])
            return row['recordCount']

    def get_contribution_count_by_table_and_location(self, table, location):
        """Get the number of contibutions for a page"""
        self.init_db_conn()

        params_dict = dict()

        sql = """
            SELECT count(*) as recordCount FROM `%s` WHERE `location` = ?
        """ % table

        row = self.fetch (sql)

        if row is None:
            logging.debug("No contributions")
            return 0
        else:
            logging.debug("Number of contributions %d" % row['recordCount'])
            return row['recordCount']

    def get_ids_by_parent_id(self, table, parent_id):
        """Get a list of the ids of the children of a parent"""
        self.init_db_conn()

        ids = []

        sql = """
            SELECT id FROM `%s` WHERE `parentId` = %%s
        """ % table

        rows = self.query (sql, [parent_id])

        if rows is None:
            logging.debug("No children ids for parent(%s)" % parent_id)
        else:
            for row in rows:
                ids.append(row['id'])

        logging.debug('returning %s child ids' % len(ids))
        return ids;

    def get_child_count_by_item_id(self, comment_table, id):
        """returns the number of children for an item"""
    
        sql = """
            SELECT count(*) as `childCount`
            FROM `%s` `f`
            WHERE `f`.`parentId`= %%s
            """ % comment_table

        row = self.fetch(sql, [id]);
        
        if row == None:
            return 0
        
        return row['childCount']

    def get_related_ids_by_item_id(self, table, item_id):
        """Get a list of the ids of the children of a parent"""
        self.init_db_conn()

        ids = []

        sql = """
            SELECT id FROM `%s` WHERE `relatedId` = %%s
        """ % table

        rows = self.query (sql, [item_id])

        if rows is None:
            logging.debug("No related ids for parent(%s)" % item_id)
        else:
            for row in rows:
                ids.append(row['id'])

        logging.debug('returning %s related ids' % len(ids))
        return ids;


class UserQueryset(MySqlApiQueryset):

    def __init__(self, settings, db_conn, **kw):
        """We may want to resuse a db_conn, not sure yet
           We need to pass the tablename since it may be different
           based on the API key
        """
        """call our MySql __init__.
           This will create a connection for us if we need it
        """
        super(UserQueryset, self).__init__(settings, db_conn, **kw)
        
        self.table_name = self.settings["TABLES"]["USER"]["TABLE_NAME"]
        self.fields = self.settings["TABLES"]["USER"]["FIELDS"]
        self.fields_muteable = self.settings["TABLES"]["USER"]["FIELDS_MUTEABLE"]

    def dictListToDictShieldList(self, dictList):
        """utility function to convert a list of dict items to a list of DictShield items
           think hard before you use this, you are probably wasting your time, and the computers CPU
           TODO: This really is common functionality, probably should be abstracted a bit
        """
        items = []
        for dictItem in dictList:
            items.append(Image(**dictList))

    ###
    ### Our special queries that have filters
    ###

    def get_by_qooid(self, qooid):
        """Loads a user by qooid"""

        sql = """
            SELECT %s FROM `%s` WHERE `oauth_session_id`=%%s
        """ % (self.get_fields_list(), self.table_name)

        row = self.query(sql, [qooid], self.FORMAT_DICT,True)

        if row is None:
            return None
        else:
            u = User(**row)
            return u

    def logout_by_qooid(self, qooid):
        """Removes the session key from a user a user by qooid"""
        if qooid == None:
            return 0

        sql = """
            UPDATE `%s` SET `oauth_session_id`= null WHERE `oauth_session_id`=%%s
        """ % (self.table_name)

        return self.execute (sql, [qooid])


class ImageQueryset(MySqlApiQueryset):
    """ This is a simple, completely standard one to one mapping to the DB
        Only dict are returned, if you want a DictShield item 
        that is the callers responsability to call dictListToDictShieldList
    """

    def __init__(self, settings, table_name, db_conn, **kw):
        """We may want to resuse a db_conn, not sure yet
           We need to pass the tablename since it may be different
           based on the API key
        """
        """call our MySql __init__.
           This will create a connection for us if we need it
        """
        super(ImageQueryset, self).__init__(settings, db_conn, **kw)
        self.table_name = table_name
        
        if self.table_name == None:
            self.table_name = settings["TABLES"]["IMAGE"]["TABLE_NAME"]
        self.fields = settings["TABLES"]["IMAGE"]["FIELDS"]
        self.fields_muteable = settings["TABLES"]["IMAGE"]["FIELDS_MUTEABLE"]

    def dictListToDictShieldList(self, dictList):
        """utility function to convert a list of dict items to a list of DictShield items
           think hard before you use this, you are probably wasting your time, and the computers CPU
           TODO: This really is common functionality, probably should be abstracted a bit
        """
        items = []

        for dictItem in dictList:
            items.append(Image(**dictItem))

        return items

    ###
    ### Our special queries that have filters
    ###

    def load_images_by_item_id(self, item_table, item_id):
        """Loads images for a comment"""
        if item_id == None:
            return None

        sql = """
            SELECT %s FROM `%s` WHERE `itemId` = %%s
        """ % (self.get_fields_list(), item_table + "_images")

        return self.dictListToDictShieldList(self.query(sql, [item_id]))

    def delete_by_item_id(self, item_table, item_id):
        """delete all flags for an item"""
    
        if isinstance( item_id, ( int, long ) ):
            sql = """
                DELETE
                FROM `%s`
                WHERE `itemId`= %%s
                """ % (item_table + "_images")
    
            items_affected = self.execute(sql, [item_id]);
            
            if items_affected == 0:
                logging.debug("No images deletes ('%s',%s)" % (item_table, item_id))
                return False
            else:
                logging.debug("%s images deletes ('%s',%s)" % (items_affected, item_table, item_id))
                return True
        else:
            raise Exception('Invalid item_id(%s), must be a number' % item_id)


class VoteQueryset(MySqlApiQueryset):
    """ This is a simple, completely standard one to one mapping to the DB
        Only dict are returned, if you want a DictShield item 
        that is the callers responsibility to call dictListToDictShieldList
    """

    def __init__(self, settings, db_conn, **kw):
        """We may want to resuse a db_conn, not sure yet
           We need to pass the tablename since it may be different
           based on the API key
        """
        """call our MySql __init__.
           This will create a connection for us if we need it
        """
        super(VoteQueryset, self).__init__(settings, db_conn, **kw)
        
        self.table_name = settings["TABLES"]["VOTE"]["TABLE_NAME"]
        self.fields = settings["TABLES"]["VOTE"]["FIELDS"]
        self.fields_muteable = settings["TABLES"]["VOTE"]["FIELDS_MUTEABLE"]

    def dictListToDictShieldList(self, dictList):
        """utility function to convert a list of dict items to a list of DictShield items
           think hard before you use this, you are probably wasting your time, and the computers CPU
           TODO: This really is common functionality, probably should be abstracted a bit
        """
        items = []

        for dictItem in dictList:
            items.append(Vote(**dictItem))

        return items

    ###
    ### Our special queries that have filters
    ###
    def get_by_item_id_and_user_id(self, ref_table, id, user_id):
        """get a users vote on an item"""
        if id == None:
            return None

        sql = """
            SELECT %s FROM `%s` WHERE `refTable` = %%s and `itemId` = %%s and `userId` = %%s
        """ % (self.get_fields_list(), self.table_name) 

        rows = self.query(sql, [ref_table, id, user_id])

        if rows == None:
            return None
            
        return self.dictListToDictShieldList(rows)

    def get_by_item_id_and_qootid(self, ref_table, id, qootid):
        """get a users vote on an item"""
        if id == None:
            return None

        sql = """
            SELECT %s FROM `%s` WHERE `refTable` = %%s and `itemId` = %%s and `qootid` = %%s
        """ % (self.get_fields_list(), self.table_name) 

        rows = self.query(sql, [ref_table, id, qootid])

        if rows == None:
            return None
            
        return self.dictListToDictShieldList(rows)

    def get_vote_counts_by_item_id(self, id, table, includeChildVotes):
        """get the vote count sum totals for an item"""
        if id == None:
            return None

        args = [table, table, id]
        # get the votes for an item
        sql = """
        SELECT ifnull(id,0) as id, 'parent' AS type, SUM(down) AS down, SUM(up) AS up  FROM (
            SELECT ifnull(q.id,0) as id,
                (SELECT SUM(down) FROM vote WHERE itemId = q.id AND refTable=%%s AND down > 0) AS down,
                (SELECT SUM(up) FROM vote WHERE itemId = q.id AND refTable=%%s AND up > 0) AS up
            FROM `%s` q
            WHERE q.id=%%s
            GROUP BY q.id) s1
        """ % table

        if includeChildVotes:
            # include totals from all the children
            sql = sql + """
            UNION
            SELECT ifnull(id,0) as id, 'children' AS type, SUM(down) AS down, SUM(up) AS up  FROM (
                SELECT ifnull(q.parentId,0) as id,
                    (SELECT SUM(down) FROM vote WHERE itemId = q.id AND refTable=%%s AND down > 0) AS down,
                    (SELECT SUM(up) FROM vote WHERE itemId = q.id AND refTable=%%s AND up > 0) AS up
                FROM `%s` q
                WHERE q.parentId > 0
                AND q.parentId=%%s
                GROUP BY q.parentId) s2
            """ % table
            args = args + [table, table, id];
        
        # sum up our results
        sql = " SELECT id, SUM(down) AS votesDown, SUM(up) AS votesUp FROM(" + sql + ") s3 WHERE NOT id IS NULL AND id  > 0 GROUP BY 1"

        return self.query(sql, args)

    def delete_by_item(self, item):
        """delete all votes for an item"""
    
        item_id = item.id
        vote_count = item.voteCount

        if vote_count > 0:
            sql = """
                DELETE
                FROM `%s`
                WHERE `itemId`= %%s limit %s
                """ % (self.table_name, vote_count)
    
            items_affected = self.execute(sql, [item_id]);
            
            if items_affected != vote_count:
                logging.debug("WARNING: Votes deleted (%s) not equal to voteCount(%s)" % (items_affected, vote_count))
                return False
            else:
                logging.debug("Votes deleted (%s) equals to voteCount(%s)" % (items_affected, vote_count))
                return True
        else:
            logging.debug("No votes deleted, voteCount(%s)" % (vote_count))
            return True

class FlagQueryset(MySqlApiQueryset):
    """ This is a simple, completely standard one to one mapping to the DB
        Only dict are returned, if you want a DictShield item 
        that is the callers responsibility to call dictListToDictShieldList
    """

    def __init__(self, settings, db_conn, **kw):
        """We may want to resuse a db_conn, not sure yet
           We need to pass the tablename since it may be different
           based on the API key
        """
        """call our MySql __init__.
           This will create a connection for us if we need it
        """
        super(FlagQueryset, self).__init__(settings, db_conn, **kw)
        
        self.table_name = settings["TABLES"]["FLAG"]["TABLE_NAME"]
        self.fields = settings["TABLES"]["FLAG"]["FIELDS"]
        self.fields_muteable = settings["TABLES"]["FLAG"]["FIELDS_MUTEABLE"]

    def dictListToDictShieldList(self, dictList):
        """utility function to convert a list of dict items to a list of DictShield items
           think hard before you use this, you are probably wasting your time, and the computers CPU
           TODO: This really is common functionality, probably should be abstracted a bit
        """
        items = []

        for dictItem in dictList:
            items.append(Flag(**dictItem))

        return items
    
    def get_flag_email_alert_info_by_id(self, id):
        """returns a row containing enough flag info to generate an email alert to the admin"""
        # first get our reftable
        sql = "SELECT refTable FROM `flag` WHERE id = %s"
        row = self.fetch(sql, [id]);
        if row == None:
            return None

        table_name = row['refTable']
    
        sql = """
            SELECT `f`.*, `i`.name, `i`.`referer`, `ui`.`username`, `ui`.`email`,
            `uq`.`username` as `adminUsername`, `uq`.`email` as `adminEmail`,
            `ft`.`name` as `flagType`
            FROM `flag` `f`
            LEFT JOIN `%s` `i` on `i`.`id`=`f`.`id`
            LEFT JOIN `qoorates` `q` on `q`.`refTable`=`f`.`refTable`
            LEFT JOIN `user` `uq` on `uq`.`id`=`q`.`userId`
            LEFT JOIN `user` `ui` on `ui`.`id`=`i`.`userId`
            LEFT JOIN `flag_type` `ft` on `ft`.`id`=`f`.`flagTypeId`
            WHERE `f`.`id`= %s
            """ % (table_name, id )

        return self.fetch(sql, [id]);

    def get_flag_by_refTableitemIduserId(self, ref_table, item_id, user_id):
        """returns a row containing enough flag info to generate an email alert to the admin"""
        # first get our reftable
        sql = "SELECT * FROM `flag` WHERE refTable = %s and itemId = %s and userId = %s"
        row = self.fetch(sql, [item_table, item_id, user_id]);
        if row == None:
            return None

        return row

    def get_flag_count_by_item_id(self, id, comment_table):
        """returns the number of times an item has been flagged"""
    
        sql = """
            SELECT count(*) as `flagCount`
            FROM `flag` `f`
            WHERE `f`.`refTable`= %s and `itemId`=%s
            """

        row = self.fetch(sql, [comment_table, id]);
        
        if row == None:
            return 0
        
        return row['flagCount']

    def delete_by_item(self, item):
        """delete all flags for an item"""
    
        item_id = item.id
        flag_count = item.flagCount

        if flag_count > 0:
            sql = """
                DELETE
                FROM `%s`
                WHERE `itemId`= %%s limit %s
                """ % (self.table_name, flag_count)
    
            items_affected = self.execute(sql, [item_id]);
            
            if items_affected != flag_count:
                logging.debug("WARNING: Flags deleted (%s) not equal to flagCount(%s)" % (items_affected, flag_count))
                return False
            else:
                logging.debug("Flags deleted (%s) equals to flagCount(%s)" % (items_affected, flag_count))
                return True
        else:
            logging.debug("No flags deleted, flagCount(%s)" % (flag_count))
            return True


class KeypairQueryset(MySqlApiQueryset):
    """ This is a simple, completely standard one to one mapping to the DB
        Only dict are returned, if you want a DictShield item 
        that is the callers responsability to call dictListToDictShieldList
    """

    def __init__(self, settings, db_conn, **kw):
        """We may want to resuse a db_conn, not sure yet
           We need to pass the tablename since it may be different
           based on the API key
        """
        """call our MySql __init__.
           This will create a connection for us if we need it
        """
        super(KeypairQueryset, self).__init__(settings, db_conn, **kw)
        self.table_name = settings["TABLES"]["KEYPAIR"]["TABLE_NAME"]
        self.fields = settings["TABLES"]["KEYPAIR"]["FIELDS"]
        self.fields_muteable = settings["TABLES"]["KEYPAIR"]["FIELDS_MUTEABLE"]

    def dictListToDictShieldList(self, dictList):
        """utility function to convert a list of dict items to a list of DictShield items
           think hard before you use this, you are probably wasting your time, and the computers CPU
           TODO: This really is common functionality, probably should be abstracted a bit
        """
        items = []
        for dictItem in dictList:
            items.append(KeyPair(**dictItem))
        return items

    ###
    ### Our special queries that have filters
    ###

    def authenticate(self, key, secret):
        """authenticate an API key"""
        if hasattr(self, '_authenticate'):
            logging.debug("returning `%s` from authenticate cached." % self._authenticate)
            return getattr(self, '_authenticate')

        sql = """
            SELECT %s FROM `%s` WHERE `key` = %%s and `secret`= %%s
        """ % (self.get_fields_list(), self.table_name)
        row = self.query(sql, [key, secret])
        if row == None:
            self._authenticate = False
        else:
            self._authenticate = True
        logging.debug("returning %s from authencticate." % self._authenticate)
        return self._authenticate


class QoorateQueryset(MySqlApiQueryset):
    """ This is a simple, completely standard one to one mapping to the DB
        Only dict are returned, if you want a DictShield item 
        that is the callers responsability to call dictListToDictShieldList
    """

    def __init__(self, settings, db_conn, **kw):
        """We may want to resuse a db_conn, not sure yet
           We need to pass the tablename since it may be different
           based on the API key
        """
        """call our MySql __init__.
           This will create a connection for us if we need it
        """
        super(QoorateQueryset, self).__init__(settings, db_conn, **kw)
        
        self.table_name = settings["TABLES"]["QOORATE"]["TABLE_NAME"]
        self.fields = settings["TABLES"]["QOORATE"]["FIELDS"]
        self.fields_muteable = settings["TABLES"]["QOORATE"]["FIELDS_MUTEABLE"]

    def dictListToDictShieldList(self, dictList):
        """utility function to convert a list of dict items to a list of DictShield items
           think hard before you use this, you are probably wasting your time, and the computers CPU
           TODO: This really is common functionality, probably should be abstracted a bit
        """
        items = []

        for dictItem in dictList:
            items.append(Qoorate(**dictItem))

        return items

    ###
    ### Our special queries that have filters
    ###

    def get_by_short_title(self, short_title):
        """Loads qoorate by short name"""

        sql = """
            SELECT %s FROM `%s` WHERE `shortTitle` = %%s
        """ % (self.get_fields_list(), self.table_name)

        row = self.dictListToDictShieldList(self.query(sql, [short_title]))
        
        if row == None or row == []:
            return None;
        else:
            return row[0];

    def get_by_ref_table(self, ref_table):
        """Loads qoorate by refTable"""

        sql = """
            SELECT %s FROM `%s` WHERE `refTable` = %%s
        """ % (self.get_fields_list(), self.table_name)

        row = self.dictListToDictShieldList(self.query(sql, [ref_table]))
        
        if row == None or row == []:
            return None;
        else:
            return row[0];
        