FROM nginx:1.19-alpine

RUN apk update && apk upgrade

RUN apk add 'ca-certificates' 'build-base'
RUN apk add 'mysql-client~=10.5.17'
RUN apk add 'python3~=3.8' 'python3-dev~=3.8' 'py3-pip'
RUN apk add 'py3-crypto~=3.9.9' 'py3-openssl~=20.0.1'

RUN pip3 install --upgrade pip
RUN pip install Flask==1.1.3 Flask-WTF==0.14.3 Flask-SQLAlchemy==2.5.0 SQLAlchemy==1.4.35 Flask-Login==0.5.0 Werkzeug==0.16.1 Jinja2==2.10.1 itsdangerous==1.1.0 wtforms==2.3.3 MarkupSafe==2.0.1 passlib==1.7.4 blinker==1.4 PyMySQL==1.0.2
RUN pip install email-validator==1.1.2

RUN apk add 'uwsgi~=2.0.19.1-r1' 'uwsgi-python3~=2.0.19.1-r1'

COPY config/docker-entrypoint.sh /usr/local/bin/
RUN chmod 755 /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]

COPY config/uwsgi.ini /etc/uwsgi.ini
COPY config/nginx.conf /etc/nginx/nginx.conf
COPY config/nginx_vhost.conf /etc/nginx/conf.d/default.conf
COPY app /app
COPY static /static

COPY ssl/*.crt /etc/ssl/
COPY ssl/*.key /etc/ssl/

COPY config/launcher.sh /usr/local/bin/
copy supplementary-materials/commands.py /
copy supplementary-materials/nist_p256.py /
RUN chmod 755 /usr/local/bin/launcher.sh

CMD ["launcher.sh"]
