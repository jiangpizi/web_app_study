#!/usr/bin/env python
# -*- coding: utf-8 -*-

def create_engine():



if __name__=="__main__":
    
    db.create_engine(user='webapp',password='password',database='test',host='127.0.0.1',port=3306)
    users = db.select('select * from user')
    print users
