#!/usr/bin/env bash

eval $(docker-machine env --shell bash node-sandbox)

exec "$@"
