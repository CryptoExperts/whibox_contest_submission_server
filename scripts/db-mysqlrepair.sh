#!/bin/bash

# Get the kind of stack (dev or prod)
if docker ps | grep -q "dev_launcher"; then
	DB_CONFIG_FILE=docker-stack-dev.yml
else
	DB_CONFIG_FILE=docker-stack-prod.yml
fi

DB_DOCKER=`docker ps | grep mysql | cut -d' ' -f1`
DB_USER=`cat $DB_CONFIG_FILE |grep MYSQL_USER|cut -f2 -d":"|sed 's/^ //g'|sed "s/'//g"|sed 's/"//g'`
DB_PWD=`cat $DB_CONFIG_FILE |grep MYSQL_PASSWORD|cut -f2 -d":"|sed 's/^ //g'|sed "s/'//g"|sed 's/"//g'`
DB_DATABASE=`cat $DB_CONFIG_FILE |grep MYSQL_DATABASE|cut -f2 -d":"|sed 's/^ //g'|sed "s/'//g"|sed 's/"//g'`

# Launch the shell
docker exec -it $DB_DOCKER /bin/bash -c "mysqlcheck -r $DB_DATABASE user -u$DB_USER -p$DB_PWD"
docker exec -it $DB_DOCKER /bin/bash -c "mysqlcheck -r $DB_DATABASE program -u$DB_USER -p$DB_PWD"
