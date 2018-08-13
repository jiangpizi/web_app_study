#!/usr/bin/env python
# -*- coding: utf-8 -*-

#from __future__ import unicode_literals
#from __future__ import absolute_import

"""
Database operation module
copy and rewrite by myself
"""
import time,uuid,functools,threading,logging

logger = logging.getLogger(__name__)

class Dict(dict):
    '''
    Simple dict but support access as x.y style.
    >>> d1 = Dict()
    >>> d1['x'] = 100
    >>> d1.x
    100
    >>> d1.y = 200
    >>> d1['y']
    200
    >>> d2 = Dict(a=1, b=2, c=34243)
    >>> d2.c
    34243
    >>> d2['empty']
    Traceback (most recent call last):
        ...
    KeyError: 'empty'
    >>> d2.empty
    Traceback (most recent call last):
        ...
    AttributeError: 'Dict' object has no attribute 'empty'
    >>> d3 = Dict(('a', 'b', 'c'), (1, 2, '3'))
    >>> d3.a
    1
    >>> d3.b
    2
    >>> d3.c
    '3'
    '''
    def __init__(self,names=(),values=(), **kw):
        super(Dict, self).__init__(**kw)
        for k, v in zip(names,values):
            self[k] = v
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError("'Dict' object has no attribute '%s'" % key)
    def __setattr__(self,key,value):
        self[key] = value

def next_id(t=None):
    if t is None:
        t = time.time()
    return '%015d%s000' %(int(t * 1000),uuid.uuid4().hex)

def _profiling(start, sql=''):
    t = time.time() - start
    if t > 0.1:
        logger.warning('[PROFILING] [DB] %s : %s' % (t, sql))
    else:
        logger.info('[PROFILING] [DB] %s : %s' % (t, sql))

class DBError(Exception):
    pass
class MultiColumnsError(Exception):
    pass

class _Engine(object):
    def __init__(self,connect):
        self._connect = connect
    def connect(self):
        return self._connect()

class _LasyConnection(object):
    def __init__(self):
        self.connection = None
    def cursor(self):
        if self.connection is None:
            connection = engine.connect()
            logger.info('open connection <%s>...' % hex(id(connection)))
            self.connection = connection
        return self.connection.cursor()
    def commit(self):
        self.connection.commit()
    def rollback(self):
        self.connection.rollback()
    def cleanup(self):
        if self.connection:
            connection = self.connection
            self.connection = None
            logger.info('close connection <%s>...' % hex(id(connection)))
            connection.close()

class _DbCtx(threading.local):
    '''
    Thread local object that holds connection info.
    '''
    def __init__(self):
        self.connection = None
        self.transactions = 0
    def is_init(self):
        return not self.connection is None

    def init(self):
        logger.info('open lazy connection...')
        self.connection = _LasyConnection()
        self.transactions = 0
    def cleanup(self):
        self.connection.cleanup()
        self.connection = None
    def cursor(self):
        return self.connection.cursor()
_db_ctx = _DbCtx()



#global engine object
engine = None
def create_engine(user,passwd,db,host='127.0.0.1',port=3306,**kw):
    import MySQLdb
    global engine
    if engine is not None:
        raise DBError('Engine is already initialized')
    params = dict(user=user, passwd=passwd, db=db,host=host,port=port)
    #NOTE return func not a connection
    engine =_Engine(lambda: MySQLdb.connect(**params))
    logger.info('Init mysql engine <%s> ok.' % hex(id(engine)))

class _ConnectionCtx(object):
    '''
    _ConnectionCtx object that can open and close connection context. _ConnectionCtx object can be nested and only the most 
    outer connection has effect.
    with connection():
        pass
        with connection():
            pass
    '''

    def __enter__(self):
        global _db_ctx
        self.should_cleanup = False
        if not _db_ctx.is_init():
            _db_ctx.init()
            self.should_cleanup = True
        return self
    def __exit__(self, exctype, excvalue, traceback):
        global _db_ctx
        if self.should_cleanup:
            _db_ctx.cleanup()
def connection():
    '''
    with connection():
        pass
    '''
    
    return _ConnectionCtx()

def with_connection(func):
    '''
    @with_connection
    def foo(*args, **kw):
        fs()
        fs()
        fs()
    '''
    @functools.wraps(func)
    def _wrapper(*args,**kw):
        with _ConnectionCtx():
            return func(*args, **kw)
    return _wrapper

