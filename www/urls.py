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

from config import configs

logger = logging.getLogger(__name__)

_COOKIE_NAME = 'awesession'
_COOKIE_KEY = configs.session.secret

def make_signed_cookie(id,password,max_age):
    # build cookie string by: id-expires-md5
    expires = str(int(time.time() + (max_age or 86400)))
    L = [id, expires, hashlib.md5('%s-%s-%s-%s' % (id, password, expires, _COOKIE_KEY)).hexdigest()]
    return '-'.join(L)

def parse_signed_cookie(cookie_str):
    #try:
    cookie = ctx.request.cookies.get(_COOKIE_NAME)
    L = cookie_str.split('-')
    if len(L) != 3:
        return None
    id,expires,md5 = L
    if int(expires) < time.time():
        return None
    user = User.get(id)
    if user is None:
        return None
    if md5 != hashlib.md5('%s-%s-%s-%s' % (id, user.password, expires, _COOKIE_KEY)).hexdigest():
        return None
    return user
    #except:
    #    logger.info('error------------')
    #    return None

def check_admin():
    user = ctx.request.user
    if user and user.admin:
        return
    raise APIPermissionError('No permission.')

@interceptor('/')
def user_interceptor(next):
    logger.info('try to bind user from session cookie...')
    user = None
    cookie = ctx.request.cookies.get(_COOKIE_NAME)
    if cookie:
        logger.info('parse session cookie... %s' %cookie)
        user = parse_signed_cookie(cookie)
        if user:
            logger.info('bind user <%s> to session...' % user.email)
        else:
            logger.info('error bind user <%s> to session...' % user)
    ctx.request.user = user

    return next()

@interceptor('/manage/')
def manage_interceptor(next):
    user = ctx.request.user
    if user and user.admin:
        return next()
    raise seeother('/signin')

@view('blogs.html')
@get('/')
def index():
    blogs = Blog.find_all()
    #user = User.find_first('where email=?', 'json@example.com')
    return dict(blogs=blogs, user=ctx.request.user)

@view('signin.html')
@get('/signin')
def signin():
    return dict()

@get('/signout')
def signout():
    ctx.response.delete_cookie(_COOKIE_NAME)
    logger.info('signout to other')
    raise seeother('/')
@api
@post('/api/authenticate')
def authenticate():
    i = ctx.request.input(remember='')
    email = i.email.strip().lower()
    password = i.password
    remember = i.remember
    user = User.find_first('where email=?', email)
    if user is None:
        raise APIError('auth:failed', 'email', 'Invalid email.')
    elif user.password != password:
        raise APIError('auth:failed', 'password', 'Invalid password.')
    # make session cookie:
    max_age = 604800 if remember=='true' else None
    cookie = make_signed_cookie(user.id, user.password, max_age)
    ctx.response.set_cookie(_COOKIE_NAME, cookie, max_age=max_age)
    user.password = '******'
    logger.info('user authenticate %s' % user.name)
    return user

_RE_EMAIL  = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_MD5 = re.compile(r'^[0-9a-f]{32}$')

@api
@post('/api/users')
def register_user():
    i = ctx.request.input(name='', email='', password='')
    name = i.name.strip()
    email = i.email.strip().lower()
    password = i.password
    if not name:
        raise APIValueError('name')
    if not email or not _RE_EMAIL.match(email):
        raise APIValueError('email')
    if not password or not _RE_MD5.match(password):
        raise APIValueError('password')
    user = User.find_first('where email=?', email)
    if user:
        raise APIError('register:failed', 'email', 'Email is already in use.')
    user = User(name=name, email=email, password=password, image='http://www.gravatar.com/avatar/%s?d=mm&s=120' % hashlib.md5(email).hexdigest())
    user.insert()
    # make session cookie:
    cookie = make_signed_cookie(user.id, user.password, None)
    ctx.response.set_cookie(_COOKIE_NAME, cookie)
    return user

@view('register.html')
@get('/register')
def register():
    return dict()

@view('manage_blog_edit.html')
@get('/manage/blogs/create')
def manage_blogs_create():
    return dict(id=None, action='/api/blogs', redirect='/manage/blogs', user=ctx.request.user)

@api
@post('/api/blogs')
def api_create_blog():
    check_admin()
    i = ctx.request.input(name='', summary='', content='')
    name = i.name.strip()
    summary = i.summary.strip()
    content = i.content.strip()
    if not name:
        raise APIValueError('name', 'name cannot be empty.')
    if not summary:
        raise APIValueError('summary', 'summary cannot be empty.')
    if not content:
        raise APIValueError('content', 'content cannot be empty.')
    user = ctx.request.user
    blog = Blog(user_id=user.id, user_name=user.name, name=name, summary=summary, content=content)
    blog.insert()
    return blog

@api
@get('/api/users')
def api_get_users():
    users = User.find_by('order by created_at desc')
    logger.info('user:%s' %users)
    for u in users:
        u.password = '*******'
    return dict(users=users)

