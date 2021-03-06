#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging

from brubeck.request_handling import WebMessageHandler, JSONMessageHandler
from brubeck.templating import Jinja2Rendering
from qoorateserver.handlers.base import QoorateMixin
from qoorateserver.querysets.querysets import CommentItemQueryset, CommentQueryset, QoorateQueryset, KeypairQueryset

##
## Our embed mixin class definition
##
class EmbedMixin(object):
    """this loads the initial comments for a page"""

    def get_head_resources(self, qoorate_base_uri):
        return [
            ( "link", (
                    ('href', "%s/css/%s/embed-base.css" % (qoorate_base_uri, self.preferences['THEME'])),
                    ('media', "all"),
                    ('rel', "stylesheet"),
                    ('type', "text/css"),
                )
            ),
            ( "link", (
                    ('href', "%s/css/%s/embed-layout.css" % (qoorate_base_uri, self.preferences['THEME'])),
                    ('media', "all"),
                    ('rel', "stylesheet"),
                    ('type', "text/css"),
                )
            ),
            ( "link", (
                    ('href', "%s/css/%s/embed-decor.css" % (qoorate_base_uri, self.preferences['THEME'])),
                    ('media', "all"),
                    ('rel', "stylesheet"),
                    ('type', "text/css"),
                )
            ),
            ( "link", (
                    ('href', "%s/css/%s/embed-fonts.css" % (qoorate_base_uri, self.preferences['THEME'])),
                    ('media', "all"),
                    ('rel', "stylesheet"),
                    ('type', "text/css"),
                )
            ),
            ( "link", (
                    ('href', "%s/css/%s/embed-mobile.css" % (qoorate_base_uri, self.preferences['THEME'])),
                    ('media', "all"),
                    ('rel', "stylesheet"),
                    ('type', "text/css"),
                )
            ),
            ( "link", (
                    ('href', "%s/css/%s/embed.css" % (qoorate_base_uri, self.preferences['THEME'])),
                    ('media', "all"),
                    ('rel', "stylesheet"),
                    ('type', "text/css"),
                )
            ),
            
            # This is inline now
            #( "jsconf", (
            #        ('src', "%s/js/embed.conf.js" % qoorate_base_uri),
            #        ('type', "text/javascript"),
            #    )
            #),
            ( "script", (
                    ('src', "%s/js/jquery-1.7.2.min.js" % qoorate_base_uri),
                    ('type', "text/javascript"),
                )
            ),
            ( "script", (
                    ('src', "%s/js/embed.js" % qoorate_base_uri),
                    ('type', "text/javascript"),
                )
            ),
            ( "script", (
                    ('src', "%s/js/fileuploader.js" % qoorate_base_uri),
                    ('type', "text/javascript"),
                )
            ),
            ( "script", (
                    ('src', "%s/js/jquery.cookie.js" % qoorate_base_uri),
                    ('type', "text/javascript"),
                )
            ),
            ( "script", (
                    ('src', "%s/js/jquery-ui-1.8.22.custom.min.js" % qoorate_base_uri),
                    ('type', "text/javascript"),
                )
            ),
        ]

    def prepare(self):
        logging.debug('EmbedHandlerBase preparing')
        self.keypair_queryset = KeypairQueryset(self.application.get_settings('mysql'), self.application.db_conn)
        if not self.keypair_queryset.authenticate(self.q_api_key, self.q_api_secret):
            logging.debug('embed_head key secret invalid')
            return self.render_template('embed_head_error.html', **context)
        ## Hook up our Comment Queryset object here
        ## We need this evertime because table name changes
        ## We should probably just chnages the state, not create a new object
        ## TODO: This will change soon as Brubeck handles this decision better
        table = self.table 
        logging.debug('table: %s' % table)
        if table == None:
            logging.debug('QoorateQueryset preparing')
            logging.debug("q_short_name: %s" % self.q_short_name)
            self.qoorate_queryset = QoorateQueryset(self.application.get_settings('mysql'), self.application.db_conn)
            self.set_table()
            table = self.qoorate.refTable
            #self._table = table
            logging.debug('new table: %s' % self.table)
        self.comment_item_queryset = CommentItemQueryset(self.application.get_settings('mysql'), self.application.db_conn, table)
        self.comment_queryset = CommentQueryset(self.application.get_settings('mysql'), self.application.db_conn, table)
        # self._url_args only has a list 
        # we need a dictonary with the named parameters
        # so, we reparse the url

    def get_content_context(self):
        logging.debug("get_content_context")
        #self.set_table()
        logging.debug("table: %s" % self.table)
        comments = self.comment_item_queryset.load_comments_by_table_and_location(self.table, 
            self.location, 
            parentOffset = self.moreIndex, 
            parentCount=self.settings['PARENT_PAGE_SIZE'], 
            childCount=self.settings['CHILD_PAGE_SIZE'])
        contributions = self.comment_queryset.get_count_by_table_and_location(self.table, self.location)
        contribution_text = "Be the First to Contribute"
        if contributions == 1:
            contribution_text = "%d Contribution" % contributions
        elif contributions > 1:
            contribution_text = "%d Contributions" % contributions
        parent_tag = 'p' + self.table[1:]
        context = {
            'app': self.application.get_settings('app'),
            'location': self.location,
            'qoorate_url': self.qoorate_url,
            'parent_tag': parent_tag,
            'q_short_name': self.q_short_name,
            'comments': comments,
            'contribution_text': contribution_text,
            'current_user': self.current_user,
            'related_user': None,
            'thumbnailLargeHash': None,
            'parentCount': self.parentCount,
            'childCount': self.childCount,
            'moreIndex': self.moreIndex,
            'has_more_contributions': self.has_more_contributions(comments),
            'confjs': self.preferences['EMBED_CONF_JS'],
            'theme': self.preferences['THEME'],
            'is_admin': self.is_admin,
        }
        return context;

