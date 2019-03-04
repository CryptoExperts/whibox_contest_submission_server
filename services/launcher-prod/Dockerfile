FROM crx/nginx:latest

RUN apk add --no-cache 'uwsgi<2.0.18' 'uwsgi-python3<2.0.18' 'mysql-client<10.4' 'python3<3.7' 'curl' 'py3-crypto<2.6.2'

RUN pip3 install --upgrade pip
RUN pip3 install Flask==1.0.2 Flask-SQLAlchemy==2.3.2 Flask-Login==0.4.1 passlib==1.7.1 PyMySQL==0.9.3 docker==3.7.0


COPY config/docker-entrypoint.sh /usr/local/bin/
RUN chmod 755 /usr/local/bin/docker-entrypoint.sh

COPY config/get_compile_and_test.sh /usr/local/bin/
RUN chmod 755 /usr/local/bin/get_compile_and_test.sh

ENTRYPOINT ["docker-entrypoint.sh"]

COPY config/uwsgi.ini /etc/uwsgi.ini
COPY config/nginx.conf /etc/nginx/nginx.conf
COPY config/nginx_vhost.conf /etc/nginx/conf.d/default.conf
COPY app /app

COPY config/launcher.sh /usr/local/bin/
RUN chmod 755 /usr/local/bin/launcher.sh

CMD ["launcher.sh"]
