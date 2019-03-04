FROM crx/nginx:latest

RUN apk add --no-cache 'mysql-client<10.4' 'python3<3.7' 'curl' 'py3-crypto<2.6.2'

RUN pip3 install --upgrade pip
RUN pip3 install Flask==1.0.2 Flask-SQLAlchemy==2.3.2 Flask-Login==0.4.1 passlib==1.7.1 PyMySQL==0.9.3 docker==3.7.0

COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod 755 /usr/local/bin/docker-entrypoint.sh

COPY get_compile_and_test.sh /usr/local/bin/
RUN chmod 755 /usr/local/bin/get_compile_and_test.sh

ENTRYPOINT ["docker-entrypoint.sh"]

COPY run_dev.py /
RUN chmod 755 /run_dev.py
CMD ["/run_dev.py"]
