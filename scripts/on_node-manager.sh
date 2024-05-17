#!/bin/bash

eval $(docker-machine env node-manager-ecdsa)

exec "$@"
