#!/usr/bin/env python
# Copyright 2012 Brooklyn Code Incorporated. See LICENSE.md for usage
# the license can also be found at http://brooklyncode.com/opensource/LICENSE.md
from brubeck.request_handling import Brubeck
import logging
import imp

def lazyprop(method):
    """ A nifty wrapper to only load preoperties when accessed
    uses the lazyProperty pattern from: 
    http://j2labs.tumblr.com/post/17669120847/lazy-properties-a-nifty-decorator
    inspired by  a stack overflow question:
    http://stackoverflow.com/questions/3012421/python-lazy-property-decorator
    This is to replace initializing common variable from cookies, query string, etc .. 
    that would be in the prepare() method.
    THIS SHOULD BE IN BRUBECK CORE
    """
    attr_name = '_' + method.__name__
    @property
    def _lazyprop(self):
        if not hasattr(self, attr_name):
            attr = method(self)
            setattr(self, attr_name, method(self))
            # filter out our javascript nulls
            if getattr(self, attr_name) == 'undefined':
                setattr(self, attr_name, None)
        return getattr(self, attr_name)
    return _lazyprop    

class BrooklynCodeBrubeck(Brubeck):
    """our main application, extending Brubeck
    This is not application specific, 
    but general stuff that maybe shoud be in Brubeck someday"""

    def __init__(self, settings_file, project_dir,
                 *args, **kwargs):
        """ Most of the parameters are dealt with by Brubeck,
            Additional functionality follow call to super
        """
        Brubeck.__init__(self, **kwargs)

        if project_dir == None:
            raise Exception('missing project_dir from config')
        else:
            self.project_dir = project_dir
        """load our settings"""
        if settings_file != None:
            self.settings = self.get_settings_from_file(settings_file)
        else:
            self.settings = {}


    def get_settings(self, setting_name, file_name=None):
        """ This is an attempt at providing a possible 
        external location for settings to overide any 
        settings in the settings file that was passed
        to the application during initialization.
        """

        try:
            if hasattr(self, 'settings'):
                if hasattr(self.settings, setting_name):
                    # we had our settings loaded already
                    return getattr(self.settings, setting_name)

            if file_name == None:
                # create default file name
                file_name = self.project_dir + '/conf/' + setting_name + '.py'

            # try to load our file
            settings = self.get_settings_from_file(file_name)

            if hasattr(settings, setting_name):
                # load us in self.settings
                # so we don't need to read from file  next time
                self.settings.append({setting_name:settings[settings_name]})
                return settings[settings_name]

            raise Exception("Unable to load settings from file %s: %s " % (file_name, setting_name))

        except:
            # raise our error
            raise


    def get_settings_from_file(self, file_name):

        settings = None
        logging.debug ('loading settings from %s' % file_name)
        
        try:
            settings = imp.load_source('settings', file_name)
        except:
            raise #Exception("unknown error getting file: " + file_name)

        return settings
