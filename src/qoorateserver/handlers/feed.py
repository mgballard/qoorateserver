#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import urllib2
import functools
import logging
import os
import time
import random
import json
import datetime
import re
import traceback
import md5
import gevent
from urlparse import urlparse

import magic
from BeautifulSoup import BeautifulSoup
from brubeck.auth import authenticated
from brubeck.request_handling import JSONMessageHandler
from brubeck.templating import load_jinja2_env, Jinja2Rendering
from brubeckuploader.base import Uploader
from brubeckoauth.base import OAuthBase
from brubeckoauth.models import OAuthRequest


from qoorateserver.modules.brooklyncodebrubeck.application import lazyprop
from qoorateserver.handlers.base import QoorateMixin, admin_role
from qoorateserver.models.models import (
    CommentItem,
    User,
    Comment,
    ImageItem,
    Vote,
    Flag,
    FlagType
)
from qoorateserver.querysets.querysets import (
    CommentItemQueryset,
    CommentQueryset,
    ImageItemQueryset,
)

################################
## Methods used by gevent.spawn
################################
uploader = None
def upload_to_S3(settings, image_path):
    # parts of this (image crunching) are still blocking
    # we really need a seperate process here, gevent is not magic
    logging.debug("upload_to_S3 : %s" % image_path)
    global uploader
    if uploader is None:
        uploader = Uploader(settings) 
    uploader.upload_to_S3(image_path)

def delete_from_S3(settings, image_name):
    logging.debug("delete_from_S3 : %s" % image_name)
    global uploader
    if uploader is None:
        uploader = Uploader(settings) 
    uploader.delete_from_S3(image_name)
