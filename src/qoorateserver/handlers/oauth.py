#!/usr/bin/env python
from brubeck.templating import Jinja2Rendering
from brubeckoauth.handlers import OAuthMixin
from qoorateserver.handlers.base import QoorateMixin
from qoorateserver.querysets.querysets import UserQueryset
from qoorateserver.models.models import User
from qoorateserver.modules.brooklyncodebrubeck.application import lazyprop
import json
import datetime
import logging
##
## Our oauth handler class definition
##
class QoorateOAuthHandler(Jinja2Rendering, OAuthMixin, QoorateMixin):
    """our qoorate specific oAuth handler"""

    ## Define these if you do not want to use redis to persist data thoughout the oauth request"""
    #datahandler = {
    #    "default": (MyOAuthQueries, oAuthModel),
    #    "oauth": (MyUserQueries, UserModel)
    #}

    @lazyprop
    def session_id(self):
        """get our QOOID
           This is our session cookie
        """
        return self.get_argument('QOOID', None)


    def onAuthenticationSuccess(self, oauth_request_model):
        """it is the applications responsibilty to extend this class and
        implement this method. It may be empty if you simply care about authentication.
        The oAuth object used to uathenticate is also accessible with self.oauth
        """
        # first try to get our user based on aouth_id and oauth_provider
        oauth_data = json.loads(oauth_request_model.data)
        initial_request_args = json.loads(oauth_request_model.initial_request_args)
        username = (oauth_data["username"] if "username" in oauth_data and oauth_data["username"] != '' else
            oauth_data["name"] if "name" in oauth_data and oauth_data["name"] != '' else
            oauth_data["fullname"] if "fullname" in oauth_data and oauth_data["fullname"] != '' else None)

        # now set our table since we already failed before
        self.set_table();
        
        if username == None:
            raise Exception("No UserName found in oauth_data 'username','name' or 'fullname' fields.")            

        now = datetime.datetime.now()
        data = {
            "oauth_provider": oauth_request_model.provider_tag,
            "oauth_uid": oauth_data["oauth_uid"],
            "oauth_session_id": oauth_request_model.session_id,
            "username": username,
            "password": None, # deprecated, but not nullable
            "email": oauth_data["email"],
            "thumbnailLarge": oauth_data["thumbnailLarge"],
            "oauth_access_token": oauth_data["oauth_access_token"],
            "oauth_data": json.dumps(oauth_data),
            "createDate": now,
            "changeDate": now,
        }

        logging.debug("User authenticated -> \n %s" % data)
        logging.debug("initial_request_args:%s" % initial_request_args)
        # just in case, clear any login for session
        self.user_queryset.logout_by_qooid(oauth_request_model.session_id)

        result = self.user_queryset.create_one(User(**data))

        # Invalidate any lazy props we may have set based on changing logins
        # Mostly current user and roles
        # this is needed mainly for permission needed by hte template
        self._is_admin = None
        self._current_user = None

        logging.debug( 'User persisted %s -> %s' %(result[0], result[1]) )
        context = {
            'message': "Thank You!",
        }
        self.set_status(200)
        return self.render_template('loggedin.html', **context)
