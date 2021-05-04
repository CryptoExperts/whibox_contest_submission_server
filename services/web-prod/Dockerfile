FROM nginx:1.19.9-alpine

RUN apk add --no-cache 'mysql-client'
RUN apk add --no-cache 'ca-certificates'

RUN apk add --no-cache 'python3' 'python3-dev' 'py3-crypto' 'py3-openssl' 'py3-pip'
RUN apk add --no-cache 'build-base'
RUN apk add --no-cache 'uwsgi' 'uwsgi-python3'

RUN pip3 install --upgrade pip
RUN pip install flask==1.1.2 flask-wtf==0.14.3 flask-sqlalchemy==2.5.1 flask-login==0.5.0
RUN pip install passlib==1.7.4 blinker==1.4 pymysql==1.0.2
RUN pip install feedwerk==0.0.2
RUN pip install email_validator

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
