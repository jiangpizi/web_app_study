#!/bin/sh

WORKDIR=`pwd`

# start mysql and create database
#service mysqld start
#mysql -uroot << EOF
#drop database poc_db;
#drop user 'poc_user'@'localhost';
#flush privileges;
#EOF
mysql -u root -p << EOF
drop database web_db;
drop user 'web_user'@'localhost';
create user 'web_user'@'localhost' identified by 'web_pwd';
create database web_db default character set = utf8;
grant all on web_db.* to 'web_user'@'localhost';
EOF
echo "web_db  created ok."
echo "----> ALL DONE <-------"

