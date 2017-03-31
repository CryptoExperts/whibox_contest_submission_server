#!/bin/bash

until [ "$(docker ps -q | wc -l)" -eq "0" ]
do
    echo -n '.'
    sleep 1
done
echo 'done'
