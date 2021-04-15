# Whitebox Contest Submission Server

Source code of the Whitebox Contest Submission Server

## About

This repository contains the full source code of the server managing the WhibOx Contest (Edition 2) initiated and developed by [CryptoExperts][crx] and hosted by [cybercrypt][cybercrypt].

For more information about the WhibOx Contest, please visit the [WhibOx Contest (Edition 2) official website][contest].

## Disclaimer

This software is supplied **AS IS** without any warranties. We had a *very* tight time schedule, so please do not expect clean code. Seriously. Any code linter would probably raise more warnings than the total number of code lines in the Python source files. Also note that the aim of this project is basically the exact opposite of what one would typically expect from a webserver: it allows anyone to submit some source code (potentially malicious source code). Then, it compiles and runs this code!

## About the architecture

The server is essentially made of 4 [Docker][docker] services :

* The `web` service, which is a typical [Flask][flask] application in charge of displaying dynamic web content to the users,
* The `mysql` service, which runs a [MySQL][mysql] database,
* The `compile_and_test` service, which compiles the challenges submitted by the contest participant and that tests the compiled challenge against the cryptographic key, and
* The `launcher` service, which prepares and runs a `compile_and_test` service whenever a new challenge is submitted.

Those 4 services are deployed in a [Docker swarm][docker_swarm] which is intended to run on two nodes (the `node_manager` and the `node_sandbox`). In our context, a node typically is a [Virtualbox][virtualbox] virtual machine. The `compile_and_test` service is only allowed to run on the `node_sandbox` while the 3 other services can only run on the `node_manager`.

