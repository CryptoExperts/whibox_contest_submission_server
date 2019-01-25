#!/bin/sh

until echo "" | mysql --host=$MYSQL_HOST --user=$MYSQL_USER --password=$MYSQL_PASSWORD > /dev/null 2>&1; do
    echo "MySQL is unavailable yet - sleeping"
    sleep 1
done

>&2 echo "MySQL is up !"

exec "$@"
