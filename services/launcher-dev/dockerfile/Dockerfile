FROM nginx:1.19.9-alpine

RUN apk add --no-cache 'mysql-client' 'curl'
RUN apk add --no-cache 'python3' 'python3-dev' 'py3-crypto' 'py3-pip'
RUN apk add --no-cache 'build-base'

RUN pip install --upgrade pip
RUN pip install Flask==1.0.2 Flask-SQLAlchemy==2.3.2 Flask-Login==0.4.1 passlib==1.7.1 PyMySQL==0.9.3 docker==3.7.0

COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod 755 /usr/local/bin/docker-entrypoint.sh

COPY get_compile_and_test.sh /usr/local/bin/
RUN chmod 755 /usr/local/bin/get_compile_and_test.sh

ENTRYPOINT ["docker-entrypoint.sh"]

COPY run_dev.py /
RUN chmod 755 /run_dev.py
CMD ["/run_dev.py"]