When running in [Production mode](#running-the-server-in-production-mode), the only publicly accessible service is the `web` service. Moreover, the only service allowed to communicate with all the other services is the `launcher` service. This feature is ensured by connecting the services by means of two distinct (virtual) networks: the `front_network` and the `back_network`. The following diagram illustrates the connections between the four services and how they are deployed on the two nodes:

![Server architecture](images/architecture.png)


## Installation procedure

## Prerequisites

In order to run this server, you need to install the following softwares first:

* [VirtualBox][virtualbox] (tested on versions 6.0.2)
* Docker Engine (tested on Docker version 18.09.3)
* Docker Machine (tested on version 0.16.1)
* Make (tested on versions 3.81)

For Mac users, note that Docker Machine is included by default when installing [Docker for Mac][docker_for_mac].

This software was tested on [macOS Sierra][sierra] and on a [Gentoo Linux][gentoo].

## Production vs. Development

There are two ways this server can be deployed:

* In **development** mode, for testing, updating the code on the fly and immediately seing the result;
* In **production** mode.

### Running the server in Production mode

#### Step 1: Create the virtual machines and the Docker swarm

In a terminal, change the current directory to the root of this git repository and type:

~~~bash
$ make machines-and-swarm
/bin/bash scripts/create_machines_and_swarm.sh
Configuring the node-manager VM
Running pre-create checks...
Creating machine...
(node-manager) Copying /.../.docker/machine/cache/boot2docker.iso to /.../.docker/machine/machines/node-manager/boot2docker.iso...
(node-manager) Creating VirtualBox VM...
(node-manager) Creating SSH key...
(node-manager) Starting the VM...
(node-manager) Check network to re-create if needed...
(node-manager) Waiting for an IP...
Waiting for machine to be running, this may take a few minutes...
Detecting operating system of created instance...
Waiting for SSH to be available...
Detecting the provisioner...
Provisioning with boot2docker...
Copying certs to the local machine directory...
Copying certs to the remote machine...
Setting Docker configuration on the remote daemon...
Checking connection to Docker...
Docker is up and running!
To see how to connect your Docker Client to the Docker Engine running on this virtual machine, run: docker-machine env node-manager
0%...10%...20%...30%...40%...50%...60%...70%...80%...90%...100%
Waiting for VM "node-manager" to power on...
VM "node-manager" has been successfully started.
Waiting for VM to startup...
..VM is up
Configuring the node-sandbox VM
Running pre-create checks...
Creating machine...
(node-sandbox) Copying /.../.docker/machine/cache/boot2docker.iso to /.../.docker/machine/machines/node-sandbox/boot2docker.iso...
(node-sandbox) Creating VirtualBox VM...
(node-sandbox) Creating SSH key...
(node-sandbox) Starting the VM...
(node-sandbox) Check network to re-create if needed...
(node-sandbox) Waiting for an IP...
Waiting for machine to be running, this may take a few minutes...
Detecting operating system of created instance...
Waiting for SSH to be available...
Detecting the provisioner...
Provisioning with boot2docker...
Copying certs to the local machine directory...
Copying certs to the remote machine...
Setting Docker configuration on the remote daemon...
Checking connection to Docker...
Docker is up and running!
To see how to connect your Docker Client to the Docker Engine running on this virtual machine, run: docker-machine env node-sandbox
Waiting for VM to startup...
VM is up
Creating the swarm
Swarm initialized: current node (wiy9j5gsx2pxdt8oa8q5i8sje) is now a manager.

To add a worker to this swarm, run the following command:

    docker swarm join --token SWMTKN-1-1frdub1yh3l7nfeaxadp98ahcxdt476nwub94ccwm4owjaiwrb-968lj0xkflh5dvkbgfih8euam 192.168.99.106:2377

To add a manager to this swarm, run 'docker swarm join-token manager' and follow the instructions.

node-manager
Joining the swarm
This node joined a swarm as a worker.
node-sandbox
~~~

This will create 2 VirtualBox VMs, called `node-manager` and `node-sandbox`, and unite them into a Docker swarm. This takes a few minutes. One can check that the two VMs were successfully created:

~~~bash
$ docker-machine ls
NAME           ACTIVE   DRIVER       STATE     URL                         SWARM   DOCKER     ERRORS
node-manager   -        virtualbox   Running   tcp://192.168.99.106:2376           v18.09.3
node-sandbox   -        virtualbox   Running   tcp://192.168.99.107:2376           v18.09.3
~~~

To stop both VMs:

~~~bash
$ make machines-stop
docker stack rm dev 1>/dev/null 2>&1
make: [machines-stop] Error 1 (ignored)
docker stack rm prod 1>/dev/null 2>&1
make: [machines-stop] Error 1 (ignored)
docker-machine stop node-manager
Stopping "node-manager"...
Machine "node-manager" was stopped.
docker-machine stop node-sandbox
Stopping "node-sandbox"...
Machine "node-sandbox" was stopped.

$ docker-machine ls
NAME           ACTIVE   DRIVER       STATE     URL   SWARM   DOCKER    ERRORS
node-manager   -        virtualbox   Stopped                 Unknown
node-sandbox   -        virtualbox   Stopped                 Unknown
~~~

To turn them back on:

~~~bash
$ make machines-start
~~~

#### Step 2: Change the Docker commands target

Instead of ssh-ing to the `node-manager` VM, it is more convenient to set a few environment variables to automagically send the docker commands to the Docker deamon running on the `node-manager`. This can be done by running:

~~~bash
$ eval $(docker-machine env node-manager)
~~~

#### Step 3 (option 1): Configure an SSL reverse proxy

Unless you are "in the dark ages of manual SSL management" (TM @hashbreaker), it is now time to configure an SSL reverse proxy, that redirects all the `https` traffic it receives to the port `5000` of the `node-manager` (in `http`). This means you need to configure another webserver instance (such as Nginx) or use a commercial alternative (such as Cloudflare or CloudFront). Describing the procedure is beyond the scope of this howto.

#### Step 3 (option 2): Create SSL certificates and configure nginx

If you do not want to configure a reverse proxy, you can integrate SSL directely into the `web-prod` service.

First, uncomment the following line in the file `docker-stack-prod.yml`:

~~~bash
# - 5443:5443
~~~

Generate a private key and a signed SSL certificate (e.g., using [Let's Encrypt][letsencrypt]) and put both files in `services/web-prod/ssl/`. Assuming that the files are named `foobar.key` and `foobar.crt` and that your hostname is `yourhostname.net`, edit the nginx configuration file as follows:

~~~bash
$ cat services/web-prod/config/nginx_vhost.conf
server {
    listen              5000;
    listen              5443 ssl;            # Do not change this. Instead, update docker-stack-prod.yml
    server_name         localhost;           # Update this
    ssl_certificate     /etc/ssl/foobar.crt; # Update this (do not change the /etc/ssl/ part, just change the file name)
    ssl_certificate_key /etc/ssl/foobar.key; # Update this (do not change the /etc/ssl/ part, just change the file name)

    client_max_body_size 50M;

    location /static {
      alias /static;
    }

    location / {
             uwsgi_pass unix:///tmp/uwsgi.sock;
	     include uwsgi_params;
    }
}
~~~

#### Step 4: Build the service images

To build the service images, run:

~~~bash
$ make build-prod
~~~

This takes quite a long time. It builds the images required on both nodes. Once this process is over:

~~~bash
$ docker images
REPOSITORY          TAG                 IMAGE ID            CREATED              SIZE
crx/launcher-prod   latest              a55d41ba2c05        About a minute ago   178MB
crx/web-prod        latest              0eb1ae8d3cd3        About a minute ago   175MB
crx/nginx           latest              ca845c9d0718        2 minutes ago        50.5MB
crx/mysql           8.0.15-1debian9     dc7f6ddade73        4 minutes ago        477MB
alpine              3.9                 5cb3aa00f899        6 days ago           5.53MB
debian              stretch-slim        b805107aed7b        9 days ago           55.3MB

$ docker-machine ssh node-sandbox docker images
REPOSITORY             TAG                 IMAGE ID            CREATED              SIZE
crx/compile_and_test   latest              d4d4f29b5fab        About a minute ago   158MB
alpine                 3.9                 5cb3aa00f899        6 days ago           5.53MB
~~~

Optionally, you can backup the built images by running:

~~~bash
$ make backup-images
~~~


#### Step 5: Configure the services

A few parameters **must** be changed in the `docker-stack-prod.yml` file before the server can be run. These parameters are indicated by a `>` sign:

~~~yaml
version: "3"

services:

    web:
        ports:
>           - 5000:5000 # The first number is the http external port and can be changed, e.g., to 80:5000 (the second number must not be changed)
            # - 5443:5443
        environment:
>           - RECAPTCHA_PUBLIC_KEY=6Le3QBoUAAAAANKiIexuJsV5XE_HjgqICK2kHGCb
>           - RECAPTCHA_PRIVATE_KEY=6Le3QBoUAAAAALLIh0LrUMsIT8F1lV5fr3eqzj4x
>           - MYSQL_PASSWORD=a_not_so_random_user_password # Must be identical in web, launcher and mysql services.


    launcher:
        environment:
>           - MYSQL_PASSWORD=a_not_so_random_user_password # Must be identical in web, launcher and mysql services.

    mysql:
        environment:
>           - MYSQL_ROOT_PASSWORD=a_not_so_random_root_password
>           - MYSQL_PASSWORD=a_not_so_random_user_password # Must be identical in web, launcher and mysql services.
~~~

#### Step 6: Launch the services on the swarm

To launch the services:

~~~bash
$ make stack-deploy-prod
MYSQL_VERSION=8.0.15-1debian9 docker stack deploy -c docker-stack-prod.yml prod
Creating network prod_front_network
Creating network prod_back_network
Creating service prod_mysql
Creating service prod_web
Creating service prod_launcher
~~~

One can check that the `web`, `mysql`, and `launcher` services run on the `node-manager`:

~~~bash
$ docker service ls
ID                  NAME                MODE                REPLICAS            IMAGE                       PORTS
0yqibnlfnipe        prod_launcher       replicated          1/1                 crx/launcher-prod:latest
uz72y4j08oqk        prod_mysql          replicated          1/1                 crx/mysql:8.0.15-1debian9
ycjne0jigiwu        prod_web            replicated          1/1                 crx/web-prod:latest

$ docker ps
CONTAINER ID        IMAGE                       COMMAND                  CREATED              STATUS              PORTS               NAMES
72aa2a64e189        crx/launcher-prod:latest    "docker-entrypoint.s…"   About a minute ago   Up About a minute   80/tcp, 443/tcp     prod_launcher.1.g4nl50uo3pt10fg263sl1sopo
9137b3d9e891        crx/web-prod:latest         "docker-entrypoint.s…"   About a minute ago   Up About a minute   80/tcp, 443/tcp     prod_web.1.1zj3s5qna8kbscvthm6wygmkl
744e9573955b        crx/mysql:8.0.15-1debian9   "docker-entrypoint.s…"   About a minute ago   Up About a minute   3306/tcp            prod_mysql.1.6p3nmq5draj0h6gjvhxr3d7j8
~~~

Note that **no** service runs on the `node-sandbox`:

~~~bash
$ docker-machine ssh node-sandbox docker ps
CONTAINER ID        IMAGE               COMMAND             CREATED             STATUS              PORTS               NAMES
~~~

The `compile_and_test` service runs on-demand, once per challenge to compile.

#### Step 7: Connecting the web service

The first time the services are launched, the `mysql` service creates a database and initializes it. This takes a few seconds. In the meantime, the `web` service waits. This can be checked:

~~~bash
$ docker ps
CONTAINER ID        IMAGE                       COMMAND                  CREATED             STATUS              PORTS               NAMES
72aa2a64e189        crx/launcher-prod:latest    "docker-entrypoint.s…"   2 minutes ago       Up 2 minutes        80/tcp, 443/tcp     prod_launcher.1.g4nl50uo3pt10fg263sl1sopo
9137b3d9e891        crx/web-prod:latest         "docker-entrypoint.s…"   2 minutes ago       Up 2 minutes        80/tcp, 443/tcp     prod_web.1.1zj3s5qna8kbscvthm6wygmkl
744e9573955b        crx/mysql:8.0.15-1debian9   "docker-entrypoint.s…"   2 minutes ago       Up 2 minutes        3306/tcp            prod_mysql.1.6p3nmq5draj0h6gjvhxr3d7j8

$ docker logs prod_web.1.1zj3s5qna8kbscvthm6wygmkl
Mysql is unavailable yet - sleeping
Mysql is unavailable yet - sleeping
Mysql is unavailable yet - sleeping
Mysql is unavailable yet - sleeping
Mysql is unavailable yet - sleeping
Mysql is unavailable yet - sleeping
Mysql is unavailable yet - sleeping
Mysql is unavailable yet - sleeping
Mysql is unavailable yet - sleeping
Mysql is unavailable yet - sleeping
Mysql is unavailable yet - sleeping
Mysql is unavailable yet - sleeping
Mysql is unavailable yet - sleeping
Mysql is unavailable yet - sleeping
Mysql is unavailable yet - sleeping
Mysql is up !
[uWSGI] getting INI configuration from /etc/uwsgi.ini
*** Starting uWSGI 2.0.17.1 (64bit) on [Thu Mar 14 16:59:05 2019] ***
compiled with version: 8.2.0 on 17 December 2018 15:55:40
os: Linux-4.14.104-boot2docker #1 SMP Thu Feb 28 20:58:57 UTC 2019
nodename: 9137b3d9e891
machine: x86_64
clock source: unix
pcre jit disabled
detected number of CPU cores: 1
current working directory: /
detected binary path: /usr/sbin/uwsgi
uWSGI running as root, you can use --uid/--gid/--chroot options
*** WARNING: you are running uWSGI as root !!! (use the --uid flag) ***
chdir() to /etc/..
your memory page size is 4096 bytes
detected max file descriptor number: 1048576
lock engine: pthread robust mutexes
thunder lock: disabled (you can enable it with --thunder-lock)
uwsgi socket 0 bound to UNIX address /tmp/uwsgi.sock fd 3
uWSGI running as root, you can use --uid/--gid/--chroot options
*** WARNING: you are running uWSGI as root !!! (use the --uid flag) ***
Python version: 3.6.8 (default, Jan 24 2019, 16:36:30)  [GCC 8.2.0]
*** Python threads support is disabled. You can enable it with --enable-threads ***
Python main interpreter initialized at 0x55a1622e78e0
uWSGI running as root, you can use --uid/--gid/--chroot options
*** WARNING: you are running uWSGI as root !!! (use the --uid flag) ***
your server socket listen backlog is limited to 100 connections
your mercy for graceful operations on workers is 60 seconds
mapped 364600 bytes (356 KB) for 4 cores
*** Operational MODE: preforking ***
WSGI app 0 (mountpoint='') ready in 1 seconds on interpreter 0x55a1622e78e0 pid: 1 (default app)
uWSGI running as root, you can use --uid/--gid/--chroot options
*** WARNING: you are running uWSGI as root !!! (use the --uid flag) ***
*** uWSGI is running in multiple interpreter mode ***
spawned uWSGI master process (pid: 1)
spawned uWSGI worker 1 (pid: 56, cores: 1)
spawned uWSGI worker 2 (pid: 57, cores: 1)
spawned uWSGI worker 3 (pid: 58, cores: 1)
spawned uWSGI worker 4 (pid: 59, cores: 1)
~~~

Once the `web` service has started, it is possible to fire up a browser and connect to `https://192.168.99.100:5000`. You can run the following command to get exact IP address of the `node-manager`:

~~~bash
$ docker-machine env node-manager | grep HOST
export DOCKER_HOST="tcp://192.168.99.107:2376"
~~~

Note that connecting to the IP address of the `node-sandbox` would also work (thanks to Docker swarm).

![Server index page screenshot](images/index_screenshot.png)

#### Step 8: Forward the host port

At this point, the service is only accessible from the host, not to computers on the same network. We can make the service available to the outside world through the [port forwarding feature of VirtualBox][virtualbox_port_forwarding]. Note that configuring port forwarding as described bellow requires to stop the VMs. Here is how to do it:

~~~bash
$ make machines-stop
$ VBoxManage modifyvm "node-manager" --natpf1 "tcp-port5000,tcp,,5000,,5000";
$ VBoxManage modifyvm "node-manager" --natpf1 "tcp-port5443,tcp,,5443,,5443";
$ make machines-start
$ make stack-deploy-prod
~~~

After a few seconds, the service should be accessible from the outside world on both ports `5000` (in `http`) and `5443` (in `https`) of the host running VirtualBox.

#### Step 9: Shutdown the swarm and the VMs

To properly shutdown the services:

~~~bash
$ make stack-rm-prod
docker stack rm prod
Removing service prod_web
Removing service prod_mysql
Removing service prod_launcher
Removing network prod_front_network
Removing network prod_back_network
~~~

Although this commands looks instantaneous, it takes a few seconds for the services to actually stop. This can be seen by running:

~~~bash
$ docker ps
CONTAINER ID        IMAGE                      COMMAND                  CREATED             STATUS              PORTS               NAMES
72aa2a64e189        crx/launcher-prod:latest   "docker-entrypoint.s…"   4 minutes ago       Up 4 minutes        80/tcp, 443/tcp     prod_launcher.1.g4nl50uo3pt10fg263sl1sopo
9137b3d9e891        crx/web-prod:latest        "docker-entrypoint.s…"   4 minutes ago       Up 4 minutes        80/tcp, 443/tcp     prod_web.1.1zj3s5qna8kbscvthm6wygmkl

$ docker ps
CONTAINER ID        IMAGE               COMMAND             CREATED             STATUS              PORTS               NAMES
~~~

Once the services have shutdown, one can shutdown the VMs:

~~~bash
$ make machines-stop
docker stack rm dev 1>/dev/null 2>&1
docker stack rm prod 1>/dev/null 2>&1
docker-machine stop node-manager
Stopping "node-manager"...
Machine "node-manager" was stopped.
docker-machine stop node-sandbox
Stopping "node-sandbox"...
Machine "node-sandbox" was stopped.

$ docker-machine ls
node-manager   -        virtualbox   Stopped                 Unknown
node-sandbox   -        virtualbox   Stopped                 Unknown
~~~

### Running the server in Production mode (TLDR version)

~~~bash
$ make machines-and-swarm
$ eval $(docker-machine env node-manager)
$ # Create SSL certificates and configure nginx
$ make build-prod
$ # Edit the docker-stack-prod.yml file
$ make stack-deploy-prod
$ # Wait for the web service and check that it started properly (using docker logs -f)
$ # Connect to http://<your host name>:5000 or https://<your host name>:5443
$ # If this does not work, try the section on port forwarding
~~~

### Running the server in Developement mode (TLDR version)

~~~bash
$ make machines-and-swarm
$ eval $(docker-machine env node-manager)
$ make build-dev
$ # Edit the docker-stack-dev.yml file
$ make stack-deploy-dev
$ # Wait for the web service and check that it started properly (using docker logs -f)
$ # Connect to https://192.168.99.100:5000
~~~

Note: in developement mode, the server runs under https with a self-signed certificate. The private key being included in this git repo, you must **not** use the developement mode in production.

[crx]: https://www.cryptoexperts.com/  "CryptoExperts website"
[cybercrypt]: https://www.cyber-crypt.com/ "cybercrypt website"
[contest]: https://whibox.cyber-crypt.com/ "WhibOx 2nd contest website"
[flask]: http://flask.pocoo.org "Flask website"
[mysql]: https://www.mysql.com "MySQL website"
[docker]: https://www.docker.com "Docker website"
[docker_swarm]: https://docs.docker.com/engine/swarm/ "Docker Swarm mode overview"
[virtualbox]: https://www.virtualbox.org "VirtualBox website"
[virtualbox_port_forwarding]: https://www.virtualbox.org/manual/ch06.html#natforward "VirtualBox documentation on port forwarding"
[docker_machine]: https://docs.docker.com/machine/overview/ "Docker Machine Overview"
[gentoo]: https://www.gentoo.org "Gentoo Linux website"
[sierra]: http://www.apple.com/lae/macos/sierra/ "macOS Sierra"
[docker_for_mac]: https://docs.docker.com/docker-for-mac/ "Docker for Mac"
[letsencrypt]: https://letsencrypt.org
