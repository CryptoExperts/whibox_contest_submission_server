#!/bin/sh
set -e

until echo "" | mysql --host=$MYSQL_HOST --user=$MYSQL_USER --password=$MYSQL_PASSWORD > /dev/null 2>&1; do
    echo "MySQL is unavailable yet - sleeping"
    sleep 1
done

>&2 echo "MySQL is up !"

# Create a cron job that gets the compile_and_test route every minute
crontab -l | { cat; echo "* * * * * /usr/local/bin/get_compile_and_test.sh"; } | crontab -
crond

exec "$@"
