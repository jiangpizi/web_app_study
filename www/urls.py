#!/usr/bin/env python
# -*- coding: utf-8 -*-

#from __future__ import unicode_literals
#from __future__ import absolute_import
 
__author__= '601996910@qq.com'

import os, re, time, base64, hashlib, logging

from transwarp.web import get, view

from transwarp.web import get, post, ctx, view, interceptor, seeother, notfound
from apis import api, APIError, APIValueError, APIPermissionError, APIResourceNotFoundError
from models import User,Blog,Comment

logger = logging.getLogger(__name__)
@view('blogs.html')
@get('/')
def index():
    blogs = Blog.find_all()
    user = User.find_first('where email=?', 'json@example.com')
    return dict(blogs=blogs, user=user)


@api
@get('/api/users')
def api_get_users():
    users = User.find_by('order by created_at desc')
    logger.info('user:%s' %users)
    for u in users:
        u.password = '*******'
    return dict(users=users)

