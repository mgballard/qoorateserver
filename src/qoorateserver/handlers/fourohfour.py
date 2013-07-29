#!/usr/bin/env python
import sys
import logging
from brubeck.templating import Jinja2Rendering
from brubeck.request_handling import WebMessageHandler



##
## Our about handler class definitions
##
class FourOhFourHandler(Jinja2Rendering, WebMessageHandler):
    """Handles our unknown unrouted page request
    """

    def get(self):
        self.set_status(404)
        context = {
            'title': 'Not Found | Salesbus',
            'tag': 'fourohfour',
        }
        return self.render_template('fourohfour.html', **context)

    def post(self):
        self.get()

    def put(self):
        self.get()

    def delete(self):
        self.get()

    def options(self):
        self.get()
