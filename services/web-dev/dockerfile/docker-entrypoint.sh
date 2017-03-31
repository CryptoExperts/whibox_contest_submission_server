#!/bin/sh

until echo "" | mysql --host=$MYSQL_HOST --user=$MYSQL_USER --password=$MYSQL_PASSWORD > /dev/null 2>&1; do
    echo "Mysql is unavailable yet - sleeping"
    sleep 1
done

>&2 echo "Mysql is up !"

exec "$@"
