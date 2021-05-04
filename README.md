# WhibOx Contest Submission Server

Source code of the [WhibOx Contest][whibox-contest] Submission Server

## About

This repository contains the full source code of the server managing the WhibOx Contest (Edition 3) initiated and developed by [CryptoExperts][crx] and hosted on [Google Cloud][google-cloud] by [Stefan Kölbl][stefan].

For more information about the WhibOx Contest Edition 3, please visit the [WhibOx Contest (Edition 3) official website][contest].

## Disclaimer

This software is supplied **AS IS** without any warranties.
We had a *very* tight time schedule, so please do not expect clean code.
Seriously.
Any code linter would probably raise more warnings than the total number of code lines in the Python source files.
Also note that the aim of this project is basically the exact opposite of what one would typically expect from a web server: it allows anyone to submit some source code (potentially malicious source code).
Then, it compiles and runs this code!

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

* [VirtualBox][virtualbox] (tested on versions 6.1.22)
* Docker Engine (tested on Docker version 20.10.5)
* Docker Machine (tested on version 0.16.1)
* Make (tested on versions 3.81)

For Mac users, note that Docker Machine is included by default when installing [Docker for Mac][docker_for_mac].

This software was tested on [macOS Big Sur][bigsur].

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
Swarm initialized: current node (hfscmjw3h2ebw50iik8e73khp) is now a manager.

To add a worker to this swarm, run the following command:

    docker swarm join --token SWMTKN-1-3gi6r65r6f26mluhdjeh1u9b9n8rk5zco8glx6xn0767wxmy67-1m6zm1nmtisnij2u6nz96bhov 192.168.99.106:2377

To add a manager to this swarm, run 'docker swarm join-token manager' and follow the instructions.

node-manager
Joining the swarm
This node joined a swarm as a worker.
node-sandbox
~~~

This will create 2 VirtualBox VMs, called `node-manager` and `node-sandbox`, and unite them into a Docker swarm.
This takes a few minutes.
One can check that the two VMs were successfully created:

~~~bash
$ docker-machine ls
NAME           ACTIVE   DRIVER       STATE     URL                         SWARM   DOCKER      ERRORS
node-manager   -        virtualbox   Running   tcp://192.168.99.106:2376           v19.03.12
node-sandbox   -        virtualbox   Running   tcp://192.168.99.107:2376           v19.03.12
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

Instead of SSH-ing to the `node-manager` VM, it is more convenient to set a few environment variables to automatically send the docker commands to the Docker daemon running on the `node-manager`.
This can be done by running:

~~~bash
$ eval $(docker-machine env node-manager)
~~~

#### Step 3 (option 1): Configure an SSL reverse proxy

Unless you are "in the dark ages of manual SSL management" (TM @hashbreaker), it is now time to configure an SSL reverse proxy, that redirects all the `https` traffic it receives to the port `5000` of the `node-manager` (in `http`).
This means you need to configure another web server instance (such as Nginx) or use a commercial alternative (such as Cloudflare or CloudFront). Describing the procedure is beyond the scope of this howto.

#### Step 3 (option 2): Create SSL certificates and configure nginx

If you do not want to configure a reverse proxy, you can integrate SSL directly into the `web-prod` service.

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
REPOSITORY          TAG           IMAGE ID       CREATED              SIZE
crx/launcher-prod   latest        5fef353df18c   21 seconds ago       432MB
crx/web-prod        latest        58c10ebaa30f   About a minute ago   440MB
nginx               1.19-alpine   a64a6e03b055   2 weeks ago          22.6MB

$ docker-machine ssh node-sandbox docker images
REPOSITORY                  TAG                 IMAGE ID            CREATED             SIZE
crx/compile_and_test        latest              dfb2f15cb36a        14 seconds ago      177MB
crx/alpine_with_compilers   latest              506f19dbcaa0        16 seconds ago      177MB
alpine                      3.13.5              6dbb9cc54074        2 weeks ago         5.61MB
~~~

Optionally, you can backup the built images by running:

~~~bash
$ make backup-images
~~~


#### Step 5: Configure the services

A few parameters **must** be changed in the `docker-stack-prod.yml` file before the server can be run.
These parameters are indicated by a `>` sign:

~~~yaml
version: "3.9"

x-recaptcha-variables: &recaptcha-variables
>   RECAPTCHA_PUBLIC_KEY: '6LejhMAaAAAAAETqdRAe39yUFQ1xWfYfGYuka-Eu'
>   RECAPTCHA_PRIVATE_KEY: '6LejhMAaAAAAABOe3jala1h8EQ9Fvg-J9y5qJgAM'
>   SECRET_KEY: 'da39a3ee5e6b4b0d3255bfef95601890afd80709'

x-db-variables: &db-variables
>   MYSQL_PASSWORD: 'a_not_so_random_user_password'

services:

    mysql:
        environment:
>           MYSQL_ROOT_PASSWORD: "a_not_so_random_root_password"
~~~

#### Step 6: Launch the services on the swarm

To launch the services:

