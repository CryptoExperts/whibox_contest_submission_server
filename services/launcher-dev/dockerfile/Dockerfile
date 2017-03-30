FROM crx/nginx:latest

RUN apk add --no-cache 'mysql-client<10.1.23' 'python3<3.6' 'py3-crypto<2.6.2'

RUN pip3 install --upgrade pip
RUN pip3 install Flask==0.12
RUN pip3 install Flask-SQLAlchemy==2.1
RUN pip3 install mysql-connector==2.1.4
RUN pip3 install docker==2.1.0
RUN pip3 install Flask-Login==0.4.0
RUN pip3 install passlib==1.7.1

COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod 755 /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]

COPY run_dev.py /
RUN chmod 755 /run_dev.py
CMD ["/run_dev.py"]
