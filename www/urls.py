#!/usr/bin/env python
# -*- coding: utf-8 -*-

#from __future__ import unicode_literals
#from __future__ import absolute_import
 
__author__= '601996910@qq.com'

import logging

from transwarp.web import get, view
from models import User,Blog,Comment


@view('blogs.html')
@get('/')
def index():
    blogs = Blog.find_all()
    user = User.find_first('where email=?', 'json@example.com')
    return dict(blogs=blogs, user=user)