~~~bash
$ make stack-deploy-prod
docker stack deploy -c docker-stack-prod.yml prod
Creating network prod_front_network
Creating network prod_back_network
Creating service prod_mysql
Creating service prod_web
Creating service prod_launcher
~~~

One can check that the `web`, `mysql`, and `launcher` services run on the `node-manager`:

~~~bash
$ docker service ls
ID             NAME            MODE         REPLICAS   IMAGE                      PORTS
branj3ox25ke   prod_launcher   replicated   1/1        crx/launcher-prod:latest
m3v3x1c955di   prod_mysql      replicated   1/1        mysql:8.0.23
yofca8hvsv7b   prod_web        replicated   1/1        crx/web-prod:latest        *:5000->5000/tcp, *:5443->5443/tcp

$ docker ps
CONTAINER ID   IMAGE                      COMMAND                  CREATED          STATUS          PORTS                 NAMES
3cc4f709fb99   mysql:8.0.23               "docker-entrypoint.s…"   23 seconds ago   Up 23 seconds   3306/tcp, 33060/tcp   prod_mysql.1.kt87s4vpt39q9lg42ouem6fcf
d8d2fbe6832c   crx/launcher-prod:latest   "docker-entrypoint.s…"   24 seconds ago   Up 23 seconds   80/tcp                prod_launcher.1.20d0k3tiq8to70y6bd1axo1pf
332105359cb3   crx/web-prod:latest        "docker-entrypoint.s…"   25 seconds ago   Up 25 seconds   80/tcp                prod_web.1.xuk8l6pkym05extps3vj305sj
~~~

Note that **no** service runs on the `node-sandbox`:

~~~bash
$ docker-machine ssh node-sandbox docker ps
CONTAINER ID        IMAGE               COMMAND             CREATED             STATUS              PORTS               NAMES
~~~

The `compile_and_test` service runs on-demand, once per challenge to compile.

#### Step 7: Connecting the web service

The first time the services are launched, the `mysql` service creates a database and initializes it.
This takes a few seconds.
In the meantime, the `web` service waits.
This can be checked:

~~~bash
$ docker ps
CONTAINER ID        IMAGE                       COMMAND                  CREATED             STATUS              PORTS               NAMES
72aa2a64e189        crx/launcher-prod:latest    "docker-entrypoint.s…"   2 minutes ago       Up 2 minutes        80/tcp, 443/tcp     prod_launcher.1.g4nl50uo3pt10fg263sl1sopo
9137b3d9e891        crx/web-prod:latest         "docker-entrypoint.s…"   2 minutes ago       Up 2 minutes        80/tcp, 443/tcp     prod_web.1.1zj3s5qna8kbscvthm6wygmkl
744e9573955b        crx/mysql:8.0.15-1debian9   "docker-entrypoint.s…"   2 minutes ago       Up 2 minutes        3306/tcp            prod_mysql.1.6p3nmq5draj0h6gjvhxr3d7j8

