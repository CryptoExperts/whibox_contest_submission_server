FROM alpine:3.9

RUN apk update
RUN apk add --no-cache 'gcc==8.2.0-r2' 'python3<3.8'  'libc-dev<0.8'
RUN apk add --no-cache -X http://dl-cdn.alpinelinux.org/alpine/edge/testing 'tcc==0.9.27-r1'

COPY main.c /
RUN gcc -c /main.c -o /main.o

COPY compile_and_test.py /
RUN chmod 755 /compile_and_test.py
CMD ["/compile_and_test.py"]
