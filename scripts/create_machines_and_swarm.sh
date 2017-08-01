#!/bin/bash

RED=$'\e[1;31m'
GREEN=$'\e[1;32m'
DEFAULT=$'\e[0m'

###############################
# Configure the node-manager VM
###############################

echo "$GREEN""Configuring the node-manager VM $DEFAULT"

if docker-machine ls | tail -n +2 | cut -d ' ' -f 1 | grep -e '^node-manager$' -q; then
    echo "$RED""A VM called node-manager already exists. Skipping this VM.$DEFAULT"
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

    docker-machine create -d virtualbox --virtualbox-share-folder $PWD/volumes:volumes node-manager
    VBoxManage controlvm node-manager poweroff
    VBoxManage sharedfolder add node-manager --name services --hostpath $PWD/services --automount
    VBoxManage startvm node-manager --type headless
    echo "Waiting for VM to startup..."
    until docker-machine ssh node-manager true 2>/dev/null
    do
	echo -n "."
	sleep 1
    done
    echo "VM is up"
    docker-machine ssh node-manager sudo mount -t vboxsf -o uid=1000,gid=50 services /services
    docker-machine ssh node-manager sudo mount -t vboxsf -o uid=1000,gid=50 volumes /volumes
fi

###############################
# Configure the node-sandbox VM
###############################

echo "$GREEN""Configuring the node-sandbox VM $DEFAULT"

if docker-machine ls | tail -n +2 | cut -d ' ' -f 1 | grep -e '^node-sandbox$' -q; then
    echo "$RED""A VM called node-sandbox already exists. Skipping this VM.$DEFAULT"
else
    name=node-sandbox
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
MANAGER_IP=$(docker-machine ip node-manager)

docker-machine ssh node-manager docker swarm init --advertise-addr $MANAGER_IP
docker-machine ssh node-manager docker node update --label-add vm=node-manager node-manager

################
# Join the swarm
################

echo "$GREEN""Joining the swarm $DEFAULT"

SWARM_WORKER_TOKEN=$(docker-machine ssh node-manager docker swarm join-token worker -q)

attempts=0
until docker-machine ssh node-sandbox docker swarm join --token $SWARM_WORKER_TOKEN $MANAGER_IP:2377 2>/dev/null
do
    echo -n "."
    ((attempts++))
    if [ $attempts -gt 30 ]
    then
    	echo "Attempt to join swarm failed. Please try again manually by typing:"
    	echo "docker-machine ssh node-sandbox docker swarm join --token $SWARM_WORKER_TOKEN $MANAGER_IP:2377"
    	echo "docker-machine ssh node-manager docker node update --label-add vm=node-sandbox node-sandbox"
    	exit 1
    fi
    sleep 1
done
docker-machine ssh node-manager docker node update --label-add vm=node-sandbox node-sandbox
