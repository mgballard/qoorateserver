#!/usr/bin/env python
import logging
from brubeck.request_handling import WebMessageHandler
from handlers.base import QoorateBaseHandler
from brubeck.templating import Jinja2Rendering
from querysets.querysets import CommentItemQueryset, CommentQueryset

##
## Our embed handler class definition
##
class EmbedHandler(Jinja2Rendering, QoorateBaseHandler, WebMessageHandler):
    """this loads the initial comments for a page"""

    def prepare(self):
        logging.debug('EmbedHandler preparing')

        # TODO: Actually get these from the DB
        self._location = 'b4d7305594aafa9493f2b7e14d2ff492'
        self._table = 'q_4044060355'
        
        ## Hook up our Comment Queryset object here
        ## We need this evertime because table name changes
        ## We should probably just chnages the state, not create a new object
        ## TODO: This will change soon as Brubeck handles this decision better
        self.comment_item_queryset = CommentItemQueryset(self.application.get_settings('mysql'), self.table, db_conn = self.application.db_conn)
        self.comment_queryset = CommentQueryset(self.application.get_settings('mysql'), self.table, db_conn = self.application.db_conn)

        # self._url_args only has a list 
        # we need a dictonary with the named parameters
        # so, we reparse the url


    def get(self):
        if self.get_argument('action', None) == 'embed_head':
            logging.debug('embed_head')
            context = {'qoorate_base_uri': self.settings['QOORATE_API_URI']}
            return self.render_template('embed_head.html', **context)
        else:
            logging.debug('embed_content')
            comments = self.comment_item_queryset.load_comments_by_location_and_page(self.table, self.location)
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
                'page': self.page,
                'comments': comments,
                'contribution_text': contribution_text,
                'current_user': self.current_user,
                'related_user': None,
                'thumbnailLargeHash': None,
            }
    
            return self.render_template('embed_content.html', **context)
