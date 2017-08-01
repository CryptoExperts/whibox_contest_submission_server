.PHONY: machines swarm-init

clean:
	find . -type f -name '*~' -delete
	find . -type d -name '__pycache__' | xargs rm -rf
	find . -type d -name '.DS_Store' | xargs rm -rf

#############
# VMs targets
#############

machines-and-swarm:
	/bin/bash scripts/create_machines_and_swarm.sh

machines-start:
	/bin/bash scripts/start_machines.sh

machines-stop:
	-docker stack rm dev 1>/dev/null 2>&1
	-docker stack rm prod 1>/dev/null 2>&1
	docker-machine stop node-manager
	docker-machine stop node-sandbox

clean-machines:
	-docker-machine rm -y --force node-sandbox
	-docker-machine rm -y --force node-manager


# For the rest:
# eval $(docker-machine env node-manager)
# or
# eval $(docker-machine env node-sandbox)

#################
# Volumes targets
#################

clean-volumes:
	cd volumes; rm -rf database; mkdir database
	cd volumes; rm -rf whitebox_program_uploads; mkdir whitebox_program_uploads
	cd volumes; cd whitebox_program_uploads; mkdir compilations

#############
# Dev targets
#############

copy-vendors-files-dev:
	-chmod 644 services/web-dev/static/css/bootstrap.min.css
	cp vendors/bootstrap/css/bootstrap.min.css services/web-dev/static/css/bootstrap.min.css
	chmod 444 services/web-dev/static/css/bootstrap.min.css
	-chmod 644 services/web-dev/static/css/font-awesome.min.css
	cp vendors/font-awesome/css/font-awesome.min.css services/web-dev/static/css/font-awesome.min.css
	chmod 444 services/web-dev/static/css/font-awesome.min.css
	-chmod 644 services/web-dev/static/css/metisMenu.min.css
	cp vendors/metisMenu/metisMenu.min.css services/web-dev/static/css/metisMenu.min.css
	chmod 444 services/web-dev/static/css/metisMenu.min.css
	-chmod 644 services/web-dev/static/css/sb-admin-2.min.css
	cp vendors/startbootstrap-sb-admin-2-gh-pages/dist/css/sb-admin-2.min.css services/web-dev/static/css/sb-admin-2.min.css
	chmod 444 services/web-dev/static/css/sb-admin-2.min.css
	-chmod 644 services/web-dev/static/fonts/fontawesome-webfont.eot
	cp vendors/font-awesome/fonts/fontawesome-webfont.eot services/web-dev/static/fonts/fontawesome-webfont.eot
	chmod 444 services/web-dev/static/fonts/fontawesome-webfont.eot
	-chmod 644 services/web-dev/static/fonts/fontawesome-webfont.svg
	cp vendors/font-awesome/fonts/fontawesome-webfont.svg services/web-dev/static/fonts/fontawesome-webfont.svg
	chmod 444 services/web-dev/static/fonts/fontawesome-webfont.svg
	-chmod 644 services/web-dev/static/fonts/fontawesome-webfont.ttf
	cp vendors/font-awesome/fonts/fontawesome-webfont.ttf services/web-dev/static/fonts/fontawesome-webfont.ttf
	chmod 444 services/web-dev/static/fonts/fontawesome-webfont.ttf
	-chmod 644 services/web-dev/static/fonts/fontawesome-webfont.woff
	cp vendors/font-awesome/fonts/fontawesome-webfont.woff services/web-dev/static/fonts/fontawesome-webfont.woff
	chmod 444 services/web-dev/static/fonts/fontawesome-webfont.woff
	-chmod 644 services/web-dev/static/fonts/fontawesome-webfont.woff2
	cp vendors/font-awesome/fonts/fontawesome-webfont.woff2 services/web-dev/static/fonts/fontawesome-webfont.woff2
	chmod 444 services/web-dev/static/fonts/fontawesome-webfont.woff2
	-chmod 644 services/web-dev/static/fonts/glyphicons-halflings-regular.eot
	cp vendors/bootstrap/fonts/glyphicons-halflings-regular.eot services/web-dev/static/fonts/glyphicons-halflings-regular.eot
	chmod 444 services/web-dev/static/fonts/glyphicons-halflings-regular.eot
	-chmod 644 services/web-dev/static/fonts/glyphicons-halflings-regular.svg
	cp vendors/bootstrap/fonts/glyphicons-halflings-regular.svg services/web-dev/static/fonts/glyphicons-halflings-regular.svg
	chmod 444 services/web-dev/static/fonts/glyphicons-halflings-regular.svg
	-chmod 644 services/web-dev/static/fonts/glyphicons-halflings-regular.ttf
	cp vendors/bootstrap/fonts/glyphicons-halflings-regular.ttf services/web-dev/static/fonts/glyphicons-halflings-regular.ttf
	chmod 444 services/web-dev/static/fonts/glyphicons-halflings-regular.ttf
	-chmod 644 services/web-dev/static/fonts/glyphicons-halflings-regular.woff
	cp vendors/bootstrap/fonts/glyphicons-halflings-regular.woff services/web-dev/static/fonts/glyphicons-halflings-regular.woff
	chmod 444 services/web-dev/static/fonts/glyphicons-halflings-regular.woff
	-chmod 644 services/web-dev/static/fonts/glyphicons-halflings-regular.woff2
	cp vendors/bootstrap/fonts/glyphicons-halflings-regular.woff2 services/web-dev/static/fonts/glyphicons-halflings-regular.woff2
	chmod 444 services/web-dev/static/fonts/glyphicons-halflings-regular.woff2
	-chmod 644 services/web-dev/static/js/bootstrap.min.js
	cp vendors/bootstrap/js/bootstrap.min.js services/web-dev/static/js/bootstrap.min.js
	chmod 444 services/web-dev/static/js/bootstrap.min.js
	-chmod 644 services/web-dev/static/js/dataTables.bootstrap.min.js
	cp vendors/datatables-plugins/dataTables.bootstrap.min.js services/web-dev/static/js/dataTables.bootstrap.min.js
	chmod 444 services/web-dev/static/js/dataTables.bootstrap.min.js
	-chmod 644 services/web-dev/static/js/dataTables.responsive.js
	cp vendors/datatables-responsive/dataTables.responsive.js services/web-dev/static/js/dataTables.responsive.js
	chmod 444 services/web-dev/static/js/dataTables.responsive.js
	-chmod 644 services/web-dev/static/js/excanvas.min.js
	cp vendors/flot/excanvas.min.js services/web-dev/static/js/excanvas.min.js
	chmod 444 services/web-dev/static/js/excanvas.min.js
	-chmod 644 services/web-dev/static/js/jquery.dataTables.min.js
	cp vendors/datatables/js/jquery.dataTables.min.js services/web-dev/static/js/jquery.dataTables.min.js
	chmod 444 services/web-dev/static/js/jquery.dataTables.min.js
	-chmod 644 services/web-dev/static/js/jquery.flot.js
	cp vendors/flot/jquery.flot.js services/web-dev/static/js/jquery.flot.js
	chmod 444 services/web-dev/static/js/jquery.flot.js
	-chmod 644 services/web-dev/static/js/jquery.flot.resize.js
	cp vendors/flot/jquery.flot.resize.js services/web-dev/static/js/jquery.flot.resize.js
	chmod 444 services/web-dev/static/js/jquery.flot.resize.js
	-chmod 644 services/web-dev/static/js/jquery.flot.time.js
	cp vendors/flot/jquery.flot.time.js services/web-dev/static/js/jquery.flot.time.js
	chmod 444 services/web-dev/static/js/jquery.flot.time.js
	-chmod 644 services/web-dev/static/js/jquery.min.js
	cp vendors/jquery/jquery.min.js services/web-dev/static/js/jquery.min.js
	chmod 444 services/web-dev/static/js/jquery.min.js
	-chmod 644 services/web-dev/static/js/metisMenu.min.js
	cp vendors/metisMenu/metisMenu.min.js services/web-dev/static/js/metisMenu.min.js
	chmod 444 services/web-dev/static/js/metisMenu.min.js
	-chmod 644 services/web-dev/static/js/sb-admin-2.min.js
	cp vendors/startbootstrap-sb-admin-2-gh-pages/dist/js/sb-admin-2.min.js services/web-dev/static/js/sb-admin-2.min.js
	chmod 444 services/web-dev/static/js/sb-admin-2.min.js

