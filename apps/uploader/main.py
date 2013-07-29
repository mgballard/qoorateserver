#!/usr/bin/env python
from brubeck.auth import authenticated
from brubeckservice.connections import (
    ServiceConnection,
    register_service,
)
from brubeck.request_handling import Brubeck
from gevent import Greenlet
from gevent.event import Event
import sys
import logging
import httplib
import imp
import os
import time
import random
import datetime
from brubeckuploader.handlers import (
    UploadHandler,
)
from brubeckservice.base import (
    lazyprop,
    BrooklynCodeBrubeck,
)

class Uploader(BrooklynCodeBrubeck):
    """Custom application class for SalesBus."""
    def __init__(self, *args, **kwargs):
        """ Most of the parameters are dealt with by Brubeck,
            Additional functionality follow call to super
        """
        super(Uploader, self).__init__(**kwargs)

##
## runtime configuration
##

## Turn on some debugging
logging.basicConfig(level=logging.DEBUG)
httplib.HTTPConnection.debuglevel = 1

#project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
project_dir = '.'
logging.info("Using project directory: " + project_dir)

config = {
    'project_dir': project_dir,
    'msg_conn': ServiceConnection('ipc://run/uploader/brubeck_svc', 'ipc://run/uploader/brubeck_svc_response', '137b789e-b7eb-475a-8d5a-b16ab544yurp'),
    'settings_file': project_dir + '/conf/uploader/settings.py',
    'handler_tuples': [ ## Set up our routes
        (r'^/brubeck/uploader', UploadHandler),
    ],
    'log_level': logging.DEBUG,
}

## other settings should be put in the file specified by 'settings_file'

##
## get us started!
##


app = Uploader(**config)
app_settings = app.get_settings('app')

register_service(app, 
    app_settings["SERVICE_INFO"]["SERVICE_REGISTRATION_PASSPHRASE"],
    app_settings["SERVICE_INFO"]["SERVICE_ID"],
    app_settings["SERVICE_INFO"]["SERVICE_REGISTRATION_ADDR"],
    app_settings["SERVICE_INFO"]["SERVICE_PASSPHRASE"], 
    app_settings["SERVICE_INFO"]["SERVICE_ADDR"],
    app_settings["SERVICE_INFO"]["SERVICE_RESPONSE_ADDR"],
    app_settings["SERVICE_INFO"].get("SERVICE_HEARTBEAT_ADDR", None),
    5,
    app.msg_conn.sender_id)

## start our server to handle requests
if __name__ == "__main__":
    app.run()
