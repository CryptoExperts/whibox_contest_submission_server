#!/bin/bash

RED=$'\e[1;31m'
GREEN=$'\e[1;32m'
DEFAULT=$'\e[0m'

###############################
# Configure the node-manager-ecdsa VM
###############################

echo "$GREEN""Configuring the node-manager-ecdsa VM $DEFAULT"

if docker-machine ls | tail -n +2 | cut -d ' ' -f 1 | grep -e '^node-manager-ecdsa$' -q; then
    echo "$RED""A VM called node-manager-ecdsa already exists. Skipping this VM.$DEFAULT"
else
    if [ ! -d $PWD/volumes ]; then
	mkdir $PWD/volumes
    fi
    if [ ! -d $PWD/volumes/database ]; then
	mkdir $PWD/volumes/database
    fi
    if [ ! -d $PWD/volumes/whitebox_program_uploads ]; then
	mkdir $PWD/volumes/whitebox_program_uploads
    fi
    if [ ! -d $PWD/volumes/whitebox_program_uploads/compilations ]; then
	mkdir $PWD/volumes/whitebox_program_uploads/compilations
    fi

    docker-machine create -d virtualbox --virtualbox-share-folder $PWD/volumes:volumes node-manager-ecdsa
    VBoxManage controlvm node-manager-ecdsa poweroff
    VBoxManage sharedfolder add node-manager-ecdsa --name services --hostpath $PWD/services --automount
    VBoxManage startvm node-manager-ecdsa --type headless
    echo "Waiting for VM to startup..."
    until docker-machine ssh node-manager-ecdsa true 2>/dev/null
    do
	echo -n "."
	sleep 1
    done
    echo "VM is up"
    docker-machine ssh node-manager-ecdsa sudo mount -t vboxsf -o uid=1000,gid=50 services /services
    docker-machine ssh node-manager-ecdsa sudo mount -t vboxsf -o uid=1000,gid=50 volumes /volumes
fi

###############################
# Configure the node-sandbox-ecdsa VM
###############################

echo "$GREEN""Configuring the node-sandbox-ecdsa VM $DEFAULT"

if docker-machine ls | tail -n +2 | cut -d ' ' -f 1 | grep -e '^node-sandbox-ecdsa$' -q; then
    echo "$RED""A VM called node-sandbox-ecdsa already exists. Skipping this VM.$DEFAULT"
else
    name=node-sandbox-ecdsa
    docker-machine create -d virtualbox --virtualbox-share-folder $PWD/volumes/whitebox_program_uploads:whitebox_program_uploads $name
    echo "Waiting for VM to startup..."
    until docker-machine ssh $name true 2>/dev/null
    do
	echo -n "."
	sleep 1
    done
    echo "VM is up"
fi

##################
# Create the swarm
##################

echo "$GREEN""Creating the swarm $DEFAULT"
MANAGER_IP=$(docker-machine ip node-manager-ecdsa)

docker-machine ssh node-manager-ecdsa docker swarm init --advertise-addr $MANAGER_IP
docker-machine ssh node-manager-ecdsa docker node update --label-add vm=node-manager-ecdsa node-manager-ecdsa

################
# Join the swarm
################

echo "$GREEN""Joining the swarm $DEFAULT"

SWARM_WORKER_TOKEN=$(docker-machine ssh node-manager-ecdsa docker swarm join-token worker -q)

attempts=0
until docker-machine ssh node-sandbox-ecdsa docker swarm join --token $SWARM_WORKER_TOKEN $MANAGER_IP:2377 2>/dev/null
do
    echo -n "."
    ((attempts++))
    if [ $attempts -gt 30 ]
    then
    	echo "Attempt to join swarm failed. Please try again manually by typing:"
    	echo "docker-machine ssh node-sandbox-ecdsa docker swarm join --token $SWARM_WORKER_TOKEN $MANAGER_IP:2377"
    	echo "docker-machine ssh node-manager-ecdsa docker node update --label-add vm=node-sandbox-ecdsa node-sandbox-ecdsa"
    	exit 1
    fi
    sleep 1
done
docker-machine ssh node-manager-ecdsa docker node update --label-add vm=node-sandbox-ecdsa node-sandbox-ecdsa
