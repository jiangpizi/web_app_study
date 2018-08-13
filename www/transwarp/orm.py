#!/usr/bin/env python
# -*- coding: utf-8 -*-

#from __future__ import unicode_literals
#from __future__ import absolute_import
 
__author__= '601996910@qq.com'

import time
import logging

import db

logger = logging.getLogger(__name__)

class TableModuleError(Exception):
    pass

class Field(object):
    _count = 0

    def __init__(self,**kw):
        self.name = kw.get('name',None)
        self._default = kw.get('default', None)
        self.primary_key = kw.get('primary_key', False)
        self.nullable = kw.get('nullable', False)
        self.updatable = kw.get('updatable', True)
        self.insertable = kw.get('insertable', True)
        self.ddl = kw.get('ddl', '')
        self._order = Field._count
        Field._count = Field._count + 1

    @property
    def default(self):
        d = self._default
        return d() if callable(d) else d

    def __str__(self):
        s = ['<%s:%s,%s,default(%s),' %(self.__class__.__name__, self.name,self.ddl,self._default)]
        self.nullable and s.append('N')
        self.updatable and s.append('U')
        self.insertable and s.append('I')
        s.append('>')
        return ''.join(s)

class StringField(Field):
    def __init__(self, **kw):
        if not 'default' in kw:
            kw['default'] = 0
        if not 'ddl' in kw:
            kw['ddl'] = 'varchar(255)'
        super(StringField,self).__init__(**kw)

class IntegerField(Field):
    def __init__(self, **kw):
        if not 'default' in kw:
            kw['default'] = 0
        if not 'ddl' in kw:
            kw['ddl'] = 'bigint'
        super(IntegerField,self).__init__(**kw)

class FloatField(Field):
    def __init__(self, **kw):
        if not 'default' in kw:
            kw['default'] = 0
        if not 'ddl' in kw:
            kw['ddl'] = 'real'
        super(FloatField,self).__init__(**kw)

class BooleanField(Field):
    def __init__(self, **kw):
        if not 'default' in kw:
            kw['default'] = 0
        if not 'ddl' in kw:
            kw['ddl'] = 'bool'
        super(BooleanField,self).__init__(**kw)

class TextField(Field):
    def __init__(self, **kw):
        if not 'default' in kw:
            kw['default'] = 0
        if not 'ddl' in kw:
            kw['ddl'] = 'text'
        super(TextField,self).__init__(**kw)

class BlodField(Field):
    def __init__(self, **kw):
        if not 'default' in kw:
            kw['default'] = 0
        if not 'ddl' in kw:
            kw['ddl'] = 'blod'
        super(BlodField,self).__init__(**kw)

class VersionField(Field):
    def __init__(self, **kw):
        super(VersionField,self).__init__(name=name,default=0,ddl='bigint')
_triggers = frozenset(['pre_insert','pre_update','pre_delete'])

def _gen_sql(table_name, mappings,checkfirst=True):
    pk = None
    if checkfirst:
        sql=['-- generating SQL for %s:' % table_name, 'create table if not exists `%s` (' % table_name]
    else:
        sql=['-- generating SQL for %s:' % table_name, 'create table `%s` (' % table_name]
    for f in sorted(mappings.values(),lambda x, y: cmp(x._order,y._order)):
        if not hasattr(f,'ddl'):
            raise StandardError('no ddl in field "%s".' %f)
        ddl = f.ddl
        nullable = f.nullable
        if f.primary_key:
            pk = f.name
        sql.append(nullable and '  `%s` %s,' %(f.name,ddl) or '  `%s` %s not null,' %(f.name,ddl))
    sql.append('  primary key(`%s`)' %pk)
    sql.append(');')
    return '\n'.join(sql)

class ModelMetaclass(type):
    '''
    Metaclass for model objects.
    '''
    def __new__(cls,name,bases,attrs):
        #skip base Model class
        if name == 'Model':
            return type.__new__(cls, name, bases, attrs)
        # store all subclasses info
        if not hasattr(cls,'subclasses'):
            cls.subclasses = {}
            cls.sqls = {}
            cls.check_sqls = {}
        if not name in cls.subclasses:
            cls.subclasses[name] = name
            cls.sqls[name] = None
            cls.check_sqls[name] = None
        else:
            logger.waring('Redefine class: %s ' % name)

        logger.info('Scan ORMapping %s...' % name)
        mappings = dict()
        primary_key = None
        for k,v in attrs.iteritems():
            if isinstance(v,Field):
                if not v.name:
                    v.name = k
                logger.info('Found mapping:%s=>%s' %(k,v))
                # check duplicate primary key:
                if v.primary_key:
                    if primary_key:
                        raise TypeError('Cannot define more than 1 primary key in class:%s' % name)
                    if v.updatable:
                        logger.warning('NOTE: change primary key to non-updatable.')
                        v.updatable = False
                    if v.nullable:
                        logger.warning('NOTE: change primary key to non-nullable.')
                        v.nullable = False
                    primary_key = v
                mappings[k] = v
        # check exist of primary key:
        if not primary_key:
            raise TypeError('Primary key not defined in class: %s' %name)
        for k in mappings.iterkeys():
            attrs.pop(k)
        if not '__table__' in attrs:
            attrs['__table__'] = name.lower()
        attrs['__mappings__'] = mappings
        attrs['__primary_key__'] = primary_key
        attrs['__sql__'] = lambda self: _gen_sql(attrs['__table__'],mappings) #FIXME
        cls.sqls[name] = _gen_sql(attrs['__table__'],mappings,checkfirst=False)
        cls.check_sqls[name] = _gen_sql(attrs['__table__'],mappings)
        for trigger in _triggers:
            if not trigger in attrs:
                attrs[trigger] = None
        return type.__new__(cls,name,bases,attrs)

