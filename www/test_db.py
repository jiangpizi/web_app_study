#!/usr/bin/env python
# -*- coding: utf-8 -*-

#from __future__ import unicode_literals
#from __future__ import absolute_import
 
__author__= '601996910@qq.com'

import sys

from models import User,Blog,Comment

from transwarp import db
from transwarp.orm import Model

import logging

logger = logging.getLogger(__name__)
logger = logging.getLogger(__name__)
LOG_FORMAT = ('%(levelname) -10s %(process)d %(asctime)s %(filename)-10s %(lineno) -5d: %(message)s') 
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

db.create_engine('web_user', 'web_pwd', 'web_db')
Model.create_all()
u = User(name='Test', email='test@example.com', password='1234567890', image='about:blank')
u1 = User(name='jsong', email='json@example.com', password='1234567890', image='about:blank')
u.insert()
u1.insert()
print 'new user id:', u.id

u1 = User.find_first('where email=?', 'test@example.com')
print 'find user\'s name:', u1.name

u1.delete()

u2 = User.find_first('where email=?', 'test@example.com')
print 'find user:', u2