class _TransactionCtx(object):
    '''
    with _TransactionCtx():
        pass
    '''
    def __enter__(self):
        global _db_ctx
        self.should_close_conn = False
        if not _db_ctx.is_init():
            _db_ctx.init()
            self.should_close_conn = True
        _db_ctx.transactions = _db_ctx.transactions + 1
        logger.info('begin transaction...' if _db_ctx.transactions == 1 else 'join current transactions')
        return self
    def __exit__(self,exctype,excvalue,traceback):
        global  _db_ctx
        _db_ctx.transactions = _db_ctx.transactions - 1
        try:
            if _db_ctx.transactions==0:
                if exctype is None:
                    self.commit()
                else:
                    self.rollback()
        finally:
            if self.should_close_conn:
                _db_ctx.cleanup()
    def commit(self):
        global _db_ctx
        logger.info('commit tansaction...')
        try:
            _db_ctx.connection.commit()
            logger.info('commit ok.')
        except:
            logger.warning('commit faild. try rollback...')
            _db_ctx.connection.rollback()
            logger.warning('rollback ok.')
            raise

    def rollback(self):
        global _db_ctx
        logger.warning('rollback transaction...')
        _db_ctx.connection.rollback()
        logger.info('rollback ok.')

def transaction():
    '''
    Create a transaction object so can use with statement:
    with transaction():
        pass
    >>> def update_profile(id, name, rollback):
    ...     u = dict(id=id, name=name, email='%s@test.org' % name, passwd=name, last_modified=time.time())
    ...     insert('user', **u)
    ...     r = update('update user set passwd=? where id=?', name.upper(), id)
    ...     if rollback:
    ...         raise StandardError('will cause rollback...')
    >>> with transaction():
    ...     update_profile(900301, 'Python', False)
    >>> select_one('select * from user where id=?', 900301).name
    u'Python'
    >>> with transaction():
    ...     update_profile(900302, 'Ruby', True)
    Traceback (most recent call last):
      ...
    StandardError: will cause rollback...
    >>> select('select * from user where id=?', 900302)
    []

    '''
    return _TransactioCtx()

def with_transaction(func):
    '''
    A decorator that makes function around transaction.
    >>> @with_transaction
    ... def update_profile(id, name, rollback):
    ...     u = dict(id=id, name=name, email='%s@test.org' % name, passwd=name, last_modified=time.time())
    ...     insert('user', **u)
    ...     r = update('update user set passwd=? where id=?', name.upper(), id)
    ...     if rollback:
    ...         raise StandardError('will cause rollback...')
    >>> update_profile(8080, 'Julia', False)
    >>> select_one('select * from user where id=?', 8080).passwd
    u'JULIA'
    >>> update_profile(9090, 'Robert', True)
    Traceback (most recent call last):
      ...
    StandardError: will cause rollback...
    >>> select('select * from user where id=?', 9090)
    []
    '''
    @functools.wraps(func)
    def _wrapper(*agrs, **kw):
        _start = time.time()
        with _TransactionCtx():
            return func(*args, **kw)
        _profiling(_start)
    return _wrapper
    

def _select(sql, first, *args):
    '''execute select SQL and return unique result or list results.'''
    cursor = None
    sql = sql.replace('?','%s')
    try:
        #cursor = engine.connect().cursor()
        cursor = _db_ctx.connection.cursor()
        cursor.execute(sql,args)
        if cursor.description:
            names = [x[0] for x in cursor.description]
        if first:
            values = cursor.fetchone()
            if not values:
                return None
            return Dict(names,values)
        return [Dict(names,x) for x in cursor] #FIXME
    finally:
        if cursor:
            cursor.close()


@with_connection
def select_one(sql, *args):
    '''
    Execute select SQL and expected one result. 
    If no result found, return None.
    If multiple results found, the first one returned.
    >>> u1 = dict(id=100, name='Alice', email='alice@test.org', passwd='ABC-12345', last_modified=time.time())
    >>> u2 = dict(id=101, name='Sarah', email='sarah@test.org', passwd='ABC-12345', last_modified=time.time())
    >>> insert('user', **u1)
    1L
    >>> insert('user', **u2)
    1L
    >>> u = select_one('select * from user where id=?', 100)
    >>> u.name
    'Alice'
    >>> select_one('select * from user where email=?', 'abc@email.com')
    >>> u2 = select_one('select * from user where passwd=? order by email', 'ABC-12345')
    >>> u2.name
    'Alice'
    '''
    return _select(sql,True,*args)

