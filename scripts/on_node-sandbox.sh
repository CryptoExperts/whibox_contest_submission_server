#!/bin/bash

eval $(docker-machine env node-sandbox)

exec "$@"
