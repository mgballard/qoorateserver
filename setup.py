#!/usr/bin/env python
 
from distutils.core import setup
 
setup(name='qoorateserver',
      version='0.0.9',
      description='Qoorate Brubeck server',
      author='Seth Murphy',
      author_email='seth@brooklyncode.com',
      url='http://github.com/qoorate/QoorateServer',
      packages=['apps.qoorateserver','apps.qoorateserver.handlers','apps.qoorateserver.querysets','apps.qoorateserver.models','apps.qoorateserver.modules'])
        