@with_connection
def select_int(sql, *args):
    '''
    Execute select SQL and expected one int and only one int result. 
    >>> n = update('delete from user')
    >>> u1 = dict(id=96900, name='Ada', email='ada@test.org', passwd='A-12345', last_modified=time.time())
    >>> u2 = dict(id=96901, name='Adam', email='adam@test.org', passwd='A-12345', last_modified=time.time())
    >>> insert('user', **u1)
    1L
    >>> insert('user', **u2)
    1L
    >>> select_int('select count(*) from user')
    2L
    >>> select_int('select count(*) from user where email=?', 'ada@test.org')
    1L
    >>> select_int('select count(*) from user where email=?', 'notexist@test.org')
    0L
    >>> select_int('select id from user where email=?', 'ada@test.org')
    96900L
    >>> select_int('select id, name from user where email=?', 'ada@test.org')
    Traceback (most recent call last):
        ...
    MultiColumnsError: Expect only one column.
    '''
    d = _select(sql,True,*args)
    if len(d) != 1:
        raise MultiColumnsError('Expect only one column.')
    return d.values()[0]

@with_connection
def select(sql, *args):
    '''
    Execute select SQL and return list or empty list if no result.
    >>> u1 = dict(id=200, name='Wall.E', email='wall.e@test.org', passwd='back-to-earth', last_modified=time.time())
    >>> u2 = dict(id=201, name='Eva', email='eva@test.org', passwd='back-to-earth', last_modified=time.time())
    >>> insert('user', **u1)
    1L
    >>> insert('user', **u2)
    1L
    >>> L = select('select * from user where id=?', 900900900)
    >>> L
    []
    >>> L = select('select * from user where id=?', 200)
    >>> L[0].email
    'wall.e@test.org'
    >>> L = select('select * from user where passwd=? order by id desc', 'back-to-earth')
    >>> L[0].name
    'Eva'
    >>> L[1].name
    'Wall.E'
    '''
    return _select(sql,False,*args)

@with_connection
def _update(sql, *args):
    cursor = None
    sql = sql.replace('?','%s')
    logger.info('SQL: %s,ARGS: %s' %(sql,args))
    try:
        #cursor = engine.connect().cursor()
        cursor = _db_ctx.connection.cursor()
        cursor.execute(sql,args)
        r = cursor.rowcount
        if _db_ctx.transactions == 0:
            logger.info('auto commit')
            _db_ctx.connection.commit()
        return r
    finally:
        if cursor:
            cursor.close()

def insert(table, **kw):
    '''
    Execute insert SQL.
    >>> u1 = dict(id=2000, name='Bob', email='bob@test.org', passwd='bobobob', last_modified=time.time())
    >>> insert('user', **u1)
    1L
    >>> u2 = select_one('select * from user where id=?', 2000)
    >>> u2.name
    'Bob'
    >>> insert('user', **u2)
    Traceback (most recent call last):
      ...
    IntegrityError: (1062, "Duplicate entry '2000' for key 'PRIMARY'")
    '''

    cols,args = zip(*kw.iteritems())
    sql = 'insert into `%s` (%s) values (%s)' % (table,','.join(['`%s`'% col for col in cols]),','.join(['?' for i in range(len(cols))]))
    return _update(sql, *args)

def update(sql, *args):
    '''
    Execute update SQL.
    >>> u1 = dict(id=1000, name='Michael', email='michael@test.org', passwd='123456', last_modified=time.time())
    >>> insert('user', **u1)
    1L
    >>> u2 = select_one('select * from user where id=?', 1000)
    >>> u2.email
    'michael@test.org'
    >>> u2.passwd
    '123456'
    >>> update('update user set email=?, passwd=? where id=?', 'michael@example.org', '654321', 1000)
    1L
    >>> u3 = select_one('select * from user where id=?', 1000)
    >>> u3.email
    'michael@example.org'
    >>> u3.passwd
    '654321'
    >>> update('update user set passwd=? where id=?', "***", "123 or id=456")
    0L
    '''

    return _update(sql, *args)
    
if __name__=='__main__':
    LOG_FORMAT = ('%(levelname) -10s %(process)d %(asctime)s %(filename)-10s %(lineno) -5d: %(message)s') 
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    create_engine('web_user', 'web_pwd', 'web_db')
    update('drop table if exists user')
    update('create table user (id int primary key, name text, email text, passwd text, last_modified real)')
    #u1 = dict(id=1000, name='Michael', email='michael@test.org', passwd='123456', last_modified=time.time())
    #insert('user', **u1)
    #import doctest
    #doctest.testmod()
