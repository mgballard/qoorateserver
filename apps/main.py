#!/usr/bin/env python
from brubeck.auth import authenticated
from brubeck.request_handling import JSONMessageHandler, cookie_encode, cookie_decode
from qoorate import Qoorate
from brubeck.templating import load_jinja2_env, Jinja2Rendering
from dictshield import fields
from dictshield.document import Document, EmbeddedDocument
from dictshield.fields import ShieldException
from gevent import Greenlet
from gevent.event import Event
from urllib import unquote, quote
import sys
import logging
import httplib
import os
import time
import random
import datetime
import qoorate

from handlers.feed import FeedHandler
from handlers.embed import EmbedHandler
from modules.uploader.handlers import TemporaryImageUploadHandler, TemporaryImageViewHandler
from handlers.oauth import QoorateOAuthHandler


##
## runtime configuration
##

## Turn on some debugging
logging.basicConfig(level=logging.DEBUG)
httplib.HTTPConnection.debuglevel = 1

project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
logging.info("Using project directory: " + project_dir)

config = {
    'project_dir': project_dir,
    'mongrel2_pair': ('ipc://run/mongrel2_send', 'ipc://run/mongrel2_recv'),
    'handler_tuples': [ ## Set up our routes
        (r'^/q/feed', FeedHandler),
        (r'^/q/embed', EmbedHandler),
        (r'^/q/uploader/images/(?P<file_name>.+)$', TemporaryImageViewHandler),
        (r'^/q/uploader', TemporaryImageUploadHandler),
        (r'^/q/oauth/(?P<provider>.+)/(?P<action>.+)$', QoorateOAuthHandler),
    ],
    'cookie_secret': '_1sRe%%66a^O9s$4c6ld!@_F%&9AlH)-6OO1!',
    'template_loader': load_jinja2_env( project_dir + '/templates'),
    'settings_file': project_dir + '/conf/development.py',
    'log_level': logging.DEBUG,
}

## other settings should be put in the file specified by 'settings_file'

##
## get us started!
##


app = Qoorate(**config)
## start our server to handle requests
if __name__ == "__main__":
    app.run()