$ docker service logs prod_web                                         16:31:30
prod_web.1.xuk8l6pkym05@node-manager    | Mysql is unavailable yet - sleeping
prod_web.1.xuk8l6pkym05@node-manager    | Mysql is unavailable yet - sleeping
prod_web.1.xuk8l6pkym05@node-manager    | Mysql is unavailable yet - sleeping
prod_web.1.xuk8l6pkym05@node-manager    | Mysql is up !
prod_web.1.xuk8l6pkym05@node-manager    | [uWSGI] getting INI configuration from /etc/uwsgi.ini
prod_web.1.xuk8l6pkym05@node-manager    | *** Starting uWSGI 2.0.19.1 (64bit) on [Tue May  4 14:29:46 2021] ***
prod_web.1.xuk8l6pkym05@node-manager    | compiled with version: 10.2.1 20201203 on 09 January 2021 08:06:39
prod_web.1.xuk8l6pkym05@node-manager    | os: Linux-4.19.130-boot2docker #1 SMP Mon Jun 29 23:52:55 UTC 2020
prod_web.1.xuk8l6pkym05@node-manager    | nodename: 332105359cb3
prod_web.1.xuk8l6pkym05@node-manager    | machine: x86_64
prod_web.1.xuk8l6pkym05@node-manager    | clock source: unix
prod_web.1.xuk8l6pkym05@node-manager    | pcre jit disabled
prod_web.1.xuk8l6pkym05@node-manager    | detected number of CPU cores: 1
prod_web.1.xuk8l6pkym05@node-manager    | current working directory: /
prod_web.1.xuk8l6pkym05@node-manager    | detected binary path: /usr/sbin/uwsgi
prod_web.1.xuk8l6pkym05@node-manager    | uWSGI running as root, you can use --uid/--gid/--chroot options
prod_web.1.xuk8l6pkym05@node-manager    | *** WARNING: you are running uWSGI as root !!! (use the --uid flag) ***
prod_web.1.xuk8l6pkym05@node-manager    | chdir() to /etc/..
prod_web.1.xuk8l6pkym05@node-manager    | your memory page size is 4096 bytes
prod_web.1.xuk8l6pkym05@node-manager    | detected max file descriptor number: 1048576
prod_web.1.xuk8l6pkym05@node-manager    | lock engine: pthread robust mutexes
prod_web.1.xuk8l6pkym05@node-manager    | thunder lock: disabled (you can enable it with --thunder-lock)
prod_web.1.xuk8l6pkym05@node-manager    | uwsgi socket 0 bound to UNIX address /tmp/uwsgi.sock fd 3
prod_web.1.xuk8l6pkym05@node-manager    | uWSGI running as root, you can use --uid/--gid/--chroot options
prod_web.1.xuk8l6pkym05@node-manager    | *** WARNING: you are running uWSGI as root !!! (use the --uid flag) ***
prod_web.1.xuk8l6pkym05@node-manager    | Python version: 3.8.8 (default, Mar 15 2021, 13:10:14)  [GCC 10.2.1 20201203]
prod_web.1.xuk8l6pkym05@node-manager    | *** Python threads support is disabled. You can enable it with --enable-threads ***
prod_web.1.xuk8l6pkym05@node-manager    | Python main interpreter initialized at 0x7f679def56c0
prod_web.1.xuk8l6pkym05@node-manager    | uWSGI running as root, you can use --uid/--gid/--chroot options
prod_web.1.xuk8l6pkym05@node-manager    | *** WARNING: you are running uWSGI as root !!! (use the --uid flag) ***
prod_web.1.xuk8l6pkym05@node-manager    | your server socket listen backlog is limited to 100 connections
prod_web.1.xuk8l6pkym05@node-manager    | your mercy for graceful operations on workers is 60 seconds
prod_web.1.xuk8l6pkym05@node-manager    | mapped 364600 bytes (356 KB) for 4 cores
prod_web.1.xuk8l6pkym05@node-manager    | *** Operational MODE: preforking ***
prod_web.1.xuk8l6pkym05@node-manager    | WSGI app 0 (mountpoint='') ready in 1 seconds on interpreter 0x7f679def56c0 pid: 1 (default app)
prod_web.1.xuk8l6pkym05@node-manager    | uWSGI running as root, you can use --uid/--gid/--chroot options
prod_web.1.xuk8l6pkym05@node-manager    | *** WARNING: you are running uWSGI as root !!! (use the --uid flag) ***
prod_web.1.xuk8l6pkym05@node-manager    | *** uWSGI is running in multiple interpreter mode ***
prod_web.1.xuk8l6pkym05@node-manager    | spawned uWSGI master process (pid: 1)
prod_web.1.xuk8l6pkym05@node-manager    | spawned uWSGI worker 1 (pid: 21, cores: 1)
prod_web.1.xuk8l6pkym05@node-manager    | spawned uWSGI worker 2 (pid: 22, cores: 1)
prod_web.1.xuk8l6pkym05@node-manager    | spawned uWSGI worker 3 (pid: 23, cores: 1)
prod_web.1.xuk8l6pkym05@node-manager    | spawned uWSGI worker 4 (pid: 24, cores: 1)
~~~

Once the `web` service has started, it is possible to fire up a browser and connect to `https://192.168.99.100:5000`.
You can run the following command to get exact IP address of the `node-manager`:

~~~bash
$ docker-machine env node-manager | grep HOST
export DOCKER_HOST="tcp://192.168.99.100:2376"
~~~

Note that connecting to the IP address of the `node-sandbox` would also work (thanks to Docker swarm).

![Server index page screenshot](images/index_screenshot.png)

#### Step 8: Forward the host port

At this point, the service is only accessible from the host, not to computers on the same network.
We can make the service available to the outside world through the [port forwarding feature of VirtualBox][virtualbox_port_forwarding].
Note that configuring port forwarding as described bellow requires to stop the VMs.
Here is how to do it:

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

Note: in development mode, the server runs under https with a self-signed certificate.
The private key being included in this git repo, you must **not** use the development mode in production.

[crx]: https://www.cryptoexperts.com/  "CryptoExperts website"
[google-cloud]: https://cloud.google.com/
[contest]: https://whibox.io/contests/2021/
[flask]: http://flask.pocoo.org "Flask website"
[mysql]: https://www.mysql.com "MySQL website"
[docker]: https://www.docker.com "Docker website"
[docker_swarm]: https://docs.docker.com/engine/swarm/ "Docker Swarm mode overview"
[virtualbox]: https://www.virtualbox.org "VirtualBox website"
[virtualbox_port_forwarding]: https://www.virtualbox.org/manual/ch06.html#natforward "VirtualBox documentation on port forwarding"
[docker_machine]: https://docs.docker.com/machine/overview/ "Docker Machine Overview"
[bigsur]: https://www.apple.com/lae/macos/big-sur/
[docker_for_mac]: https://docs.docker.com/docker-for-mac/ "Docker for Mac"
[letsencrypt]: https://letsencrypt.org
[whibox-contest]: https://whibox.io/contests/
[stefan]: https://kste.dk/