copy-common-app-dev-files:
	-chmod 644 services/launcher-dev/app/models/program.py
	cp services/web-dev/app/models/program.py services/launcher-dev/app/models/program.py
	chmod 400 services/launcher-dev/app/models/program.py
	-chmod 644 services/launcher-dev/app/models/user.py
	cp services/web-dev/app/models/user.py services/launcher-dev/app/models/user.py
	chmod 400 services/launcher-dev/app/models/user.py
	-chmod 644 services/launcher-dev/app/models/whiteboxbreak.py
	cp services/web-dev/app/models/whiteboxbreak.py services/launcher-dev/app/models/whiteboxbreak.py
	chmod 400 services/launcher-dev/app/models/whiteboxbreak.py
	-chmod 644 services/launcher-dev/app/funny_name_generator.py
	cp services/web-dev/app/funny_name_generator.py services/launcher-dev/app/funny_name_generator.py
	chmod 400 services/launcher-dev/app/funny_name_generator.py

build-dev: copy-vendors-files-dev copy-common-app-dev-files
	docker build -t crx/mysql services/mysql/
	docker build -t crx/nginx services/nginx/
	docker build -t crx/web-dev services/web-dev/dockerfile/
	docker build -t crx/launcher-dev services/launcher-dev/dockerfile/
	/bin/bash scripts/on_node-sandbox.sh docker build -t crx/compile_and_test services/compile_and_test/

