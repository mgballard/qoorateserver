#!/usr/bin/env python
# -*- coding: utf-8 -*-
from qoorateserver.modules.brooklyncodebrubeck.application import BrooklynCodeBrubeck
from brubeckmysql.base import create_db_conn
import time
import datetime
import logging
from gevent.queue import Queue
from gevent.greenlet import Greenlet
from gevent.event import Event

##
## Submit an item to be generate a relevancy index
##

def qoorate_determine_relevency(application, item):
    """schedule an indexing using concurrency"""
    logging.info("qoorate_determine_relevency, start: %s" % item)
    g = Greenlet(qoorate_generate_relevency, item)
    logging.info("qoorate_generate_relevency, greenlet, start(): %s" % item)
    g.start()
    logging.info("qoorate_generate_relevency, end: %s" % item)

def qoorate_generate_relevency(application, item):
    """ generate our relevancy number and persist the item"""
    # this is the algorithm to determine the actual number
    def qoorate_compute_relevency(item):
        """generate our index for relevancy."""   
        logging.info("qoorate_compute_relevency, start: %s" % item)
        relevancy = 0
        # for now just use voting logic already in place
        votesUp = item.votesUp
        votesDown = item.votesDown
        if votesUp== None:
            votesUp = 0;
        if votesDown== None:
            votesDown = 0;
        voteCount = votesUp + votesDown
        voteNumber = votesUp - votesDown
        if item.type == 10 :
            voteNumber = voteCount
        logging.info("qoorate_compute_relevency, end: %s (%s)" % item, relevancy)
        relevancy = voteNumber
        return relevancy

    # call and log our actions
    logging.info("qoorate_generate_relevency, start: %s" % item)
    relevancy = qoorate_compute_relevency(application, item)    
    if item.sortOrder != relevancy:
        # update our sortOrder
        logging.info("qoorate_generate_relevency, update sort order, start: %s (%s, %s)" % item, item.sortOrder, relevancy)
        comment_queryset = CommentQueryset(
            application.get_settings('mysql'),
            item.tableName, application.db_conn
        )
        item.sortOrder = relevancy
        results = self._comment_item_queryset.create_one(
                    item,
                    table_name = item.tableName
                )
        if comment_queryset.MSG_UPDATED == result[0]:
            logging.info("qoorate_generate_relevency, UPDATE SUCCESS: %s (%s)" % item, relevancy)

    logging.info("qoorate_generate_relevency, end: %s (%s)" % item, relevancy)
    return relevancy

def qoorate_compute_relevency(item):
    """generate our index for relevancy."""   
    logging.info("qoorate_compute_relevency, start: %s" % item)
    # for now just use voting logic already in place
    votesUp = item.votesUp
    votesDown = item.votesDown
    if votesUp== None:
        votesUp = 0;
    if votesDown== None:
        votesDown = 0;
    voteCount = votesUp + votesDown
    voteNumber = votesUp - votesDown
    if item.type == 10 :
        voteNumber = voteCount
    logging.info("qoorate_compute_relevency, end: %s" % item)
    return voteNumber

def unsanitize_safe_htmlentities(sanitized_text):
    """unsanitizes html elements"""
    logging.debug("unsanitizing: %s" % sanitized_text)
    sanitized_text = sanitized_text.encode('ascii', 'xmlcharrefreplace')
    logging.debug("unsanitizing encoded ascii: %s" % sanitized_text)
    sanitized_text = sanitized_text.encode('utf8')
    logging.debug("unsanitizing encoded utf8: %s" % sanitized_text)

    unsanitized_text = sanitized_text.replace("&amp;#", "&#")
    logging.debug(" unsanitized: %s" % unsanitized_text)
    return unsanitized_text
    
class Qoorate(BrooklynCodeBrubeck):
    """Custom application class for Qoorate."""
    def __init__(self, settings_file=None, project_dir=None,
                 *args, **kwargs):
        """ Most of the parameters are dealt with by Brubeck,
            Additional functionality follow call to super
        """
        super(Qoorate, self).__init__(settings_file, project_dir, **kwargs)

        pool_size = 10

        if self.db_conn == None:
            # create our db_conn if we have the settings to
            if settings_file != None:
                mysql_settings = self.get_settings('mysql')
                if mysql_settings != None:
                    logging.debug("creating application db_conn pool")
                    self.db_conn = Queue()
                    for i in range(pool_size): 
                        self.db_conn.put_nowait(create_db_conn(mysql_settings)) 

        self.template_env.filters['sc'] = unsanitize_safe_htmlentities

    def determine_relevency(self, item):
        """schedule an indexing using concurrency"""
        logging.info("qoorate_determine_relevency, start: %s" % item)
        logging.info("qoorate_generate_relevency, star greenlet: %s" % item)
        qoorate_determine_relevency(item)
        logging.info("qoorate_generate_relevency, end: %s" % item)

##
## This are just some general function I couldn't thing of anywhere else to put
##
def getTimeAgo(create_date):
    """get the human readbale text for the comment time"""
    diffTime = time.mktime(datetime.datetime.now().timetuple()) - time.mktime(create_date.timetuple())

    if diffTime < 60:
        seconds = diffTime
        return "%d second ago" % seconds if seconds == 1 else "%d seconds ago" % seconds
    elif diffTime < 3600:
        minutes =  diffTime / 60
        return "%d minute ago" % minutes if minutes == 1 else "%d minutes ago" % minutes
    elif diffTime < 86400:
        hours = diffTime / 3600
        return "%d hour ago" % hours if hours == 1 else "%d hours ago" % hours
    elif diffTime < 604800:
        days = diffTime / 86400
        return "%d day ago"  % days if days == 1 else "%d days ago" % days
    elif diffTime < 2419200:
        weeks = diffTime / 604800
        return "%d week ago"  % weeks if weeks == 1 else "%d weeks ago" % weeks
    else:
        return create_date.strftime('%b %d, %Y %I:%M %p') # Jan 23, 2012 3:45 PM
