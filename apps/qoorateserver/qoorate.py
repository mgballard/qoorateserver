#!/usr/bin/env python
from qoorateserver.modules.brooklyncodebrubeck.application import BrooklynCodeBrubeck
from brubeckmysql.base import create_db_conn
import time
import datetime
import logging
from gevent.queue import Queue

class Qoorate(BrooklynCodeBrubeck):

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
