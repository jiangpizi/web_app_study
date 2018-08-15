#!/usr/bin/env python
# -*- coding: utf-8 -*-

#from __future__ import unicode_literals
#from __future__ import absolute_import
 
__author__= '601996910@qq.com'

import logging

from transwarp.web import get, view
from models import User,Blog,Comment


@view('test_user.html')
@get('/')
def test_user():
    users = User.find_all()
    return dict(users=users)