class Model(dict):
    '''
    Base class for ORM.
    >>> class User(Model):
    ...     id = IntegerField(primary_key=True)
    ...     name = StringField()
    ...     email = StringField(updatable=False)
    ...     passwd = StringField(default=lambda: '******')
    ...     last_modified = FloatField()
    ...     def pre_insert(self):
    ...         self.last_modified = time.time()
    >>> u = User(id=10190, name='Michael', email='orm@db.org')
    >>> r = u.insert()
    >>> u.email
    'orm@db.org'
    >>> u.passwd
    '******'
    >>> u.last_modified > (time.time() - 2)
    True
    >>> f = User.get(10190)
    >>> f.name
    'Michael'
    >>> f.email
    'orm@db.org'
    >>> f.email = 'changed@db.org'
    >>> r = f.update() # change email but email is non-updatable!
    >>> len(User.find_all())
    1
    >>> g = User.get(10190)
    >>> g.email
    'orm@db.org'
    >>> r = g.delete()
    >>> len(db.select('select * from user where id=10190'))
    0
    >>> import json
    >>> print User().__sql__()
    -- generating SQL for user:
    create table `user` (
      `id` bigint not null,
      `name` varchar(255) not null,
      `email` varchar(255) not null,
      `passwd` varchar(255) not null,
      `last_modified` real not null,
      primary key(`id`)
    );
    '''
    __metaclass__ = ModelMetaclass

    def __init__(self, **kw):
        super(Model, self).__init__(**kw)

    def __getattr__(self,key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError("'Dict' object has no attribute '%s'" %key)

    def __setattr__(self, key, value):
        self[key] = value

    @classmethod
    def create_all(cls,bind=None, tables=None, checkfirst=True):
        sqls = cls.sqls
        check_sqls = cls.check_sqls
        if checkfirst:
            sqls = check_sqls
        if tables is not None:
            for table in tables:
                try:
                    sql = sqls[table]
                except KeyError:
                    raise TableModuleError("'table module not built' table:'%s' " %table)
                db.update(sqls[table])
        else:
            for k,sql in sqls.iteritems():
                    db.update(sql)

    def create(self):
        sql = self.__sql__()
        #print sql
        db.update(sql)

    @classmethod
    def get(cls, pk):
        '''
        Get by primary key.
        '''
        d = db.select_one('select * from %s where %s=?' %(cls.__table__,cls.__primary_key__.name), pk)
        return cls(**d) if d else None
    @classmethod
    def find_first(cls, where, *args):
        '''
        Find by where clause and return one result. If multiple results found, 
        only the first one returned. If no result found, return None.
        '''
        d = db.select_one('select * from %s %s' %(cls.__table__,where), *args)
        return cls(**d) if d else None
    @classmethod
    def find_all(cls, *args):
        '''
        find all and return list.
        '''
        L = db.select('select * from `%s`' % cls.__table__)
        return [cls(**d) for d in L]
    @classmethod
    def count_all(cls):
        '''
        Find by 'select count(pk) from table' and return integer.
        '''
        return db.select_int('select count(`%s`) from `%s`' %(cls._primary_key__.name,cls__table__))
    @classmethod
    def count_by(cls,where,*args):
        '''
        Find by 'select count(pk) from table where ... ' and return int.
        '''
        return db.select_int('select count(`%s`) from `%s` %s' %(cls.__primary_key__.name,cls.__table__,where),*args)
    

    def update(self):
        self.pre_update and self.pre_update()
        L = []
        args = []
        for k,v in self.__mappings__.iteritems():
            if v.updatable:
                if hasattr(self,k):
                    arg = getattr(self,k)
                else:
                    arg = v.default
                    setattr(self,k,args)
                L.append('`%s`=?' %k)
                args.append(arg)
        pk = self.__primary_key__.name
        args.append(getattr(self,pk))
        db.update('update `%s` set %s where %s=?' %(self.__table__,','.join(L),pk), *args)
        return self
    def delete(self):
        self.pre_delete and self.pre_delete()
        pk = self.__primary_key__.name
        args = (getattr(self,pk),)
        db.update('delete from `%s` where `%s`=?' %(self.__table__,pk),*args)
        return self

    def insert(self):
        self.pre_insert and self.pre_insert()
        params = {}
        for k,v in self.__mappings__.iteritems():
            logger.info("***************%s:%s" % (k,v))
            if v.insertable:
                if not hasattr(self,k):
                    setattr(self, k, v.default)
                params[v.name] = getattr(self,k)
        db.insert('%s' %self.__table__,**params)
        return self


if __name__=='__main__':
    import sys
    LOG_FORMAT = ('%(levelname) -10s %(process)d %(asctime)s %(filename)-10s %(lineno) -5d: %(message)s') 
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    db.create_engine('web_user', 'web_pwd', 'web_db')
    db.update('drop table if exists user')
    db.update('create table user (id int primary key, name text, email text, passwd text, last_modified real)')
    import doctest
    doctest.testmod()
    #sys.exit()
