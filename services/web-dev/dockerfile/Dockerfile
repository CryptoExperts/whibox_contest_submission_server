FROM nginx:1.19-alpine

RUN apk update && apk upgrade

RUN apk add ca-certificates build-base
RUN apk add mysql-client~=10.5.9
RUN apk add python3~=3.8 python3-dev~=3.8 py3-pip
RUN apk add py3-crypto~=3.9.9 py3-openssl~=20.0.1

RUN pip install --upgrade pip
RUN pip install Flask==1.1.2 Flask-WTF==0.14.3 Flask-SQLAlchemy==2.5.1 Flask-Login==0.5.0 Werkzeug==1.0.1
RUN pip install passlib==1.7.4 blinker==1.4 PyMySQL==1.0.2
RUN pip install feedwerk==0.0.2
RUN pip install email-validator==1.1.2

COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod 755 /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]

COPY ssl/foobar.key /
COPY ssl/foobar.crt /

# This should be the only difference from the prod Dockerfile
# By copying run_dev.py, we assume that the app will be mounted in /app in the docker.
COPY run_dev.py /
COPY supplementary-materials/commands.py /
COPY supplementary-materials/nist_p256.py /
RUN chmod 755 /run_dev.py

CMD ["/run_dev.py"]
