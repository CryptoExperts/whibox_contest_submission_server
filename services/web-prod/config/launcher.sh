#!/bin/sh

nginx
exec uwsgi --ini /etc/uwsgi.ini
