FROM nginx:1.19.9-alpine

RUN apk add --no-cache 'mysql-client'
RUN apk add --no-cache 'ca-certificates'
RUN apk add --no-cache 'python3' 'python3-dev' 'py3-crypto' 'py3-openssl' 'py3-pip'
RUN apk add --no-cache 'build-base'

RUN pip --version
RUN pip install --upgrade pip
RUN pip install Flask==1.1.2 Flask-WTF==0.14.3 Flask-SQLAlchemy==2.5.1 Flask-Login==0.5.0
RUN pip install passlib==1.7.4 blinker==1.4 PyMySQL==1.0.2
RUN pip install email_validator


COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod 755 /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]

# Copy mock ssl key and certificate
COPY ssl/foobar.key /
COPY ssl/foobar.crt /

# This should be the only difference from the prod Dockerfile
# By copying run_dev.py, we assume that the app will be mounted in /app in the docker.
COPY run_dev.py /
COPY supplementary-materials/commands.py /
COPY supplementary-materials/nist_p256.py /
RUN chmod 755 /run_dev.py
CMD ["/run_dev.py"]
