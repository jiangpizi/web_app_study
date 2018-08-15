#!/usr/bin/env python
# -*- coding: utf-8 -*-

#from __future__ import unicode_literals
#from __future__ import absolute_import
 
__author__= '601996910@qq.com'

'''
A WSGI application entry.
'''

import logging
import os

from transwarp import db
from transwarp.web import WSGIApplication, Jinja2TemplateEngine

from config import configs

logger = logging.getLogger(__name__)
# init db
db.create_engine(**configs.db)

# init wsgi app
wsgi = WSGIApplication(os.path.dirname(os.path.abspath(__file__)))

template_engine = Jinja2TemplateEngine(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'))

wsgi.template_engine = template_engine

import urls
wsgi.add_module(urls)

if __name__=='__main__':
    LOG_FORMAT = ('%(levelname) -10s %(process)d %(asctime)s %(filename)-10s %(lineno) -5d: %(message)s') 
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    #print os.path.dirname(os.path.abspath(__file__))
    #print os.path.abspath(__file__)
    wsgi.run(port=9000,host='0.0.0.0')

