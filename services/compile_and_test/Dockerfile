FROM crx/alpine_with_compilers

# Change our 'user' to lower privileges
RUN adduser -D user

COPY --chown=user:user supplementary-materials/main.c compile_and_test.py execute.py /

RUN gcc -w -c ./main.c -o ./main.o
RUN chmod a+r ./main.o

USER user
RUN chmod 755 ./compile_and_test.py
CMD ["./compile_and_test.py"]