##
## Our embed handler class definition
##
class EmbedHandler(Jinja2Rendering, EmbedMixin, QoorateMixin):
    """this loads the initial comments for a page"""

    def get(self):
        try:
            logging.debug('get EmbedHandler')
            action = self.get_argument('action', None)
            logging.debug("action: %s " % action)
            if self.qoorate:
                logging.debug("qoorate preferences: %s" % self.qoorate.preferences)
                logging.debug("preferences EMBED_CONF_JS: %s" % self.preferences['EMBED_CONF_JS'])
            else:
                logging.debug("qoorate missing")
            
            if action == 'embed_head':
                logging.debug('embed_head called')
                head_resources = self.get_head_resources(self.settings['QOORATE_API_URI'])
                def build_link(resource):
                    return "<link " + " ".join(map((lambda a: "%s='%s'" % (a[0],a[1])),resource)) + " />\r\n"
                def build_script(resource):
                    return "<script " + " ".join(map((lambda a: "%s='%s'" % (a[0],a[1])),resource)) + "></script>\r\n"
                content = ''
                for resource in head_resources:
                    if resource[0]=='link':
                        content += build_link(resource[1])
                    if resource[0]=='script' or resource[0]=='jsconf':
                        content += build_script(resource[1])
                self.set_status('200')
                self.set_body(content)
                return self.render()
            else:
                logging.debug("embed_content called (key,secret): (%s,%s)" % (self.q_api_key, self.q_api_secret))
                if not self.keypair_queryset.authenticate(self.q_api_key, self.q_api_secret) == True:
                    logging.debug('embed_content key secret invalid')
                    return self.render_template('errors.html', **{'error_code': 0})            
                context = self.get_content_context()
                return self.render_template(self.preferences['THEME'] + '/embed_content.html', **context)
        except Exception as e:
            return self.render_error(-1)

##
## Our JSON embed handler class definition
## When content isn't enough, use JSON
##
class EmbedHandlerJSON(JSONMessageHandler, EmbedMixin, QoorateMixin):
    """this loads the initial comments for a page"""

    def get(self):
        try:
            logging.debug('get EmbedHandlerJSON')
            action = self.get_argument('action', None)
            logging.debug("action: %s " % action)
            logging.debug("qoorate preferences: %s" % self.qoorate.preferences)
            head_resources = self.get_head_resources(self.settings['QOORATE_API_URI'])
            self.add_to_payload('head', head_resources)
            context = self.get_content_context()
            content = self.render_partial(self.preferences['THEME'] + '/embed_content.html', **context)
            self.set_status(200)
            self.add_to_payload('content', content)
            return self.render()
        except Exception as e:
            return self.render_error(-1)
