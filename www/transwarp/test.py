#!/usr/bin/env python
# -*- coding: utf-8 -*-

if __name__=="__main__":
    from transwarp import db
    db.create_engine(user='webapp',password='password',database='test',host='127.0.0.1',port=3306)
    users = db.select('select * from user')
    print users
