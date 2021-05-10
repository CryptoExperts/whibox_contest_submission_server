FROM nginx:1.19-alpine

RUN apk update && apk upgrade

RUN apk add build-base curl
RUN apk add mysql-client~=10.5.9

RUN apk add python3~=3.8 python3-dev~=3.8 py3-pip
RUN apk add py3-crypto~=3.9.9

RUN pip install --upgrade pip
RUN pip install Flask==1.1.2 Flask-SQLAlchemy==2.5.1 Flask-Login==0.5.0
RUN pip install passlib==1.7.4 PyMySQL==1.0.2
RUN pip install docker==5.0.0 click==7.1.2

COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod 755 /usr/local/bin/docker-entrypoint.sh

COPY get_compile_and_test.sh /usr/local/bin/
RUN chmod 755 /usr/local/bin/get_compile_and_test.sh

ENTRYPOINT ["docker-entrypoint.sh"]

COPY run_dev.py /
COPY supplementary-materials/commands.py /
COPY supplementary-materials/nist_p256.py /

RUN chmod 755 /run_dev.py
CMD ["/run_dev.py"]
