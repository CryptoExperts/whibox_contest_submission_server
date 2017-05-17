FROM crx/nginx:latest

RUN apk add --no-cache 'mysql-client<10.1.23' 'python3<3.6' 'ca-certificates' 'py3-crypto<2.6.2' 'py3-openssl<17.0.0'

RUN pip3 install --upgrade pip
RUN pip3 install Flask==0.12
RUN pip3 install Flask-WTF==0.14.2
RUN pip3 install Flask-SQLAlchemy==2.1
RUN pip3 install Flask-Login==0.4.0
RUN pip3 install passlib==1.7.1
RUN pip3 install mysql-connector==2.1.4
RUN pip3 install blinker==1.4

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
