FROM crx/alpine_with_compilers

COPY main.c compile_and_test.py execute.py /
RUN gcc -w -c /main.c -o /main.o
RUN chmod 755 /compile_and_test.py
CMD ["/compile_and_test.py"]
