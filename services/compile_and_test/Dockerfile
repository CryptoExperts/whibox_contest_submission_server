FROM alpine:3.5

RUN apk add --no-cache 'gcc<6.2.3' 'python3<3.6'  'libc-dev<0.8'

# COPY compile.sh /
# RUN chmod 755 /compile.sh
# CMD ["/compile.sh"]

COPY main.c /
RUN gcc -c /main.c -o /main.o

COPY compile_and_test.py /
RUN chmod 755 /compile_and_test.py
CMD ["/compile_and_test.py"]