##
## Our feed handler class definitions
##
class FeedHandler(QoorateMixin, JSONMessageHandler, Jinja2Rendering):
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
        """replyComment argument.
        This is the text for a comment or photo
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
        """ replyPhoto argument.
        Not really used,
        but sent as a blank string to let us know it is a photo.
        """
        return self.get_argument('replyPhoto', None)

    @lazyprop
    def description(self):
        """ description argument.
        Used with link comment type.
        """
        return self.get_argument('description', None)

    @lazyprop
    def post_to(self):
        """ post_to argument.
        If present indicates we want to share the item 
        via current social network.
        """
        return self.get_argument('post_to', None)

    @lazyprop
    def is_anonymous(self):
        """ is_anonymous argument.
        If present indicates we want to post anonymously.
        """
        is_anonymous = 0
        if self.get_argument('is_anonymous', None) == '1':
            is_anonymous = 1
        return is_anonymous

    @lazyprop
    def locationId(self):
        """ locationId argument.
        Not sure how this is different than location.
        """
        return self.get_argument('locationId', 0)

    @lazyprop
    def relatedId(self):
        """ relatedId argument.
        The itemId of the parent for a reply.
        """
        return int(self.get_argument('relatedId', 0))

    @lazyprop
    def name(self):
        """ name argument.
        This is the text of a post. We default to the replyComment field.
        This really should be different. 
        Maybe smarter, and not just best guess?
        """
        return self.get_argument('replyComment', None)

    @lazyprop
    def thumbnailLarge(self):
        """ thumbnailLarge argument.
        This is the image link we want to be part of the comment.
        """
        return self.get_argument('thumbnailLarge', None)

    @lazyprop
    def qoorateId(self):
        """ qoorateId argument.
        Not used? remove soon?
        """
        return self.get_argument('qoorateId', None)

    @lazyprop
    def itemId(self):
        """ itemId argument.
        The itemId of the post we are requesting an action for.
        Used for actions like share and flag.
        """
        return self.get_argument('itemId', None)

    @lazyprop
    def comment(self):
        """ comment argument.
        Used in vote and flag, but never passed from application.
        """
        return self.get_argument('comment', None)

    @lazyprop
    def flagTypeId(self):
        """ flagTypeId argument.
        """
        return self.get_argument('flagTypeId', None)

    @lazyprop
    def uploader(self):
        """ Image mainipulation and s3 upload object.
        This is an extenal Brubeck Package.
        """
        return Uploader(self.application.get_settings('uploader'))

    @lazyprop
    def oauth_base(self):
        """get the base oauth object.
        This is an extenal Brubeck Package.
        """
        return OAuthBase()

    @lazyprop
    def oauth_settings(self):
        """get the base oauth settings"""
        return self.application.get_settings('oauth')

    @lazyprop
    def app_settings(self):
        """get the base app settings"""
        return self.application.get_settings('app')

    @lazyprop
    def anonymous_capable(self):
        """ See if we should a llow a post to be submitted anonymously by an authenticated user.
        The user is still stored with the record, but not displayed.
        """
        anonymous_capable = False
        if ('anonymous_capable' in self.app_settings and
            self.app_settings['ANONYMOUS_CAPABLE'] == 1):
                anonymous_capable = True
        return anonymous_capable

    @lazyprop
    def nickname(self):
        """ nickname used for anonymous posts.
        """
        return self.get_argument('nickname', None)


    # Voting constants
    UP = 1
    DOWN = -1

    def prepare(self):
        """prepare what we need for each request"""
        image_table = None
        if self.table == None:
            self.set_table()
        setattr(self, 'replycount', 0)
        if self.table != None:
            """it's ok if we don't get here.
            We may be a request that doesn't deal with comment items
            """
            logging.debug("feed.prepare, table: %s" % self.table)
            image_table = self.table + '_images'
            self._comment_queryset = CommentQueryset(
                self.application.get_settings('mysql'),
                self.application.db_conn,
                self.table
            )
            self._image_queryset = ImageItemQueryset(
                self.application.get_settings('mysql'),
                self.application.db_conn,
                image_table 
            )
            self._comment_item_queryset = CommentItemQueryset(
                self.application.get_settings('mysql'),
                self.application.db_conn,
                self.table 
            )

    def post(self):
        """rout to our proper performXXXXXX method
        Don't worry about authentication here, 
        the performXXXX has that responsibility
        """
        try:
            logging.debug("FeedHandler post")
            logging.debug("Body -> \n %s" % (self.message.body))
            logging.debug("Arguments -> \n %s" % (
                    json.dumps(self.message.arguments)
                )
            )
            logging.debug("action: %s" % self.action)
            
            ## we are just delegating here. 
            ## Since we follow a pattern here, we could probably be
            ## less verbose.
            if self.action == 'logoffUser':
                self.perform_logoff_user()
            elif self.action == 'addUser':
                self.perform_add_user()
            elif self.action == 'editUser':
                self.perform_edit_user()
            elif self.action == 'deleteUser':
                self.perform_delete_user()
            elif self.action == 'addRelated':
                self.perform_add_related()
            elif self.action == 'editRelated':
                self.perform_edit_related()
            elif self.action == 'deleteRelated':
                self.perform_delete_related()
            elif self.action == 'deleteComment':
                self.perform_delete_comment()
            elif self.action == 'addItem':
                self.perform_add_item()
            elif self.action == 'editItem':
                self.perform_edit_item()
            elif self.action == 'deleteItem':
                self.perform_delete_item()
            elif self.action == 'addTag':
                self.perform_add_tag()
            elif self.action == 'editTag':
                self.perform_edit_tag()
            elif self.action == 'deleteTag':
                self.perform_delete_tag()
            elif self.action == 'upVote':
                self.perform_vote(self.UP)
            elif self.action == 'downVote':
                self.perform_vote(self.DOWN)
            elif self.action == 'addQoorate':
                self.perform_add_qoorate()
            elif self.action == 'editQoorate':
                self.perform_edit_qoorate()
            elif self.action == 'deleteQoorate':
                self.perform_delete_qoorate()
            elif self.action == 'attachLink':
                self.perform_attach_link()
            elif self.action == 'attachVideo':
                self.perform_attach_video()
            elif self.action == 'attachPhoto':
                self.perform_attach_photo()
            elif self.action == 'authentication':
                self.perform_authentication()
            elif self.action == 'flag':
                self.perform_flag()
            elif self.action == 'createTopic':
                self.perform_topic()
            elif self.action == 'getMoreChildren':
                self.perform_more_children()
            elif self.action == 'getMore':
                self.perform_more()
            elif self.action == 'shareItem':
                self.perform_share_item()
            elif self.action == 'sort':
                self.perform_sort()
            elif self.action == 'validateLogin':
                self.perform_validate_login()
            elif self.action == 'queryComments':
                self.perform_query_comments()
            else:
                raise Exception("Unsupported action: %s" % self.action)
        except Exception as e:
            logging.info("ERROR: (%s)%s" % (e.message, traceback.format_exc()));
            self.set_status(500)
            self.add_to_payload('error', 1)
            self.add_to_payload('message', e.message)
            self.add_to_payload('action', self.action)
            return self.render()
        # Success
        # The client expects error = 0 to mean success
        self.add_to_payload('contributions', self.get_contribution_count())
        self.add_to_payload('q_short_name', self.q_short_name)
        self.add_to_payload('location', self.location)
        self.add_to_payload('replycount', self.replycount)
        self.add_to_payload('error', 0)
        self.set_status(200)
        return self.render()

    def get_contribution_count(self):
        """adds our contribtion count to the payload"""
        if self.table == None or self.location == None:
            return 0
        else:
            return self.comment_queryset.get_count_by_table_and_location(
                self.table, self.location
            )

    ##
    ## All off our action methods
    ## Not all of these are implemented, or even needed
    ## However, they are left here for legacy documentation
    ## since this is a rewrite of a PHP prototype
    ##
    def perform_logoff_user(self):
        """removes the session cookie from our user"""
        if self.current_user != None:
            self.user_queryset.logout_by_qooid(self.qooid)
        return

    def perform_add_user(self):
        raise NotImplementedError

    @authenticated
    def perform_edit_user(self):
        raise NotImplementedError

    @authenticated
    def perform_delete_user(self):
        raise NotImplementedError

    @authenticated
    def perform_add_related(self):
        raise NotImplementedError

    @authenticated
    def perform_edit_related(self):
        raise NotImplementedError

    @authenticated
    def perform_delete_related(self):
        raise NotImplementedError

    @authenticated
    def perform_delete_comment(self):
        raise NotImplementedError

    @authenticated
    def perform_add_item(self):
        """add a new item (comment, topic, photo or link)"""        
        if self.table == None:
            raise Exception("Table must be set!")
        name = (self.replyTopic if self.replyTopic != None else
            self.replyPhoto if self.replyPhoto != None else
            self.replyComment if self.replyLink != None else
            self.replyComment if self.replyComment != None else None)
        
        #if name is not None:
        #    name = name.encode('ascii', 'xmlcharrefreplace')

        
        type = (10 if self.replyTopic != None else
            2 if self.replyLink != None else
            1 if self.replyPhoto != None else
            0 if self.replyComment != None else None)
        parent = None
        related_comment = None
        related_user = None
        if self.relatedId > 0:
            related_comment = self.comment_queryset.read_one(
                self.relatedId,
                table_name=self.table
            )[1]
            self._parentId = related_comment['parentId'] if (
                related_comment['parentId'] !=0) else related_comment['id']
            related_user = User(
                **self.user_queryset.read_one(related_comment['userId'])[1]
            )
            # needed to make sure we return all comments later
            self._childCount = 0; 
        comment_image = None
        if self.replyLink != None:
            if self.thumbnailLarge != None and self.thumbnailLarge != '':
                self._thumbnailLarge = self.uploader.download_image_from_url(
                    self.thumbnailLarge
                )
            self._description = self.replyLink
        if self.thumbnailLarge != None and self.thumbnailLarge != '':
            # we are a photo, or a replyLink
            # save to S3
            # we may need to set this now 
            # because we are using replyComment to post
            # should be replyLink (or just send the type)
            if type != 2:
                type = 1

            # do us async now, temp image will be displayed to user
            # we still need to deal with failure
            
            spawned = self.settings["BACKGROUND_S3_UPLOAD"]
            uploaded = False
            if spawned:
                logging.debug("spawning upload")
                gevent.joinall([
                    gevent.spawn(upload_to_S3, self.application.get_settings('uploader'), self.thumbnailLarge)
                    ])
                uploaded = True
                logging.debug("spawned upload")
            else:
                logging.debug("blocking upload start")
                uploaded = self.uploader.upload_to_S3(self.thumbnailLarge)
                logging.debug("blocking upload done")
            if uploaded:
                image_data = {
                    'id': None,
                    'itemId': None,
                    's3Bucket': self.settings['AMAZON_BUCKET'],
                    'thumbnailLargeHash': self.thumbnailLarge,
                }
                comment_image = ImageItem(**image_data)
                # don't save us yet, we still need our comment id
            else:
                raise Exception('Unable to upload photo.')
        now = datetime.datetime.now()
        data = {
            'locationId':       self.locationId,
            'relatedId':        self.relatedId,
            'parentId':         self.parentId, 
            'name':             name,
            'location':         self.location,
            'userId':           self.current_user.id,
            'type':             type,
            'is_anonymous':     self.is_anonymous,
            'voteCount':        0,
            'voteNumber':       0,
            'votesUp':          0,
            'votesDown':        0,
            'flagCount':        0,
            'childCount':       0,
            'sortOrder':        0,
            'status':           '',
            'description':      self.description,
            'thumbnailLarge':   self.thumbnailLarge,
            'referer':          self.referer,
            'changeDate':       now,
            'createDate':       now,
            'nickname':         self.nickname,
        }
        item = Comment(**data)
        #logging.debug(json.dumps(item))
        result = self.comment_queryset.create_one(item, table_name=self.table)
        if self.comment_queryset.MSG_CREATED == result[0]:
            item = result[1]
            parent_item = self.update_child_count(item)
            if parent_item != None and parent_item.childCount != None:
                self.replycount = parent_item.childCount
            if comment_image != None:
                comment_image.itemId = item.id
                comment_image = self.image_queryset.create_one(
                    comment_image,
                    table_name = self.table + '_images'
                )
            # logging.debug(json.dumps(item))
            parent_tag = 'p' + self.table[1:]
            context = {
                'app': self.application.get_settings('app'),
                'location': self.location,
                'parent_tag': parent_tag,
                'q_short_name': self.q_short_name,
                'comments': [item],
                'current_user': self.current_user,
                'related_user': related_user,
                'comment_images': [comment_image],
                'thumbnailLargeHash': self.thumbnailLarge,
                'parentCount': self.parentCount,
                'childCount': self.childCount,
                'moreIndex': self.moreIndex,
                'has_more_contributions': False,
                'is_admin': self.is_admin,
            }
            # share us if we have been asked to
            if not self.post_to is None:
                logging.debug("sharing new item.")
                provider = None
                user = self.current_user
                if user.oauth_provider=='fb':
                    provider = 'facebook'
                elif user.oauth_provider=='tw':
                    provider = 'twitter'
                if not provider == None:
                    provider_settings = self.oauth_settings['PROVIDERS'][provider]
                    oauth_request_model = self.create_oauth_request_model(
                        provider_settings,
                        user
                    )
                    if self._share(item, oauth_request_model, provider_settings, True):
                        # success
                        logging.debug("Shared new item.")
                    else:
                        # failure
                        logging.debug("Unable to share new item.")
            # currentlly JS wants all comments for a parent when a reply is made
            # so, we will do the same for now. seems harsh.
            if item.parentId > 0:
                comments = self.comment_item_queryset.load_comments_by_table_and_location(
                    self.table, 
                    self.location, 
                    parentId = item.parentId
                )
                comments = self.place_new_item_after_related(comments, item)
                context['comments'] = comments
                context['has_more_contributions'] = self.has_more_contributions(
                    comments
                )
            logging.debug("CONTEXT: %s" % context)
            html = self.render_partial(self.preferences['THEME'] + '/comments.html', **context)
            logging.debug(html)
            self.add_to_payload('item', item)
            self.add_to_payload('content', html)
            return
        raise Exception('Unknown error occured, unable to add item.')

    def place_new_item_after_related(self, comments, item):
        """we want the new item to always be after related item"""
        logging.debug("place_new_item_after_related")
        item_index = -1
        related_item_index = -1
        if len(comments) > 2:
            for x in range(0, len(comments)):
                comment = comments[x]
                if comment.id == item.id:
                    item_index = x
                logging.debug("comment.id: %s" % comment.id)
                logging.debug("item.relatedId: %s" % item.relatedId)
                logging.debug("equal: %s\n\n" % (
                        comment.id == item.relatedId
                    )
                )
                if comment.id == item.relatedId:
                    related_item_index = x
                if item_index>0 and related_item_index > 0:
                    break;
            logging.debug("item_index: %s" % item_index)
            logging.debug("related_item_index: %s" % related_item_index)
            item = comments[item_index]
            del comments[item_index]

            if related_item_index == 0:
                comments = [comments[0]] + [item] + comments[1:]
            elif related_item_index + 1 == len(comments):
                comments += [item]
            else:
                comments = (comments[0:related_item_index + 1] +
                           [item] + comments[related_item_index + 1:])
            # fix our child sequence
            for y in range(0, len(comments)):
                comment = comments[y]
                comment.child_sequence = y
        return comments

    @authenticated
    def perform_edit_item(self):
        raise NotImplementedError

    @authenticated
    @admin_role
    def perform_delete_item(self):
        """ delete a single item and all related content """
        logging.debug("perform_delete_item()")
        result = self.comment_queryset.read_one(self.itemId)[1]
        deleted_item_ids = []
        if result != None:
            logging.debug("found item to delete")
            item = Comment(**result)
            # remove any related image records (including removing images from S3?)
            # right now we fire and forget, deleting the image record no matter what
            if item.type == 1:
                logging.debug("perform_delete_item, removing images.")
                spawned = self.settings["BACKGROUND_S3_UPLOAD"]
                deleted = False
                if spawned:
                    logging.debug("spawning delete")
                    gevent.joinall([
                        gevent.spawn(delete_from_S3, self.application.get_settings('uploader'), item.thumbnailLarge)
                        ])
                    uploaded = True
                    logging.debug("spawned delete")
                else:
                    logging.debug("blocking delete start")
                    uploaded = self.uploader.delete_from_S3(item.thumbnailLarge)
                    logging.debug("blocking delete done")
                self.image_queryset.delete_by_item_id(self.table, item.id)

            # remove any related flags
            self.flag_queryset.delete_by_item(item)
            # remove any related votes
            self.vote_queryset.delete_by_item(item)
            # remove any related comments
            if item.parentId == 0:
                # we need to loop through child items to remove all flags and votes too
                child_item_ids = self.comment_queryset.get_ids_by_parent_id(self.table, item.id)
                for child_item_id in child_item_ids:
                    child_item_result = self.comment_queryset.read_one(child_item_id)[1]
                    if child_item_result != None:
                        child_item = Comment(**child_item_result)
                        # remove any related child item flags
                        self.flag_queryset.delete_by_item(child_item)
                        # remove any related child item votes
                        self.vote_queryset.delete_by_item(child_item)
                        # remove our child item
                        result = self.comment_queryset.destroy_one(child_item.id)
                        deleted_item_ids.append(child_item.id)
            else:
                deleted_item_ids.append(self.delete_related_items(item, deleted_item_ids))
            # remove comment item itself
            logging.debug('perform_delete_item: removing requested item (%s)' % self.itemId)
            result = self.comment_queryset.destroy_one(self.itemId)
            if item.parentId > 0:
                parent_item = self.update_child_count(item)
                self.replycount = parent_item.childCount
        else:
            logging.debug('perform_delete_item: item not found (%s)' % self.itemId)

        self.add_to_payload('item', item)
        self.add_to_payload('deleted_related_item_ids', json.dumps(deleted_item_ids))
        return

    @authenticated
    @admin_role
    def delete_related_items(self, item, deleted_item_ids):
        # we need to loop through related items to remove all flags and votes too
        # this is called recursively
        related_item_ids = self.comment_queryset.get_related_ids_by_item_id(self.table, item.id)
        if len(related_item_ids) > 0:
            for related_item_id in related_item_ids:
                related_item_result = self.comment_queryset.read_one(related_item_id)[1]
                if related_item_result != None:
                    related_item = Comment(**related_item_result)
                    # remove any related item flags
                    self.flag_queryset.delete_by_item(related_item)
                    # remove any related item votes
                    self.vote_queryset.delete_by_item(related_item)
                    # remove our related item
                    result = self.comment_queryset.destroy_one(related_item.id)
                    deleted_item_ids.append(related_item.id)
                    self.delete_related_items(related_item, deleted_item_ids)

    @authenticated
    def perform_add_tag(self):
        raise NotImplementedError

    @authenticated
    def perform_edit_tag(self):
        raise NotImplementedError

    @authenticated
    def perform_delete_tag(self):
        raise NotImplementedError

    ##
    ## Voting methods
    ##

    def perform_vote(self, direction):
        """perform a requested vote"""
        logging.debug("perform_vote(%s)" % direction)
        parent_votes = None
        votes = None
        if self.itemId == None:
            self._itemId = self.relatedId
        item = None
        result = self.comment_queryset.read_one(
            self.itemId, 
            table_name=self.table
        )[1]
        if result != None:
            item = Comment(**result)
            vote = self._vote(direction, item)
            item = self.update_vote_counts(item)
            if item.parentId != 0:
                # We need to recalculate our parent votes 
                # and return the results too
                parentItem = None
                result = self.comment_queryset.read_one(
                    item.parentId,
                    table_name=self.table
                )[1]
                if result != None:
                    parentItem = Comment(**result)
                    parentItem = self.update_vote_counts( parentItem );
                    # add our parent votes to the payload
                    self.add_to_payload(
                        'parent_votes', ("{"
                        "'voteCount': %s,"
                        "'voteNumber': %s,"
                        "'votesUp': %s,"
                        "'votesDown': %s"
                        "}") % (
                            parentItem.voteCount, parentItem.voteNumber,
                            parentItem.votesUp, parentItem.votesDown
                        )
                    )
            logging.debug("perform_vote adding to payload")
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
        # logging.debug(json.dumps(item)())
        votes = self.vote_queryset.get_vote_counts_by_item_id(
            item.id,
            self.table,
            includeChildVotes
        )
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
        result = self.comment_queryset.create_one(
            item,
            table_name=self.table
        )[1]
        if result == None:
            return item
        return result

    def _vote(self, direction, item):
        """records a vote on an item"""
        logging.debug("_vote(%s, %s)" % (direction, item))
        user_id = self.current_user.id if self.current_user != None else 0
        logging.debug("user_id, item.userId: %s, %s" % (
                user_id,
                item.userId
            )
        )
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
            vote = self.vote_queryset.get_by_item_id_and_user_id(
                self.table, item.id, user_id
            )
        else:
            vote = self.vote_queryset.get_by_item_id_and_qootid(
                self.table, item.id, self.qootid
            )
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
    def perform_flag(self):
        """perform a flag"""
        logging.debug("perform_flag")
        if self.itemId == None:
            self._itemId = self.relatedId
        item = None
        result = self.comment_queryset.read_one(
            self.itemId, table_name=self.table
        )[1]
        if result != None:
            item = Comment(**result)
            flag = self._flag(item)
            item = self.update_flag_count(item)
            flag = self.flag_queryset.get_flag_by_refTableitemIduserId(self.table, item.id, self.current_user.id)
            self.send_flag_alert(item, flag)
            logging.debug("perform_flag adding to payload")
            self.add_to_payload('flagCount', str(item.flagCount))
            logging.debug("flagCount: %s " % item.flagCount)
            success_message = ""
            self.add_to_payload('message', success_message)
            logging.debug("message: %s " % success_message)
        return

    def update_flag_count(self, item):
        """Updates the vote count for the item"""
        logging.debug("update_flag_count(%s)" % item)
        # logging.debug(json.dumps(item)())
        flags = self.flag_queryset.get_flag_count_by_item_id(
            item.id, self.table
        )
        logging.debug(flags)
        # update our item with new vote totals
        item.flagCount = flags
        result = self.comment_queryset.create_one(
            item, table_name=self.table
        )
        if result == None:
            return item
        return result[1]

    def _flag(self, item):
        """records a flag on an item"""
        logging.debug("_flag(%s)" % (item))

        # Make sure we have a valid flag type
        result = self.flag_type_queryset.read_one(
                self.flagTypeId
            )[1]
        if result == None:
            logging.debug("Unknown flag_type: %s" % self.flagTypeId)
            raise Exception("Unknown flag type!")
        else:
            logging.debug("flag_type found: %s" % self.flagTypeId)
        # Make sure we have permission to flag as this type
        flag_type = FlagType(**result)
        if flag_type.role == 1 and not self.is_admin:
            logging.debug("flag_type is admin, you are not: %s" % self.current_user.id)
            raise Exception("Unauthorized flag type!")
        else:
            logging.debug("flag_type is authorized: %s" % self.flagTypeId)
        # check for an existing flag record for the user
        flag = self.flag_queryset.get_by_item_id_and_user_id(
            self.table, item.id, self.current_user.id
        )
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
            logging.debug("result == None")
            return flag
            logging.debug("NOT result == None")
        return result[1]

    def send_flag_alert(self, item, flag):
        """send an email alert about a flag action"""
        #logging.debug("sendFlagAlert item:%s" % (item));
        #logging.debug("sendFlagAlert flag flagTypeId: %s" % (flag.flagTypeId));
        #logging.debug("sendFlagAlert flag id: %s" % (flag.id));
        flag_info = self.flag_queryset.get_flag_email_alert_info_by_id(flag['id'])
        # send our email
        settings = self.application.settings;
        subject            = "QOORATE FLAG: %s" % flag_info['flagTypeId']
        to_address         = flag_info['adminEmail']
        cc_address         = settings.app["ADMIN_EMAIL_ADDRESS"]
        username           = flag_info['username']
        adminUsername      = flag_info['adminUsername']
        flagType           = flag_info['flagType']
        itemName           = flag_info['name']
        from_address       = settings.app["FROM_EMAIL_ADDRESS"]
        from_name          = settings.app["FROM_NAME"]
        flaggerUsername    = self.current_user.username;
        
        self._referer = self.referer.split("#")[0];
        
        item_url = "%s#%s-%s" % (self.referer, self.table, item.id);
        message = ("Hello %s,\r\n\r\n"
        "An item from %s has been flagged as '%s' by %s.\r\n\r\n"
        "The comment was:\r\n\r\n"
        "%s \r\n\r\n"
        "You can view the item here:\r\n\r\n"
        "%s \r\n\r\n"
        "Thanks,\r\n\r\n"
        "%s") % (
            adminUsername, username,
            flagType, flaggerUsername,
            itemName, item_url,
            from_name
        )
        if (to_address != cc_address and 
            "CC_ADMIN_FLAG_EMAILS" in self.settings and 
            self.settings["CC_ADMIN_FLAG_EMAILS"]):
            cc_address = "\r\nCC: " + cc_address 
        else:
            cc_address = ''
        headers = "From: " + from_address + cc_address
        # OLD PHP CODE
        #mail ( to_address , subject , message, headers )
        return

    def perform_add_qoorate(self):
        raise NotImplementedError

    @authenticated
    def perform_edit_qoorate(self):
        raise NotImplementedError

    @authenticated
    def perform_delete_qoorate(self):
        raise NotImplementedError

    @authenticated
    def perform_attach_link(self):
        """get a list of image urls from a page"""
        replyLink = self.get_argument('replyLink', None)
        title = None
        description = None
        images = []
        if replyLink != None:
            try:
                response = urllib2.urlopen(replyLink)
                the_page = response.read()
                pool = BeautifulSoup(the_page)
                title = self.get_link_title(pool)
                description = self.get_link_description(pool)
                images = self.get_link_images(pool, replyLink)
                self.add_to_payload('title', title)
                self.add_to_payload('description', description)
                self.add_to_payload('images', images)
            except Exception as e:
                    raise Exception('Unable to fetch images for %s' % replyLink);
        else:
            raise Exception('replyLink not set for request');

        return

    def get_link_title(self, pool):
        """get title tag from a BeatifulSoup 'pool'"""
        title = ''
        tag = pool.find('meta', attr={
                'property': re.compile("^og:title$", re.I)
            }
        )
        if tag != None:
            title = self._get_tag_attr(tag, 'content')
        else:
            tag = pool.find('title');
            if tag != None:
                title =  tag.contents
            else:
                tag = pool.find('meta', attr={
                        'name': re.compile("^title$", re.I)
                    }
                )
                if tag != None:
                    title = self._get_tag_attr(tag, 'content')
        if len(title) > 0:
            title = title[0]
        return title;

    def _get_tag_attr(self, pool, attr):
        """used to get an atrribute from beatiful soup,
        and give us nothing if doesn't exist"""
        try:
            return pool[attr]
        except:
            pass
        return None        

    def get_link_description(self, pool):
        """get title tag from a BeatifulSoup 'pool'"""
        description = ''
        tag = pool.find('meta', attr={
                'property': re.compile('(?i)og:description')
            }
        );
        if tag != None and len(tag) > 0:
            description = self._get_tag_attr(tag, 'content')
        else:
            tag = pool.find('meta', {'name': re.compile('(?i)description')})
            if tag != None:
                description = self._get_tag_attr(tag, 'content')
        return description

    def get_link_images(self, pool, pageUrl):
        """get image choices to attach to a link 
        from a BeatifulSoup 'pool'
        """
        urls = []
        tags = pool.findAll('meta', attr={
                'property': re.compile('(?i)og:image')
            }
        )
        if tags != None and len(tags) > 0:
            for tag in tags:
                try:
                    url = self.fix_url(
                        self._get_tag_attr(tag, 'content'),
                        pageUrl
                    )
                    if url != None:
                        urls.append(url)
                except:
                    pass
        else:
            tags = pool.findAll('link', attr={
                    'rel': re.compile('(?i)img_src')
                }
            )
            if tags != None and len(tags) > 0:
                for tag in tags:
                    url = self.fix_url(
                        self._get_tag_attr(tag, 'content'),
                        pageUrl
                    )
                    if url != None:
                        urls.append(url)
        # always get all our images
        tags = pool.findAll('img')
        if tags != None  and len(tags) > 0:
            for tag in tags:
                url = self.fix_url(
                    self._get_tag_attr(tag, 'src'),
                    pageUrl
                )
                if url != None and url[-4] != '.gif':
                    urls.append(url)
        return urls

    def screen_url(self, url):
        """try to filter out images for a thumbnail 
        based on ad like behavior
        """
        if url == None or url.find("/ad/") > -1:
            return False;
        return True

    def fix_url(self, url, pageUrl):
        """attempts to give a url an absolute path"""
        logging.debug("fix_url('%s', '%s')" % (url, pageUrl))
        if self.screen_url(url) == False:
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
    def perform_attach_video(self):
        raise NotImplementedError

    @authenticated
    def perform_attach_photo(self):
        raise NotImplementedError

    def perform_authentication(self):
        raise NotImplementedError

    @authenticated
    def perform_topic(self):
        raise NotImplementedError

    ##
    ## paging functions
    ##

    def get_comment_context(self, comments):
        parent_tag = 'p' + self.table[1:]
        context = {
            'app': self.application.get_settings('app'),
            'location': self.location,
            'parent_tag': parent_tag,
            'q_short_name': self.q_short_name,
            'comments': comments,
            'current_user': self.current_user,
            'related_user': None,
            'parentCount': self.parentCount,
            'childCount': self.childCount,
            'moreIndex': self.moreIndex,
            'has_more_contributions': self.has_more_contributions(comments),
            'is_admin': self.is_admin,
        }
        return context

    def _get_sort_parameters(self):
        """Get our sort parameters and attach our properties to self."""
        # our default (sort == 1)
        self.sortOrder = 'voteNumber';
        self.dateOrder = 'ASC';
        self.voteOrder = 'DESC';
        if self.sort == '3': # oldest
            self.sortOrder = 'createDate'
            self.dateOrder = 'ASC'
            self.voteOrder = None
        elif self.sort == '2': # recent
            self.sortOrder = 'createDate'
            self.dateOrder = 'DESC'
            self.voteOrder = None

    def perform_more(self):
        """get more contributions"""
        self._get_sort_parameters()
        comments = self.comment_item_queryset.load_comments_by_table_and_location(
            self.table, 
            self.location, 
            parentOffset = self.moreIndex, 
            parentCount=self.parentCount, 
            childCount=self.childCount, 
            sortOrder=self.sortOrder, 
            dateOrder=self.dateOrder, 
            voteOrder=self.voteOrder)
        context = self.get_comment_context(comments)
        self.add_to_payload("content", self.render_partial(
                self.preferences['THEME'] + '/comments.html',
                **context
            )
        )
        return

    def perform_query_comments(self):
        """get more contributions"""
        self._get_sort_parameters()
        comments = self.comment_item_queryset.load_comments_by_table_and_location(
            self.table, 
            self.location, 
            parentOffset = self.moreIndex, 
            parentCount=self.parentCount, 
            childCount=self.childCount, 
            sortOrder=self.sortOrder, 
            dateOrder=self.dateOrder, 
            voteOrder=self.voteOrder,
            flagTypeId=self.flagTypeId, 
        )
        query = {
            "table": self.table, 
            "location": self.location, 
            "parentOffset": self.moreIndex, 
            "parentCount": self.parentCount, 
            "childCount": self.childCount, 
            "sortOrder": self.sortOrder, 
            "dateOrder": self.dateOrder, 
            "voteOrder": self.voteOrder,
            "flagTypeId": self.flagTypeId, 
        }
        # return our comments as json items
        self.add_to_payload("comments", comments)
        # return our query parameters used to request items
        self.add_to_payload("query", query)
        return

    def perform_more_children(self):
        """get all the children for a parent"""
        self._get_sort_parameters()
        comments = self.comment_item_queryset.load_comments_by_table_and_location(
            self.table, 
            self.location, 
            parentId = self.parentId, 
            parentCount=self.parentCount,
            childCount=self.childCount, 
            sortOrder=self.sortOrder, 
            dateOrder=self.dateOrder, 
            voteOrder=self.voteOrder)
        context = self.get_comment_context(comments)
        self.add_to_payload("content", self.render_partial(
                self.preferences['THEME'] + '/comments.html',
                **context
            )
        )
        return

    def perform_sort(self):
        """sort our items and return them all"""
        self._get_sort_parameters()
        comments = self.comment_item_queryset.load_comments_by_table_and_location(
            self.table, 
            self.location, 
            parentOffset = self.moreIndex, 
            parentCount=self.settings['PARENT_PAGE_SIZE'] ,
            childCount=self.settings['CHILD_PAGE_SIZE'], 
            sortOrder=self.sortOrder, 
            dateOrder=self.dateOrder, 
            voteOrder=self.voteOrder)
        contributions = self.comment_queryset.get_count_by_table_and_location(
            self.table,
            self.location
        )
        parent_tag = 'p' + self.table[1:]
        context = {
            'app': self.application.get_settings('app'),
            'location': self.location,
            'parent_tag': parent_tag,
            'q_short_name': self.q_short_name,
            'comments': comments,
            'current_user': self.current_user,
            'related_user': None,
            'parentCount': self.parentCount,
            'childCount': self.childCount,
            'moreIndex': self.moreIndex,
            'has_more_contributions': self.has_more_contributions(comments)
        }
        self.add_to_payload("content", self.render_partial(
                self.preferences['THEME'] + '/comments.html',
                **context
            )
        )
        return

    @authenticated
    def perform_share_item(self):
        """Share an item on the current logged in social network"""
        """ SAMPLE REQUEST:
        replyComment:test share
        post:
        action:shareItem
        location:acd150a6885f609532931d89844070b1
        referer:http://qrate.co/q_test.php
        table:q_demo
        itemId:46
        relatedId:46
        """
        logging.debug("perform_share_item")
        item = Comment(**self.comment_queryset.read_one(self.itemId)[1])
        provider = ''
        user = self.current_user
        if user.oauth_provider=='fb':
            provider = 'facebook'
        elif user.oauth_provider=='tw':
            provider = 'twitter'
        else:
            raise Exception('Unsupported oauth provider for sharing: ' % (
                    user.oauth_provider
                )
            )
        logging.debug("provider: %s" % provider)
        provider_settings = self.oauth_settings['PROVIDERS'][provider]

        oauth_request_model = self.create_oauth_request_model(
            provider_settings,
            user
        )
        if self._share(item, oauth_request_model, provider_settings):
            # success
            self.add_to_payload("shareItem", "complete")
            self.add_to_payload("item", item)
            return
        else:
            # failure
            raise Exception('Unable to share item.')
        return

    @authenticated
    def _share(self, item, oauth_request_model, provider_settings, is_new_item=False):
        """share an item via you logged in social network"""
        q = '"' # used to wrap comment
        item_user = User(**self.user_queryset.read_one(item.userId)[1])
        # prepend our additional comment if needed
        text = ''
        if is_new_item == False and self.replyComment != '':
            text = "%s:\n\n" % self.replyComment 
        else:
            q = ''
        oauth_object = self.oauth_base.get_oauth_object(provider_settings)
        logging.debug("_share, provider_tag: %s" % oauth_request_model.provider_tag)
        logging.debug("_share, item.type: %s" % item.type)
        logging.debug("_share, item.name: %s" % item.name)
        logging.debug("_share, item.description: %s" % item.description)
        logging.debug("_share, self.referer: %s" % self.referer)
        logging.debug("_share, self.itemId: %s" % self.itemId)
        logging.debug("_share, self.replyComment: %s" % self.replyComment)
        if oauth_request_model.provider_tag == 'tw':
            text = "%s%s%s" % (text, q, item.name)
            if item.type == 2:
                if len(text) > 90:
                    text = '%s%s' % (text[0:90], '...')
                text = "%s\n%s" % (text, item.description)
            else:
                if len(text) > 100:
                    text = "%s%s" % (text[0:100], '...')
            ref = self.referer.split("#")[0]
            link = "%s#%s-%s" % (ref, self.table, item.id)
            text = "%s%s\n%s" % (text, q, link)
            url = "https://api.twitter.com/1.1/statuses/update.json"
            query_params = {}
            post_vars = { "status": text}
            response = oauth_object.request(
                provider_settings,
                "POST",
                url,
                post_vars,
                oauth_request_model
            )
            # logging.debug(json.dumps(oauth_request_model))
            if 'error' in response:
                raise Exception(response['error'])
            return True
        elif oauth_request_model.provider_tag == 'fb':
            text = "%s%s%s" % (text, q, item.name)
            if item.type == 2:
                comment_link =  item.description
                # facebook doesn't take an educated 
                # guess at a link without a protocol
                if comment_link[0:4] != 'http':
                    comment_link = "http://%s" % comment_link
                text  = "%s %s" % (text, comment_link)

            ref = self.referer.split("#")[0]
            link = "%s#%s" % (ref, item.id)

            text = "%s%s\n%s" % (text, q, link)
            url = "https://graph.facebook.com/%s/feed" % (
                self.current_user.oauth_uid
            )
            post_vars = {
                'access_token' : oauth_request_model.token,
                'message' : text,
            }
            response = oauth_object.request(
                provider_settings,
                "POST",
                url,
                post_vars,
                oauth_request_model,
            )
            return True;
        else:
            raise Exception('Unsupported oauth provider for sharing: ' % (
                    oauth_request_model.oauth_provider
                )
            )

    def create_oauth_request_model(self, provider_settings, user):
        """passed provider settings and a user
        returns an OAuthRequest object
        """
        logging.debug(user.oauth_data)
        oauth_data = json.loads(user.oauth_data)
        data = {
            'id': self.qooid,
            'api_id': self.qooid,
            'session_id': self.qooid,
            'token_secret': oauth_data['oauth_token_secret'] if (
                'oauth_token_secret') in oauth_data else None,
            'token': user.oauth_access_token,
            'provider': provider_settings['PROVIDER_NAME'],
            'provider_tag': provider_settings['PROVIDER_TAG'],
            'data': user.oauth_data,
        }
        return OAuthRequest(**data)

    @authenticated
    def perform_validate_login(self):
        """let the client know we are logged in"""
        # If we got this far, we are logged in, 
        # just send back our provider.
        self.add_to_payload('oAuthProvider', self.current_user.oauth_provider)
        self.add_to_payload('is_admin', self.is_admin)
        return

    def update_child_count(self, item):
        """Updates the vote count for the item. if the item is a child, the parent is updated"""
        logging.debug("update_child_count(%s)" % item)
        if item.parentId > 0:
            result = self.comment_queryset.read_one(item.parentId)[1]
            if result != None:
                item = Comment(**result)
                logging.debug("update_child_count fetched parent: %s" % item)
            else:
                logging.debug("update_child_count parent not found: %s" % item.parentId)
        # logging.debug(json.dumps(item)())
        child_count = self.comment_queryset.get_child_count_by_item_id(
            self.table, item.id
        )
        logging.debug("child_count: %s" % child_count)
        # update our item with new child count
        item.childCount = child_count
        result = self.comment_queryset.create_one(
            item, table_name=self.table
        )
        if result == None:
            return item
        return result[1]
