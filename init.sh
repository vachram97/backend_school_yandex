#!/bin/bash

apt install mysql-server python3 python3-pip libmysqlclient-dev

mysql < init.sql

pip3 install -r requirements.txt
