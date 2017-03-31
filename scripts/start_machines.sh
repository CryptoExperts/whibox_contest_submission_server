#!/bin/bash

RED=$'\e[1;31m'
GREEN=$'\e[1;32m'
DEFAULT=$'\e[0m'

function wait_for_vm_to_really_start {
    echo "Waiting for $1 VM to start..."
    until docker-machine ssh $1 true 2>/dev/null
    do
	echo -n "."
	sleep 1
    done
    printf "\nThe $1 VM is started.\n"
}

declare -a VM_VALS
function compute_vm_vals {
    VM_VALS=""
    local line=$(docker-machine ls | tail -n +2 | grep -e "^$1\s" | tr "*" "-")
    local index=0
    for col_title in $line; do
	VM_VALS[$index]="$col_title"
	((index++))
    done
}

# $1 is the vm name, $2 is the mount point
function create_mount_point_if_required {
    if ! docker-machine ssh $1 ls $2 1>/dev/null 2>&1; then
	echo "The $2 folder does not exist on the VM. Creating it."
	docker-machine ssh $1 mkdir -p $2
    else
	echo "The $2 folder already exists on the VM."
    fi
}

# $1 is the vm name, $2 is the mount point, $3 is the shared folder name
function silently_umount_point {
    if echo $(docker-machine ssh $1 sudo mount) | grep -e "$3 on $2" 1>/dev/null 2>&1; then
	docker-machine ssh $1 sudo umount $2
    fi
}

# $1 is the vm name, $2 is the mount point, $3 is the shared folder name
function mount_point {
    if ! echo $(docker-machine ssh $1 sudo mount) | grep -e "$3 on $2" 1>/dev/null 2>&1; then
	echo "Mounting the '$3' shared folder on $2."
	docker-machine ssh $1 sudo mount -t vboxsf -o uid=1000,gid=50 $3 $2
    else
	echo "The '$3' shared folder is already mounted on $2."
    fi
}

########################
# Start the node-manager
########################

echo "$GREEN""Starting the node-manager VM $DEFAULT"

compute_vm_vals "node-manager"

# Start the VM, if necessary

if [ -z "$VM_VALS" ]; then
    echo "$RED""Could not find a VM called node-manager. Skipping this VM.$DEFAULT"
else
    echo "The node-manager VM was found."

    echo "The ${VM_VALS[0]} VM state is: ${VM_VALS[3]}"

    if [ ${VM_VALS[3]} == "Stopped" ]; then
	echo "Starting the ${VM_VALS[0]} VM."
	VBoxManage startvm ${VM_VALS[0]} --type headless 1>/dev/null
	wait_for_vm_to_really_start ${VM_VALS[0]}
	compute_vm_vals "node-manager"
	echo "The ${VM_VALS[0]} VM state is: ${VM_VALS[3]}"
    fi
fi

########################
# Start the node-sandbox
########################

echo "$GREEN""Starting the node-sandbox VM $DEFAULT"

compute_vm_vals "node-sandbox"

# Start the VM, if necessary

if [ -z "$VM_VALS" ]; then
    echo "$RED""Could not find a VM called node-sandbox. Skipping this VM.$DEFAULT"
else
    echo "The node-sandbox VM was found."

    echo "The ${VM_VALS[0]} VM state is: ${VM_VALS[3]}"

    if [ ${VM_VALS[3]} == "Stopped" ]; then
	echo "Starting the ${VM_VALS[0]} VM."
	VBoxManage startvm ${VM_VALS[0]} --type headless 1>/dev/null
	wait_for_vm_to_really_start ${VM_VALS[0]}
	compute_vm_vals "node-sandbox"
	echo "The ${VM_VALS[0]} VM state is: ${VM_VALS[3]}"
    fi
fi
