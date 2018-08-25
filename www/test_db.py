#!/usr/bin/env python
# -*- coding: utf-8 -*-

#from __future__ import unicode_literals
#from __future__ import absolute_import
 
__author__= '601996910@qq.com'

import sys
import hashlib

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
u = User(name='admin',admin=1, email='admin123@qq.com', image='about:blank')
u1 = User(name='jsong', email='json@example.com', image='about:blank')
u.insert()
u1.insert()

b = Blog(id=1,user_id='00153431774194282fc64ed618a485e83a2f227bce4da45000', user_name='jsong', name='test blog', summary='test blog:this is a blog about test',context="测试博客")

b2 = Blog(id=2,user_id='00153431774194282fc64ed618a485e83a2f227bce4da45000', user_name='jsong', name='test blog2', summary='test blog:this is a blog about test',context="测试博客2")
b.insert()
b2.insert()
