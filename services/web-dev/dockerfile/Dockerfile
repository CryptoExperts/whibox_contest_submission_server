FROM crx/nginx:latest

RUN apk add --no-cache 'mysql-client<10.4' 'python3<3.7' 'ca-certificates' 'py3-crypto<2.6.2' 'py3-openssl<=19.0.0'

RUN pip3 install --upgrade pip
RUN pip3 install Flask==1.0.2 Flask-WTF==0.14.2 Flask-SQLAlchemy==2.3.2 Flask-Login==0.4.1 passlib==1.7.1 blinker==1.4 PyMySQL==0.9.3


COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod 755 /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]

# Copy mock ssl key and certificate
COPY ssl/foobar.key /
COPY ssl/foobar.crt /

# This should be the only difference from the prod Dockerfile
# By copying run_dev.py, we assume that the app will be mounted in /app in the docker.
COPY run_dev.py /
RUN chmod 755 /run_dev.py
CMD ["/run_dev.py"]
