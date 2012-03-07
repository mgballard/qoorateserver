#!/usr/bin/env python
import logging
from brubeck.request_handling import WebMessageHandler, JSONMessageHandler
from handlers.base import QoorateBaseHandler
from brubeck.templating import Jinja2Rendering
from querysets.querysets import CommentItemQueryset, CommentQueryset, QoorateQueryset, KeyPairQueryset

def get_head_resources(qoorate_base_uri):
    return [
        ( "link", (
                ('href', "%s/css/embed-base.css" % qoorate_base_uri),
                ('media', "all"),
                ('rel', "stylesheet"),
                ('type', "text/css"),
            )
        ),
    
        ( "link", (
                ('href', "%s/css/embed-layout.css" % qoorate_base_uri),
                ('media', "all"),
                ('rel', "stylesheet"),
                ('type', "text/css"),
            )
        ),
    
        ( "link", (
                ('href', "%s/css/embed-decor.css" % qoorate_base_uri),
                ('media', "all"),
                ('rel', "stylesheet"),
                ('type', "text/css"),
            )
        ),
    
        ( "link", (
                ('href', "%s/css/embed-fonts.css" % qoorate_base_uri),
                ('media', "all"),
                ('rel', "stylesheet"),
                ('type', "text/css"),
            )
        ),
    
        ( "link", (
                ('href', "%s/css/embed-mobile.css" % qoorate_base_uri),
                ('media', "all"),
                ('rel', "stylesheet"),
                ('type', "text/css"),
            )
        ),
    
        ( "jsconf", (
                ('src', "%s/js/embed.conf.js" % qoorate_base_uri),
                ('type', "text/javascript"),
            )
        ),
    
        ( "script", (
                ('src', "%s/js/jquery-1.4.4.min.js" % qoorate_base_uri),
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
    ]

##
## Our embed handler class definition
##
class EmbedBaseHandler(QoorateBaseHandler):
    """this loads the initial comments for a page"""

    def prepare(self):
        logging.debug('EmbedHandlerBase preparing')
        
        self.keypair_queryset = KeyPairQueryset(self.application.get_settings('mysql'), self.application.db_conn)
        if not self.keypair_queryset.authenticate(self.q_api_key, self.q_api_secret):
            logging.debug('embed_head key secret invalid')
            return self.render_template('embed_head_error.html', **context)

        ## Hook up our Comment Queryset object here
        ## We need this evertime because table name changes
        ## We should probably just chnages the state, not create a new object
        ## TODO: This will change soon as Brubeck handles this decision better
        self.qoorate_queryset = QoorateQueryset(self.application.get_settings('mysql'), self.application.db_conn)
        qoorate = self.qoorate_queryset.get_by_short_title(self.q_short_name)
        self._table = qoorate.refTable

        self.comment_item_queryset = CommentItemQueryset(self.application.get_settings('mysql'), self.table, self.application.db_conn)
        self.comment_queryset = CommentQueryset(self.application.get_settings('mysql'), self.table, self.application.db_conn)

        # self._url_args only has a list 
        # we need a dictonary with the named parameters
        # so, we reparse the url

    def get_content_context(self):
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
            'table': self.table,
            'comments': comments,
            'contribution_text': contribution_text,
            'current_user': self.current_user,
            'related_user': None,
            'thumbnailLargeHash': None,
            'parentCount': self.parentCount,
            'childCount': self.childCount,
            'moreIndex': self.moreIndex,
            'has_more_contributions': self.has_more_contributions(comments),
                
        }
        
        return context;
        
##
## Our embed handler class definition
##
class EmbedHandler(Jinja2Rendering, EmbedBaseHandler, WebMessageHandler):
    """this loads the initial comments for a page"""

    def get(self):
        action = self.get_argument('action', None)
        logging.debug(action)
        
        if action == 'embed_head':
     
            head_resources = get_head_resources(self.settings['QOORATE_API_URI'])

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
            logging.debug('embed_content')

            if not self.keypair_queryset.authenticate(self.q_api_key, self.q_api_secret):
                logging.debug('embed_content key secret invalid')
                return self.render_template('embed_content_error.html', **context)            

            context = self.get_content_context()

            return self.render_template('embed_content.html', **context)


##
## Our JSON embed handler class definition
## When content isn't enough, use JSON
##
class EmbedHandlerJSON(EmbedBaseHandler, JSONMessageHandler):
    """this loads the initial comments for a page"""

    def get(self):

        head_resources = get_head_resources(self.settings['QOORATE_API_URI'])
        self.add_to_payload('head', head_resources)

        context = self.get_content_context()

        content = self.render_partial('embed_content.html', **context)

        self.set_status(200)
        self.add_to_payload('content', content)

        return self.render()

