#!/usr/bin/env python
from brubeck.auth import authenticated
from brubeck.request_handling import JSONMessageHandler
from brubeck.templating import load_jinja2_env, Jinja2Rendering
import sys
import urllib2
from urlparse import urlparse
import functools
import logging
import os
import time
import random
import json
import datetime
import magic
import re
import md5

from BeautifulSoup import BeautifulSoup



from models.models import CommentItem, User, Comment, Image, Vote, Flag
from querysets.querysets import CommentItemQueryset, UserQueryset, CommentQueryset, ImageQueryset, VoteQueryset, FlagQueryset
from handlers.base import QoorateBaseHandler
from modules.brooklyncodebrubeck.application import lazyprop
from modules.uploader.base import Uploader

##
## Our feed handler class definitions
##
class FeedHandler(Jinja2Rendering, QoorateBaseHandler,JSONMessageHandler):
    """Handles poll requests from user; sends out queued messages.
       This handler feels like it does a little too much,
       but it is a port of the original PHP code.
       In an ideal world the calls would be a bit more RESTfull.
    """

    ##
    ## Lazy parameters, needed by most function, but not all
    ##
    ## IMPORTANT: These are only properties a user can set.
    
    @lazyprop
    def replyComment(self):
        """ xxx argument
        """
        return self.get_argument('replyComment', None)

    @lazyprop
    def replyTopic(self):
        """ xxx argument
        """
        return self.get_argument('replyTopic', None)

    @lazyprop
    def replyLink(self):
        """ xxx argument
        """
        return self.get_argument('replyLink', None)

    @lazyprop
    def replyPhoto(self):
        """ xxx argument
        """
        return self.get_argument('replyPhoto', None)

    @lazyprop
    def description(self):
        """ xxx argument
        """
        return self.get_argument('description', None)

    @lazyprop
    def post(self):
        """ xxx argument
        """
        return self.get_argument('post', None)

    @lazyprop
    def locationId(self):
        """ xxx argument
        """
        return self.get_argument('locationId', 0)

    @lazyprop
    def relatedId(self):
        """ xxx argument
        """
        return self.get_argument('relatedId',  0)

    @lazyprop
    def parentId(self):
        """ xxx argument
        """
        return self.get_argument('parentId',  0)

    @lazyprop
    def description(self):
        """ xxx argument
        """
        return self.get_argument('description', None)

    @lazyprop
    def name(self):
        """ xxx argument
        """
        return self.get_argument('replyComment', None)

    @lazyprop
    def thumbnailLarge(self):
        """ xxx argument
        """
        return self.get_argument('thumbnailLarge', None)

    @lazyprop
    def qoorateId(self):
        """ xxx argument
        """
        return self.get_argument('qoorateId', None)

    @lazyprop
    def itemId(self):
        """ xxx argument
        """
        return self.get_argument('itemId', None)

    @lazyprop
    def comment(self):
        """ xxx argument
        """
        return self.get_argument('comment', None)    

    @lazyprop
    def flagTypeId(self):
        """ xxx argument
        """
        return self.get_argument('flagTypeId', None)    

    @lazyprop
    def uploader(self):
        """ image mainipulation and s3 upload
        """
        return Uploader(self.application.get_settings('uploader'))    

    # Voting constants
    UP = 1
    DOWN = -1
    def __init__(self, application, message, *args, **kwargs):
        super(FeedHandler, self).__init__(application, message, *args, **kwargs)
        logging.debug('FeedHandler __init__')
        ## Hook up our Queryset objects here

        image_table = None
        if self.table != None:
            image_table = self.table + '_images'
            
        self.comment_queryset = CommentQueryset(self.application.get_settings('mysql'), self.table, db_conn = self.application.db_conn)
        self.image_queryset = ImageQueryset(self.application.get_settings('mysql'), image_table, db_conn = self.application.db_conn)
        self.vote_queryset = VoteQueryset(self.application.get_settings('mysql'), db_conn = self.application.db_conn)
        self.flag_queryset = FlagQueryset(self.application.get_settings('mysql'), db_conn = self.application.db_conn)

    def prepare(self):
        # TODO: Actually get these from the DB
        """prepare what we need for each request"""
        self.comment_item_queryset = CommentItemQueryset(self.application.get_settings('mysql'), self.table, db_conn = self.application.db_conn)

    def get(self):
        self.set_status(200)
        self.add_to_payload('error', "Not implemented")
        return self.render()

    def post(self):
        """rout to our proper performXXXXXX method
        Don't worry about authentication here, the performXXXX has that responsibility
        """

        logging.debug("FeedHandler post")
        logging.debug("Body -> \n %s" % (self.message.body))
        logging.debug("Arguments -> \n %s" % (json.dumps(self.message.arguments)))
        logging.debug(self.get_argument('action'))

        try:
            if self.action == 'logoffUser':
                self.performLogoffUser()

            elif self.action == 'addUser':
                self.performAddUser()

            elif self.action == 'editUser':
                self.performEditUser()

            elif self.action == 'deleteUser':
                self.performDeleteUser()

            elif self.action == 'addRelated':
                self.performAddRelated()

            elif self.action == 'editRelated':
                self.performEditRelated()

            elif self.action == 'deleteRelated':
                self.performDeleteRelated()

            elif self.action == 'deleteComment':
                self.performDeleteComment()

            elif self.action == 'addItem':
                self.performAddItem()

            elif self.action == 'editItem':
                self.performEditItem()

            elif self.action == 'deleteItem':
                self.performDeleteItem()

            elif self.action == 'addTag':
                self.performAddTag()

            elif self.action == 'editTag':
                self.performEditTag()

            elif self.action == 'deleteTag':
                self.performDeleteTag()

            elif self.action == 'upVote':
                self.performVote(self.UP)

            elif self.action == 'downVote':
                self.performVote(self.DOWN)

            elif self.action == 'addQoorate':
                self.performAddQoorate()

            elif self.action == 'editQoorate':
                self.performEditQoorate()

            elif self.action == 'deleteQoorate':
                self.performDeleteQoorate()

            elif self.action == 'attachLink':
                self.performAttachLink()

            elif self.action == 'attachVideo':
                self.performAttachVideo()

            elif self.action == 'attachPhoto':
                self.performAttachPhoto()

            elif self.action == 'authentication':
                self.performAuthentication()

            elif self.action == 'flag':
                self.performFlag()

            elif self.action == 'createTopic':
                self.performTopic()

            elif self.action == 'getMoreChildren':
                self.performMoreChildren()

            elif self.action == 'getMore':
                self.performGetMore()

            elif self.action == 'shareItem':
                self.performShareItem()

            elif self.action == 'sort':
                self.performSort()
                self.getContributionCount()

            elif self.action == 'validateLogin':
                self.performValidateLogin()

            else:
                raise Exception("Unsupported action: %s" % self.action)

        except Exception as e:
            raise
            self.set_status(500)
            self.add_to_payload('error', 1)
            self.add_to_payload('message', e.message)
            self.add_to_payload('action', self.action)
            return self.render()

        # Success
        # The client expects error = 0 to mean success
        self.add_to_payload('contributions', self.getContributionCount())
        self.add_to_payload('table', self.table)
        self.add_to_payload('location', self.location)
        self.add_to_payload('error', 0)
        self.set_status(200)
        return self.render()

    def getContributionCount(self):
        """adds our contribtion count to the payload"""
        if self.table == None or self.location == None:
            return 0
        else:
            return self.comment_queryset.get_count_by_table_and_location(self.table, self.location)

    ##
    ## All off our action methods
    ## Not all of these are implemented, or even needed
    ## However, they are left here for legacy documentation
    ## since this is a rewrite of a PHP prototype
    ##
    def performLogoffUser(self):
        """removes the session cookie from our user"""

        if self.current_user != None:
            self.user_queryset.logout_by_qooid(self.qooid)

        return

    def performAddUser(self):
        """xxx"""
        raise Exception("performAddUser not implemented.")
        return

    @authenticated
    def performEditUser(self):
        """xxx"""
        raise Exception("performEditUser not implemented.")
        return

    @authenticated
    def performDeleteUser(self):
        """xxx"""
        raise Exception("performDeleteUser not implemented.")
        return

    @authenticated
    def performAddRelated(self):
        """xxx"""
        raise Exception("performAddRelated not implemented.")
        return

    @authenticated
    def performEditRelated(self):
        """xxx"""
        raise Exception("performEditRelated not implemented.")
        return

    @authenticated
    def performDeleteRelated(self):
        """xxx"""
        raise Exception("performDeleteRelated not implemented.")
        return

    @authenticated
    def performDeleteComment(self):
        """xxx"""
        raise Exception("performDeleteComment not implemented.")
        return

    @authenticated
    def performAddItem(self):
        """add a new item (comment, topic, photo or link)"""
        
        if self.table == None:
            raise Exception("Table must be set!")

        name = (self.replyTopic if self.replyTopic != None else
            self.replyPhoto if self.replyPhoto != None else
            self.replyComment if self.replyLink != None else
            self.replyComment if self.replyComment != None else None)

        type = (10 if self.replyTopic != None else
            2 if self.replyLink != None else
            1 if self.replyPhoto != None else
            0 if self.replyComment != None else None)

        parentId = 0
        parent = None
        related_comment = None
        related_user = None
        if self.relatedId > 0:
            related_comment = self.comment_queryset.read_one(self.relatedId, table_name=self.table)[1]
            parentId = related_comment['parentId'] if related_comment['parentId'] !=0 else related_comment['id']
            related_user = User(**self.user_queryset.read_one(related_comment['userId'])[1])

        # if we have a thumbnail, save to S3 and replace value withe new URL
        #if thumbnailLarge != None:

        comment_image = None
        if self.replyLink != None:
            self._thumbnailLarge = self.uploader.download_image_from_url(self.thumbnailLarge)
            self._description = self.replyLink

        if self.thumbnailLarge != None and self.thumbnailLarge != '':
            # we are a photo, or a replyLink

            # save to S3

            # we may need to set this now because we are using replyComment to post
            # should be replyLink (or just send the type)
            if type != 2:
                type = 1
                
            if (self.uploader.upload_to_S3(self.thumbnailLarge)):
                image_data = {
                    'id': None,
                    'itemId': None,
                    's3Bucket': self.settings['AMAZON_BUCKET'],
                    'thumbnailLargeHash': self.thumbnailLarge,
                }
                
                comment_image = Image(**image_data)
                # don't save us yet, we still need our comment id                

            else:
                raise Exception('Unable to upload photo.')

        now = datetime.datetime.now()
        data = {
            'locationId':       self.locationId,
            'relatedId':        self.relatedId,
            'parentId':         parentId, 
            'name':             name,
            'location':         self.location,
            'userId':           self.current_user.id,
            'type':             type,
            'voteCount':        0,
            'voteNumber':       0,
            'votesUp':          0,
            'votesDown':        0,
            'flagCount':        0,
            'sortOrder':        0,
            'status':           '',
            'description':      self.description,
            'thumbnailLarge':   self.thumbnailLarge,
            'referer':          self.referer,
            'changeDate':       now,
            'createDate':       now
        }

        item = Comment(**data)
        logging.debug(item.to_json())
        result = self.comment_queryset.create_one(item, table_name=self.table)
        if self.comment_queryset.MSG_CREATED == result[0]:
            item = result[1]
            if comment_image != None:
                comment_image.itemId = item.id
                comment_image = self.image_queryset.create_one(comment_image, table_name = self.table + '_images')
                
            logging.debug(item.to_json)

            parent_tag = 'p' + self.table[1:]
            context = {
                'app': self.application.get_settings('app'),
                'location': self.location,
                'parent_tag': parent_tag,
                'table': self.table,
                'comments': [item],
                'current_user': self.current_user,
                'related_user': related_user,
                'comment_images': [comment_image],
                'thumbnailLargeHash': self.thumbnailLarge,
                'parentCount': self.parentCount,
                'childCount': self.childCount,
                'moreIndex': self.moreIndex,
            }
            
            # currentlly JS wants all comments for a prent when a reply is made
            # so, we will do the same for now. seems harsh.
            if item.parentId > 0:
                comments = self.comment_item_queryset.load_comments_by_table_and_location(self.table, 
                    self.location, 
                    parentId = item.parentId)

                # we also want the new item to always be after related item
                item_index = -1
                related_item_index = -1
                if len(comments) > 2:
                    for x in range(0, len(comments)):
                        comment = comments[x]
                        if comment.id == item.id:
                            item_index = x
    
                        if comment.id == item.relatedId:
                            related_item_index = x
                        if item_index>0 and related_item_index > 0:
                            break;
    
                    item = comments[item_index]
                    del comments[item_index]
                    if related_item_index == 0:
                        comments = comments[0] + [item] + comments[2:]
                    elif related_item_index + 1 == len(comments):
                        comments = comments[0:related_item_index + 1] + [item]
                    else:
                        comments = comments[0:related_item_index + 1] + [item] + comments[related_item_index + 2:]

                context['comments'] = comments
                    
            html = self.render_partial('comments.html', **context)
            logging.debug(html)
            self.add_to_payload('item', item)
            self.add_to_payload('content', html)
            return
            
        raise Exception('Unknown error occured, unable to add item.')

    @authenticated
    def performEditItem(self):
        """xxx"""
        raise Exception("performEditItem not implemented.")
        return

    @authenticated
    def performDeleteItem(self):
        """xxx"""
        raise Exception("performDeleteItem not implemented.")
        return

    @authenticated
    def performAddTag(self):
        """xxx"""
        raise Exception("performAddTag not implemented.")
        return

    @authenticated
    def performEditTag(self):
        """xxx"""
        raise Exception("performEditTag not implemented.")
        return

    @authenticated
    def performDeleteTag(self):
        """xxx"""
        raise Exception("performDeleteTag not implemented.")
        return

    ##
    ## This is the code we are converting, let us see how much cleaner it becomes
    ##
    """
    // SM: 20111220 - new way, new function, all with SQL
    public static function performVote($user, $direction) {
        Qoorate::debug("performVote($direction)");
        // SM: 20120109 - No longer need to be logged in to vote
        // If not logged in we will enforce singular login by QOOID
        //if ( ! isset( $user ) ) {
        //    throw new Exception("You must be logged in to vote.");
        //}

        list($itemId, $refTable) = Qoorate::_vote($user, $direction);

        $parent_votes = null;
        $votes = null;
        $isTop = Qoorate::isParent($itemId, $refTable);
        $isTopic = Qoorate::isTopic($itemId, $refTable);
        Qoorate::debug("isTop=$isTop");

        $votes = Qoorate::updateVoteCounts($itemId, $refTable, $isTop, $isTopic);

        if( ! $isTop ) {
            // We need to recalculate our parent votes and return the results too
            $parentId = Qoorate::getParentId($itemId, $refTable);
            // SM: 20120123 - we need to know if the parent is a topic too
            $isTopic = Qoorate::isTopic($parentId, $refTable);
            $parent_votes = Qoorate::updateVoteCounts( $parentId, $refTable, true, $isTopic );
            // add our parent votes to the return object 
            $votes['parent_votes'] = $parent_votes;
        }

        return $votes;

    }

    // SM: 20111220 - Updates the vote count for the item
    public static function updateVoteCounts($itemId, $refTable, $includeChildVotes, $isTopic){
        if ( $isTopic ) {
            $includeChildVotes = false;
        }
        
        $votes = Qoorate::getVoteCounts($itemId, $refTable, $includeChildVotes);

        $votesUp = $votes['votesUp'];
        $votesDown = $votes['votesDown'];
        if( !isset($votesUp) ) {
            $votesUp = 0;
        }
        if( ! isset($votesDown) ) {
            $votesDown = 0;
        }
        $voteCount = $votesUp + $votesDown;
        $voteNumber = $votesUp - $votesDown;

        if($isTopic) {
            $voteNumber = $voteCount;
        }

        $row = array( 'voteCount'=> $voteCount, 'voteNumber'=>$voteNumber, 'votesUp'=>$votesUp, 'votesDown'=>$votesDown);
        $updated = Qoorate::editRow($refTable, "id", $itemId, $row);

        return array_merge( array( 'id'=>$itemId, 'table'=>$refTable ), $row );
    }

    // SM: 20111220 - Gets the vote count for an item
    public static function getVoteCounts($itemId, $refTable, $includeChildVotes = false){
        $params = null;
        // get the votes for an item
        $sql = "select id, 'parent' as type, sum(down) as down, sum(up) as up  from ( \n" .
                       "select q.id, \n" . 
                       "(select sum(down) from vote where itemId = q.id and refTable=? and down > 0) as down, \n" . 
                       "(select sum(up) from vote where itemId = q.id and refTable=? and up > 0) as up \n" . 
                       "from $refTable q \n" .
                       "where q.id=? \n" .
                       "group by q.id) s1 \n";

        if ( $includeChildVotes ) {
            // include totals from all the children
            $sql .= "union \n" .
                   "select id, 'children' as type, sum(down) as down, sum(up) as up  from ( \n" .
                       "select q.parentId as id," . 
                       "(select sum(down) from vote where itemId = q.id and refTable=? and down > 0) as down," . 
                       "(select sum(up) from vote where itemId = q.id and refTable=? and up > 0) as up \n" . 
                       "from $refTable q \n" .
                       "where q.parentId > 0 \n" .
                       "and q.parentId=? \n" .
                       "group by q.parentId) s2 \n";
            // include param valuse for the item and children query
            $params = array( $refTable, $refTable, $itemId,  $refTable, $refTable, $itemId );
        } else {
            // Just include param values for the item
            $params = array( $refTable, $refTable, $itemId );        
        }

        // sum up our results
        $sql = "select id, sum(down) as votesDown, sum(up) as votesUp from( \n" .
               $sql . "\n" .
               ") s3 where not id is null and id  > 0 group by 1\n";


        return Qoorate::getQueryRow($sql, $params);
    }

    public static function _vote($user, $direction) {
        // params
        $itemId         = (isset($_REQUEST['itemId']))          ? $_REQUEST['itemId']                   : NULL;
        $refTable       = (isset($_REQUEST['refTable']))        ? $_REQUEST['refTable']                 : NULL;
        $comment        = (isset($_REQUEST['comment']))         ? sanitizeString($_REQUEST['comment'])  : NULL;
        $thumbnailLarge = (isset($_REQUEST['thumbnailLarge']))  ? $_REQUEST['thumbnailLarge']           : NULL;

        $userId = 0;
        if ( isset( $user ) ) {
            $userId = $user['id'];
        }
        $qootid = 0;

        $qootid = $_COOKIE['QOOTID'];

        $page     = (isset($_REQUEST['page']))         ? $_REQUEST['page'] : NULL;
        //itemID comes from relatedID in the case of embedded qoorates.
        if(!$itemId) {
            $itemId = $_REQUEST['relatedId'];
            $refTable = $_REQUEST['table'];
        }

        $createDate = Qoorate::getDatetime();

        // add to the database
        $row = array('itemId' => $itemId,
                     'refTable' => $refTable,
                     'userId' => $userId,
                     'qootid' => $qootid,
                     '`comment_-`' => $comment,
                     'thumbnailLarge' => $thumbnailLarge,
                     'up' => 0,
                     'down' => 0,
                     'createDate' => $createDate);


        if($direction == 'up'){
            $row['up'] = 1;
            $row['down'] = 0;
        } elseif($direction == 'down') {
            $row['up'] = 0;
            $row['down'] = 1;
        }

        //echo var_dump($row);
        //mgb  12/11 check to see if a vote for this item and by this user already exists, update it otherwise create a new entry
        if($userId > 0 ) {
            $isCheat = Qoorate::getQueryRow("select userId from $refTable where id = ?", array($itemId));
            if( $isCheat['userId'] == $userId){
                throw new Exception('You cannot vote on your own contribution');
            }
        }

        if( $userId == 0 && !isset($qootid) )  {
            Qoorate::debug("Error voting: cookies not enabled.");
            throw new Exception("Please enable cookies to vote.");
        }


        // SM: 20120109 - We need to check for a record 
        $exists = 0;

        if( $userId > 0 ) {
            $exists_row = Qoorate::getQueryRow("select count(*) as votes from vote where refTable = ? and itemId = ? and userId = ?", array($refTable, $itemId, $userId));
        } else {
            $exists_row = Qoorate::getQueryRow("select count(*) as votes from vote where refTable = ? and itemId = ? and qootid= ?", array($refTable, $itemId, $qootid));            
        }

        if( isset( $exists_row ) && $exists_row['votes'] > 0 ) {
            $exists = $exists_row['votes'];
        }
        
        // SM: 20111220 - Uncommented, was allowing multiple votes on an item
        // SM: 10120109 - Updated no longer used to see if a record exists. 
        // If the vote would not be changed it would assume it didn't exist, creating a duplicate
        if( $exists > 0 && $userId > 0 ) {
            $updated = Qoorate::editRow('vote', "refTable", "$refTable", $row, "itemId", $itemId, "userId", $userId);
        } else if( $exists > 0 && isset($qootid) ){
            $updated = Qoorate::editRow('vote', "refTable", "$refTable", $row, "itemId", $itemId, "qootid", $qootid); 
        }else { 
            // SM: 20111227 - Was still creating multiple votes sometimes
            // added unique constraint to DB and catch and ignore here
            // ALTER TABLE vote ADD UNIQUE (refTable, itemId, userId);
            // SM: 20120109 - Added qootid, a really long cookie to enable non logged in users to vote
            // removed unique constraint, we need to trust editRow now
            try {
                $voteId = Qoorate::addRow("vote", $row); //this takes care of adding the entry to vote table 
            } catch ( Exception $e ){
                Qoorate::debug("Error voting: " . $e->getMessage());
            }
        }

        return array($itemId,$refTable);
    }
    """
    ##
    ## End old php code
    ##    

    ##
    ## Voting methods
    ##

    def performVote(self, direction):
        """perform a requested vote"""
        logging.debug("performVote(%s)" % direction)

        parent_votes = None
        votes = None
        if self.itemId == None:
            self._itemId = self.relatedId

        item = None
        result = self.comment_queryset.read_one(self.itemId, table_name=self.table)[1]
        #logging.debug(result)
        if result != None:
            item = Comment(**result)

            vote = self._vote(direction, item)
    
            item = self.update_vote_counts(item)
    
            if item.parentId != 0:
                # We need to recalculate our parent votes and return the results too
                parentItem = None
                result = self.comment_queryset.read_one(item.parentId, table_name=self.table)[1]
                if result != None:
                    parentItem = Comment(**result)
                    parentItem = self.update_vote_counts( parentItem );
                    # add our parent votes to the payload
                    self.add_to_payload('parent_votes', ("{" +
                        "'voteCount': %s," +
                        "'voteNumber': %s," +
                        "'votesUp': %s," +
                        "'votesDown': %s" +
                        "}") % (parentItem.voteCount, parentItem.voteNumber, parentItem.votesUp, parentItem.votesDown) )

            logging.debug("performVote adding to payload")

            self.add_to_payload('voteCount', str(item.voteCount))
            logging.debug("voteCount: %s " % item.voteCount)

            self.add_to_payload('voteNumber', str(item.voteNumber))
            logging.debug("voteNumber: %s " % item.voteNumber)

            self.add_to_payload('votesUp', str(item.votesUp))
            logging.debug("votesUp: %s " % item.votesUp)

            self.add_to_payload('votesDown', str(item.votesDown))
            logging.debug("votesDown: %s " % item.votesDown)

        return

    def update_vote_counts(self, item):
        """Updates the vote count for the item"""
        logging.debug("update_vote_counts(%s)" % item)
        isTopic = False
        includeChildVotes = True
        
        if item.type == 10:
            isTopic = True
            includeChildVotes = False

        logging.debug(item.to_json())

        votes = self.vote_queryset.get_vote_counts_by_item_id(item.id, self.table, includeChildVotes)
        logging.debug(votes)
        votesUp = votes[0]['votesUp']
        votesDown = votes[0]['votesDown']

        if votesUp== None:
            votesUp = 0;
            
        if votesDown== None:
            votesDown = 0;

        voteCount = votesUp + votesDown
        voteNumber = votesUp - votesDown

        if isTopic:
            voteNumber = voteCount

        # update our item with new vote totals
        item.voteCount = voteCount
        item.voteNumber = voteNumber
        item.votesUp = votesUp
        item.votesDown = votesDown
        
        result = self.comment_queryset.create_one(item, table_name=self.table)[1]
        if result == None:
            return item
        
        return result


    def _vote(self, direction, item):
        """records a vote on an item"""
        logging.debug("_vote(%s, %s)" % (direction, item))

        user_id = self.current_user.id if self.current_user != None else 0

        logging.debug("user_id, item.userId: %s, %s" % (user_id, item.userId))

        if  user_id == item.userId:
            raise Exception('You cannot vote on your own contribution')

        if user_id == 0 and self.qootid == None:
            logging.debug("Error voting: cookies not enabled.")
            raise Exception("Please enable cookies to vote.")

        up = 0
        down = 0
        
        if direction == self.UP:
            up = 1
        elif direction == self.DOWN:
            down = 1


        # check for a record 
        vote = None
        if user_id > 0:
            vote = self.vote_queryset.get_by_item_id_and_user_id(self.table, item.id, user_id)
        else:
            vote = self.vote_queryset.get_by_item_id_and_qootid(self.table, item.id, qootid)

        if vote != None and len(vote) > 0:
            vote = vote[0]
            vote.up = up
            vote.down = down
        else:
            now = datetime.datetime.now()

            data = {
                'id': None,
                'itemId': item.id,
                'refTable': self.table,
                'userId': user_id,
                'qootid': self.qootid,
                'comment': self.comment,
                'thumbnailLarge': self.thumbnailLarge,
                'up': up,
                'down': down,
                'createDate': now
                }
        
            vote = Vote(**data)

        result = self.vote_queryset.create_one(vote)
        if result == None:
            return vote
        
        return result

    ##
    ## Flag methods
    ##

    @authenticated
    def performFlag(self):
        """perform a flag"""
        logging.debug("performFlag")

        if self.itemId == None:
            self._itemId = self.relatedId

        item = None
        result = self.comment_queryset.read_one(self.itemId, table_name=self.table)[1]
        if result != None:
            item = Comment(**result)

            flag = self._flag(item)
    
            item = self.update_flag_count(item)
    
            self.send_flag_alert(item, flag)

            logging.debug("performFlag adding to payload")

            self.add_to_payload('flagCount', str(item.flagCount))
            logging.debug("flagCount: %s " % item.flagCount)
            
            success_message = ""
            self.add_to_payload('message', success_message)
            logging.debug("message: %s " % success_message)

        return

    def update_flag_count(self, item):
        """Updates the vote count for the item"""
        logging.debug("update_flag_count(%s)" % item)

        logging.debug(item.to_json())

        flags = self.flag_queryset.get_flag_counts_by_item_id(item.id, self.table)
        logging.debug(flags)


        # update our item with new vote totals
        item.flagCount = flags

        result = self.comment_queryset.create_one(item, table_name=self.table)

        if result == None:
            return item
        
        return result[1]


    def _flag(self, item):
        """records a flag on an item"""
        logging.debug("_flag(%s)" % (item))



        #if  self.current_user.id == item.userId:
        #    raise Exception('You cannot flag your own contribution')

        # check for a record 
        flag = self.vote_queryset.get_by_item_id_and_user_id(self.table, item.id, self.current_user.id)

        if flag != None and len(flag) > 0:
            flag = flag[0]
            flag.flagTypeId = self.flagTypeId
        else:
            now = datetime.datetime.now()

            data = {
                'id': None,
                'itemId': item.id,
                'refTable': self.table,
                'userId': self.current_user.id,
                'comment': self.comment,
                'flagTypeId': self.flagTypeId,
                'createDate': now
                }
        
            flag = Flag(**data)

        result = self.flag_queryset.create_one(flag)
        if result == None:
            return flag
        
        return result[1]

    def send_flag_alert(self, item, flag):
        """send an email alert about a flag action"""
        logging.debug("sendFlagAlert %s" % (item));
        
        flag_info = self.flag_queryset.get_flag_email_alert_info_by_id(flag.id)
        
        # send our email
        subject            = "QOORATE FLAG: " + flag_info['flagType']
        to_address         = flag_info['adminEmail']
        cc_address         = self.settings.app["ADMIN_EMAIL_ADDRESS"]
        username           = flag_info['username']
        adminUsername      = flag_info['adminUsername']
        flagType           = flag_info['flagType']
        itemName           = flag_info['name']
        from_address       = self.settings.app["FROM_EMAIL_ADDRESS"]
        from_name          = self.settings.app["FROM_NAME"]        
        flaggerUsername    = self.current_user.username;
        
        self._referer = self.referer.split("#")[0];
        
        item_url = "%s#%s-%s" % (self.referer, self.table, item.id);

        message = "Hello " + adminUsername + ",\r\n\r\n" + \
            "An item from " + username + " has been flagged as '" + flagType + "' by " + flaggerUsername + ".\r\n\r\n" +  \
            "The comment was:\r\n\r\n" +  \
            itemName + " \r\n\r\n" +  \
            "You can view the item here:\r\n\r\n" + \
            item_url + " \r\n\r\n" + \
            "Thanks,\r\n\r\n" + from_name
                      
        
        if to_address != cc_address and "CC_ADMIN_FLAG_EMAILS" in self.settings and self.settings["CC_ADMIN_FLAG_EMAILS"]:
            cc_address = "\r\nCC: " + cc_address 
        else:
            cc_address = ''

        
        headers = "From: " + from_address + cc_address
        # OLD PHP CODE
        #mail ( to_address , subject , message, headers )

        return



    def performAddQoorate(self):
        """xxx"""
        raise Exception("performAddQoorate not implemented.")
        return

    @authenticated
    def performEditQoorate(self):
        """xxx"""
        raise Exception("performEditQoorate not implemented.")
        return

    @authenticated
    def performDeleteQoorate(self):
        """xxx"""
        raise Exception("performDeleteQoorate not implemented.")
        return

    @authenticated
    def performAttachLink(self):
        """get a list of image urls from a page"""
        replyLink = self.get_argument('replyLink', None)
        title = None
        description = None
        images = []
        if replyLink != None:
            response = urllib2.urlopen(replyLink)

            the_page = response.read()
            pool = BeautifulSoup(the_page)
            title = self.getLinkTitle(pool)
            description = self.getLinkDescription(pool)
            images = self.getLinkImages(pool, replyLink)

        self.add_to_payload('title', title)
        self.add_to_payload('description', description)
        self.add_to_payload('images', images)

        return

    def getLinkTitle(self, pool):
        """get title tag from a BeatifulSoup 'pool'"""
        title = ''

        tag = pool.find('meta', attr={'property': re.compile("^og:title$", re.I)});
        if tag != None:
            title = self._get_tag_attr(tag, 'content')
        else:
            tag = pool.find('title');
            if tag != None:
                title =  tag.contents
            else:
                tag = pool.find('meta', attr={'name': re.compile("^title$", re.I)});
                if tag != None:
                    title = self._get_tag_attr(tag, 'content')
        if len(title) > 0:
            title = title[0]
        return title;

    def _get_tag_attr(self, pool, attr):
        """used to get an atrribute from beatiful soup, and give us nothing if doesn't exist"""
        try:
            return pool[attr]
        except:
            pass
        return None        

    def getLinkDescription(self, pool):
        """get title tag from a BeatifulSoup 'pool'"""
        description = ''

        tag = pool.find('meta', attr={'property': re.compile('(?i)og:description')});
        if tag != None and len(tag) > 0:
            description = self._get_tag_attr(tag, 'content')
        else:
            tag = pool.find('meta', {'name': re.compile('(?i)description')})
            if tag != None:
                description = self._get_tag_attr(tag, 'content')

        return description;

    def getLinkImages(self, pool, pageUrl):
        """get image choices to attach to a link from a BeatifulSoup 'pool'"""
        urls = []

        tags = pool.findAll('meta', attr={'property': re.compile('(?i)og:image')});
        if tags != None and len(tags) > 0:
            for tag in tags:
                try:
                    url = self.fixUrl(self._get_tag_attr(tag, 'content'), pageUrl)
                    if url != None:
                        urls.append(url)
                except:
                    pass
        else:
            tags = pool.findAll('link', attr={'rel': re.compile('(?i)img_src')});
            if tags != None and len(tags) > 0:
                for tag in tags:
                    url = self.fixUrl(self._get_tag_attr(tag, 'content'), pageUrl)
                    if url != None:
                        urls.append(url)

        # always get all our images
        tags = pool.findAll('img');            
        if tags != None  and len(tags) > 0:
            for tag in tags:
                url = self.fixUrl(self._get_tag_attr(tag, 'src'), pageUrl)
                if url != None and url[-4] != '.gif':
                    urls.append(url)
        return urls;

    def screenUrl(self, url):
        """try to filter out images for a thumbnail based on ad like behavior"""
        if url.find("/ad/") > -1:
            return False;
            
        return True
        
    def fixUrl(self, url, pageUrl):
        """attempts to give a url an absolute path"""
        logging.debug("fixUrl('%s', '%s')" % (url, pageUrl))

        if self.screenUrl(url) == False:
            return None
            
        if url[0:4] == 'http':
            return url
        parse_url = urlparse(pageUrl)

        base_url = "%s://%s" % (parse_url[0], parse_url[1])

        
        if url[0:1] == '/':
            url = "%s%s" % (base_url, url)

        elif parse_url[2] == '':
            url = "%s/%s" % (base_url, url)

        else:
            path_parts = url.split('/')
            path_parts.pop()
            url = "%s/%s/" % (base_url, path_parts.join('/'), url)

        logging.debug("base_url %s" % base_url)
        logging.debug("url %s" % url)

        return url

    @authenticated
    def performAttachVideo(self):
        """xxx"""
        raise Exception("performAttachVideo not implemented.")
        return

    @authenticated
    def performAttachPhoto(self):
        """xxx"""
        raise Exception("performAttachPhoto not implemented.")
        return

    def performAuthentication(self):
        """xxx"""
        raise Exception("performAuthentication not implemented.")
        return

    @authenticated
    def performTopic(self):
        """xxx"""
        raise Exception("performTopic not implemented.")
        return

    def performMoreChildren(self):
        """get all the children for a parent"""
        comments = self.comment_item_queryset.load_comments_by_table_and_location(self.table, 
            self.location,  
            parentId = self.parentId, 
            parentCount=self.parentCount,
            childCount=self.childCount)

        parent_tag = 'p' + self.table[1:]

        context = {
            'app': self.application.get_settings('app'),
            'location': self.location,
            'parent_tag': parent_tag,
            'table': self.table,
            'comments': comments,
            'current_user': self.current_user,
            'related_user': None,
            'parentCount': self.parentCount,
            'childCount': self.childCount,
            'moreIndex': self.moreIndex,
        }
        
        self.add_to_payload("content", self.render_partial('comments.html', **context))

        return

    def performSort(self):
        """sort our items and return them all"""

        # our default (sort == 1)
        sortOrder = 'voteNumber';
        dateOrder = 'ASC';
        voteOrder = 'DESC';

        if self.sort == '3': # oldest
            sortOrder = 'createDate'
            dateOrder = 'ASC'
            voteOrder = None
        elif self.sort == '2': # recent
            sortOrder = 'createDate'
            dateOrder = 'DESC'
            voteOrder = None

        comments = self.comment_item_queryset.load_comments_by_table_and_location(self.table, 
            self.location,  
            parentOffset = self.moreIndex, 
            parentCount=self.settings['PARENT_PAGE_SIZE'] ,
            childCount=self.settings['CHILD_PAGE_SIZE'], 
            sortOrder=sortOrder, 
            dateOrder=dateOrder, 
            voteOrder=voteOrder)

        contributions = self.comment_queryset.get_count_by_table_and_location(self.table, self.location)


        parent_tag = 'p' + self.table[1:]
        context = {
            'app': self.application.get_settings('app'),
            'location': self.location,
            'parent_tag': parent_tag,
            'table': self.table,
            'comments': comments,
            'current_user': self.current_user,
            'related_user': None,
            'parentCount': self.parentCount,
            'childCount': self.childCount,
            'moreIndex': self.moreIndex,
        }
        
        self.add_to_payload("content", self.render_partial('comments.html', **context))

        return
         
    def performShareItem(self):
        """xxx"""
        raise Exception("performShareItem not implemented.")
        return

    @authenticated
    def performValidateLogin(self):
        """let the client know we are logged in"""
        # If we got this far, we are logged in, just send back our provider.
        self.add_to_payload('oAuthProvider', self.current_user.oauth_provider)
        return