FROM crx/nginx:latest

RUN apk add --no-cache 'uwsgi<2.0.15' 'uwsgi-python3<2.0.15' 'mysql-client<10.1.23' 'python3<3.6' 'ca-certificates' 'py3-crypto<2.6.2'

RUN pip3 install --upgrade pip
RUN pip3 install Flask==0.12
RUN pip3 install Flask-WTF==0.14.2
RUN pip3 install Flask-SQLAlchemy==2.1
RUN pip3 install Flask-Login==0.4.0
RUN pip3 install passlib==1.7.1
RUN pip3 install mysql-connector==2.1.4
RUN pip3 install blinker==1.4

COPY config/docker-entrypoint.sh /usr/local/bin/
RUN chmod 755 /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]

COPY config/uwsgi.ini /etc/uwsgi.ini
COPY config/nginx.conf /etc/nginx/nginx.conf
COPY config/nginx_vhost.conf /etc/nginx/conf.d/default.conf
COPY app /app
COPY static /static

COPY config/launcher.sh /usr/local/bin/
RUN chmod 755 /usr/local/bin/launcher.sh

CMD ["launcher.sh"]
