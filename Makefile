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

define copy-single-vendors-file-dev
	@printf "copy from $(1) to $(2)\n"
	@-chmod 644 $(2)
	@cp $(1) $(2)
	@chmod 444 $(2)
endef

copy-vendors-files-dev:
# copy fonts
	$(call copy-single-vendors-file-dev,vendors/startbootstrap-sb-admin-2-gh-pages/vendor/fontawesome-free/css/all.min.css,services/web-dev/static/css/fontawesome.all.min.css)
	$(call copy-single-vendors-file-dev,vendors/startbootstrap-sb-admin-2-gh-pages/vendor/fontawesome-free/webfonts/fa-solid-900.ttf,services/web-dev/static/webfonts/fa-solid-900.ttf)
	$(call copy-single-vendors-file-dev,vendors/startbootstrap-sb-admin-2-gh-pages/vendor/fontawesome-free/webfonts/fa-solid-900.woff,services/web-dev/static/webfonts/fa-solid-900.woff)
	$(call copy-single-vendors-file-dev,vendors/startbootstrap-sb-admin-2-gh-pages/vendor/fontawesome-free/webfonts/fa-solid-900.woff2,services/web-dev/static/webfonts/fa-solid-900.woff2)

# copy css
	$(call copy-single-vendors-file-dev,vendors/startbootstrap-sb-admin-2-gh-pages/css/sb-admin-2.min.css,services/web-dev/static/css/sb-admin-2.min.css)

# copy js
	$(call copy-single-vendors-file-dev,vendors/startbootstrap-sb-admin-2-gh-pages/js/sb-admin-2.min.js,services/web-dev/static/js/sb-admin-2.min.js)
	$(call copy-single-vendors-file-dev,vendors/startbootstrap-sb-admin-2-gh-pages/vendor/bootstrap/js/bootstrap.bundle.min.js,services/web-dev/static/js/bootstrap.bundle.min.js)
	$(call copy-single-vendors-file-dev,vendors/startbootstrap-sb-admin-2-gh-pages/vendor/bootstrap/js/bootstrap.bundle.min.js.map,services/web-dev/static/js/bootstrap.bundle.min.js.map)
	$(call copy-single-vendors-file-dev,vendors/startbootstrap-sb-admin-2-gh-pages/vendor/jquery/jquery.min.js,services/web-dev/static/js/jquery.min.js)
	$(call copy-single-vendors-file-dev,vendors/startbootstrap-sb-admin-2-gh-pages/vendor/jquery-easing/jquery.easing.min.js,services/web-dev/static/js/jquery.easing.min.js)

# copy images
	$(call copy-single-vendors-file-dev,vendors/startbootstrap-sb-admin-2-gh-pages/img/undraw_profile.svg,services/web-dev/static/images/undraw_profile.svg)

# copy flot
	$(call copy-single-vendors-file-dev,vendors/flot/jquery.flot.js,services/web-dev/static/js/jquery.flot.js)
	$(call copy-single-vendors-file-dev,vendors/flot/jquery.flot.resize.js,services/web-dev/static/js/jquery.flot.resize.js)
	$(call copy-single-vendors-file-dev,vendors/flot/jquery.flot.time.js,services/web-dev/static/js/jquery.flot.time.js)

	# cp vendors/metisMenu/metisMenu.min.css services/web-dev/static/css/metisMenu.min.css
	# cp vendors/datatables-plugins/dataTables.bootstrap.min.js services/web-dev/static/js/dataTables.bootstrap.min.js
	# cp vendors/datatables-responsive/dataTables.responsive.js services/web-dev/static/js/dataTables.responsive.js
	# cp vendors/datatables/js/jquery.dataTables.min.js services/web-dev/static/js/jquery.dataTables.min.js
	# cp vendors/metisMenu/metisMenu.min.js services/web-dev/static/js/metisMenu.min.js

update_submodule:
	git submodule init && git submodule update

copy-common-app-dev-files: update_submodule
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
	docker build -t crx/web-dev services/web-dev/dockerfile/
	docker build -t crx/launcher-dev services/launcher-dev/dockerfile/
	/bin/bash scripts/on_node-sandbox.sh docker build -t crx/alpine_with_compilers services/alpine_with_compilers/
	/bin/bash scripts/on_node-sandbox.sh docker build -t crx/compile_and_test services/compile_and_test/

build-dev-no-cache: copy-vendors-files-dev copy-common-app-dev-files
	docker build --no-cache -t crx/nginx services/nginx/
	docker build --no-cache -t crx/web-dev services/web-dev/dockerfile/
	docker build --no-cache -t crx/launcher-dev services/launcher-dev/dockerfile/
	/bin/bash scripts/on_node-sandbox.sh docker build --no-cache -t crx/alpine_with_compilers services/alpine_with_compilers/
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
	docker build -t crx/web-prod services/web-prod/
	docker build -t crx/launcher-prod services/launcher-prod/
	/bin/bash scripts/on_node-sandbox.sh docker build -t crx/alpine_with_compilers services/alpine_with_compilers/
	/bin/bash scripts/on_node-sandbox.sh docker build -t crx/compile_and_test services/compile_and_test/

backup-images:
	docker save crx/web-dev > backups/images/web-dev.backup
	docker save crx/web-prod > backups/images/web-prod.backup
	docker save crx/launcher-dev > backups/images/launcher-dev.backup
	docker save crx/launcher-prod > backups/images/launcher-prod.backup

restore-images:
	docker load -i backups/images/web-dev.backup
	docker load -i backups/images/web-prod.backup
	docker load -i backups/images/launcher-dev.backup
	docker load -i backups/images/launcher-prod.backup


build-prod-no-cache: copy-files-from-dev-to-prod
	docker build --no-cache -t crx/web-prod services/web-prod/
	docker build --no-cache -t crx/launcher-prod services/launcher-prod/
	/bin/bash scripts/on_node-sandbox.sh docker build --no-cache -t crx/alpine_with_compilers services/alpine_with_compilers/
	/bin/bash scripts/on_node-sandbox.sh docker build --no-cache -t crx/compile_and_test services/compile_and_test/

stack-deploy-prod:
	docker stack deploy -c docker-stack-prod.yml prod

stack-rm-prod:
	docker stack rm prod

stack-reload-prod:
	-docker stack rm prod
	/bin/bash scripts/wait_for_empty_docker_ps.sh
	docker stack deploy -c docker-stack-prod.yml prod
