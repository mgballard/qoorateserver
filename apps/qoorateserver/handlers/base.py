#!/usr/bin/env python
import logging
from brubeck.request_handling import MessageHandler
from qoorateserver.querysets.querysets import UserQueryset
from qoorateserver.modules.brooklyncodebrubeck.application import lazyprop

##
## Our Qoorate base handler definition
##

class QoorateBaseHandler(MessageHandler):
    """our base handler
    we should never route to this"""
    ##
    ## Some functionality maybe Brubeck should have?
    ##
    def render_partial(self, template_file, **context):
        """Renders an HTML snippet from a jinja template
        """
        jinja_env = self.application.template_env
        template = jinja_env.get_template(template_file)
        return template.render(**context or {})

    ##
    ## A bunch of lazy properties we can use in our handlers
    ##

    @lazyprop
    def current_user(self):
        """this is required for Brubeck authentication decorater to work"""
        return self.user_queryset.get_by_qooid(self.qooid)

    ##
    ## These are our cookies
    ##
    ## IMPORTANT: It is the clients responsibility to set cookies
    ## Generally, headers are sent by the time the server get's involved.

    @lazyprop
    def qooid(self):
        """get our QOOTID cookie
        this is our session cookie
        we mainly just use this for our authentication
        IMPORTANT: This is the clients responsibility to se this and forward olong with the proxied request
        """
        return self.get_cookie('QOOID', None)

    @lazyprop
    def qootid(self):
        """get our QOOTID cookie
        this is our longer lasting tracking cookie
        we mainly just use this for anonymous users
        """
        return self.get_cookie('QOOTID', None)

    ##
    ## These are the typical query parameters from the PHP proxy
    ##

    @lazyprop
    def q_api_key(self):
        """this is required for Brubeck authentication decorater to work"""
        return self.get_argument('q_api_key', None)

    @lazyprop
    def q_api_secret(self):
        """this is required for Brubeck authentication decorater to work"""
        return self.get_argument('q_api_secret', None)

    @lazyprop
    def q_short_name(self):
        """this is required for Brubeck authentication decorater to work"""
        return self.get_argument('q_short_name', None)

    @lazyprop
    def table(self):
        """defines the table comments are stored in
        TODO: this is bad ... we should get everything based on the api_key and api_secret
        """
        return self.get_argument('table', None)

    @lazyprop
    def location(self):
        """defines the page/location the comments are for"""
        return self.get_argument('location', None)

    @lazyprop
    def referer(self):
        """defines the referrer of a POST request
        TODO: probably not such a good name, though that is what it is
        """
        return self.get_argument('referer', None)

    @lazyprop
    def target(self):
        """defines the target of a POST request"""
        return self.get_argument('target', None)

    @lazyprop
    def action(self):
        """defines the action on a POST request"""
        return self.get_argument('action', None)

    @lazyprop
    def sort(self):
        """used to define the sort order for comments"""
        return self.get_argument('sort', None)

    @lazyprop
    def settings(self):
        """used to define the sort order for comments"""
        return self.application.get_settings('app')

    @lazyprop
    def user_queryset(self):
        """used to initialize and cache the user queryset"""
        return UserQueryset(self.application.get_settings('mysql'), self.application.db_conn)

    @lazyprop
    def qoorate_url(self):
        """used to initialize and cache the user queryset"""
        return self.settings['QOORATE_URI']

    @lazyprop
    def parentId(self):
        """ xxx argument
        """
        return int(self.get_argument('parentId', 0))
        
    @lazyprop
    def moreIndex(self):
        """used to initialize and cache the user queryset"""
        return int(self.get_argument('moreIndex', 1))
        

    @lazyprop
    def childCount(self):
        """get the number of children for paging"""
        if self.action == 'getMoreChildren':
            return 0
        else:
            return self.settings['CHILD_PAGE_SIZE']

    @lazyprop
    def parentCount(self):
            return self.settings['PARENT_PAGE_SIZE']

    def has_more_contributions(self, comments):
        """inspect a list of comment and let us know if we have more
        The comments list will have one more than requested to let us
        know we need a more link.
        """
        if self.parentId > 0 and self.childCount == 0:
            return False;
            
        parent_count = 0;

        for comment in comments:
            if comment.parentId == 0:
                parent_count += 1
        
        return parent_count > self.moreIndex + self.parentCount - 1