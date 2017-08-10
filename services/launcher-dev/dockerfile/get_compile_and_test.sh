#!/bin/ash

2>&1 echo "Contacting 127.0.0.1:5000/compile_and_test..."
curl 127.0.0.1:5000/compile_and_test
2>&1 echo "curl return status: $?"


# Any modification made to this file might have to be propagated to the get_compile_and_test.sh used in production.