build-dev-no-cache: copy-vendors-files-dev copy-common-app-dev-files
	docker build --no-cache -t crx/mysql services/mysql/
	docker build --no-cache -t crx/nginx services/nginx/
	docker build --no-cache -t crx/web-dev services/web-dev/dockerfile/
	docker build --no-cache -t crx/launcher-dev services/launcher-dev/dockerfile/
	/bin/bash scripts/on_node-sandbox.sh docker build --no-cache -t crx/compile_and_test services/compile_and_test/

stack-deploy-dev: copy-vendors-files-dev copy-common-app-dev-files
	docker stack deploy -c docker-stack-dev.yml dev

stack-rm-dev:
	docker stack rm dev

stack-reload-dev: copy-vendors-files-dev copy-common-app-dev-files
	-docker stack rm dev
	/bin/bash scripts/wait_for_empty_docker_ps.sh
	docker stack deploy -c docker-stack-dev.yml dev

##############
# Prod targets
##############

clean-prod:
	-find services/web-prod/app -type f -exec chmod 777 {} +
	-rm -rf services/web-prod/app
	-find services/web-prod/static -type f -exec chmod 777 {} +
	-rm -rf services/web-prod/static
	-find services/launcher-prod/app -type f -exec chmod 777 {} +
	-rm -rf services/launcher-prod/app

copy-files-from-dev-to-prod: clean clean-prod copy-vendors-files-dev copy-common-app-dev-files
	cp -r services/web-dev/app services/web-prod/
	find services/web-prod/app -type f -exec chmod 444 {} +
	cp -r services/web-dev/static services/web-prod/
	find services/web-prod/static -type f -exec chmod 444 {} +
	cp -r services/launcher-dev/app services/launcher-prod/
	find services/launcher-prod/app -type f -exec chmod 444 {} +

build-prod: copy-files-from-dev-to-prod
	docker build -t crx/mysql services/mysql/
	docker build -t crx/nginx services/nginx/
	docker build -t crx/web-prod services/web-prod/
	docker build -t crx/launcher-prod services/launcher-prod/
	/bin/bash scripts/on_node-sandbox.sh docker build -t crx/compile_and_test services/compile_and_test/

build-prod-no-cache: copy-files-from-dev-to-prod
	docker build --no-cache -t crx/mysql services/mysql/
	docker build --no-cache -t crx/nginx services/nginx/
	docker build --no-cache -t crx/web-prod services/web-prod/
	docker build --no-cache -t crx/launcher-prod services/launcher-prod/
	/bin/bash scripts/on_node-sandbox.sh docker build --no-cache -t crx/compile_and_test services/compile_and_test/

stack-deploy-prod:
	docker stack deploy -c docker-stack-prod.yml prod

stack-rm-prod:
	docker stack rm prod

stack-reload-prod:
	-docker stack rm prod
	/bin/bash scripts/wait_for_empty_docker_ps.sh
	docker stack deploy -c docker-stack-prod.yml prod
