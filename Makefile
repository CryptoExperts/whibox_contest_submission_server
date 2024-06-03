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
	-/bin/bash scripts/on_node-manager.sh docker stack rm dev 1>/dev/null 2>&1
	-/bin/bash scripts/on_node-manager.sh docker stack rm prod 1>/dev/null 2>&1
	docker-machine stop node-manager-ecdsa || true
	VBoxManage startvm node-manager-ecdsa --type emergencystop || true
	docker-machine stop node-sandbox-ecdsa || true
	VBoxManage startvm node-sandbox-ecdsa --type emergencystop || true

clean-machines:
	-docker-machine rm -y --force node-sandbox-ecdsa
	-docker-machine rm -y --force node-manager-ecdsa


# For the rest:
# eval $(docker-machine env node-manager-ecdsa)
# or
# eval $(docker-machine env node-sandbox-ecdsa)

#################
# Volumes targets
#################

clean-volumes:
	mkdir -p volumes; cd volumes; rm -rf database; mkdir database
	cd volumes; rm -rf whitebox_program_uploads; mkdir whitebox_program_uploads
	cd volumes; cd whitebox_program_uploads; mkdir compilations

clean-node-volumes:
	docker-machine ssh node-manager-ecdsa rm -rf /volumes/databases/*
	docker-machine ssh node-manager-ecdsa rm -rf /volumes/whitebox_program_uploads/compilations/*
	

#############
# Dev targets
#############

define copy-single-vendors-file-dev
	@printf "copy from $(1) to $(2)\n"
	@-chmod 644 $(2)
	@cp $(1) $(2)
	@chmod 444 $(2)
endef

# Regenerate the minified CSS files
regen-vendors:
	cleancss vendors/startbootstrap-sb-admin-2-gh-pages/css/sb-admin-2.css > vendors/startbootstrap-sb-admin-2-gh-pages/css/sb-admin-2.min.css

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
	$(call copy-single-vendors-file-dev,vendors/js.cookie-2.2.1.min.js,services/web-dev/static/js/js.cookie.min.js)

# copy images
	$(call copy-single-vendors-file-dev,vendors/startbootstrap-sb-admin-2-gh-pages/img/undraw_profile.svg,services/web-dev/static/images/undraw_profile.svg)

# copy flot
	$(call copy-single-vendors-file-dev,vendors/flot/jquery.flot.js,services/web-dev/static/js/jquery.flot.js)
	$(call copy-single-vendors-file-dev,vendors/flot/jquery.flot.resize.js,services/web-dev/static/js/jquery.flot.resize.js)
	$(call copy-single-vendors-file-dev,vendors/flot/jquery.flot.time.js,services/web-dev/static/js/jquery.flot.time.js)

# copy dataTable
	$(call copy-single-vendors-file-dev,vendors/startbootstrap-sb-admin-2-gh-pages/vendor/datatables/dataTables.bootstrap4.min.css,services/web-dev/static/css/dataTables.bootstrap4.min.css)
	$(call copy-single-vendors-file-dev,vendors/startbootstrap-sb-admin-2-gh-pages/vendor/datatables/dataTables.bootstrap4.min.js,services/web-dev/static/js/dataTables.bootstrap4.min.js)
	$(call copy-single-vendors-file-dev,vendors/startbootstrap-sb-admin-2-gh-pages/vendor/datatables/jquery.dataTables.min.js,services/web-dev/static/js/jquery.dataTables.min.js)


	# cp vendors/datatables-responsive/dataTables.responsive.js services/web-dev/static/js/dataTables.responsive.js

update_submodule:
	git submodule init && git submodule update --remote --merge

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
	/bin/bash scripts/on_node-manager.sh docker build -t crx/web-dev services/web-dev/dockerfile/
	/bin/bash scripts/on_node-manager.sh docker build -t crx/launcher-dev services/launcher-dev/dockerfile/
	/bin/bash scripts/on_node-sandbox.sh docker build -t crx/alpine_with_compilers services/alpine_with_compilers/
	/bin/bash scripts/on_node-sandbox.sh docker build -t crx/compile_and_test services/compile_and_test/

build-dev-no-cache: copy-vendors-files-dev copy-common-app-dev-files
	/bin/bash scripts/on_node-manager.sh docker build --no-cache -t crx/web-dev services/web-dev/dockerfile/
	/bin/bash scripts/on_node-manager.sh docker build --no-cache -t crx/launcher-dev services/launcher-dev/dockerfile/
	/bin/bash scripts/on_node-sandbox.sh docker build --no-cache -t crx/alpine_with_compilers services/alpine_with_compilers/
	/bin/bash scripts/on_node-sandbox.sh docker build --no-cache -t crx/compile_and_test services/compile_and_test/

stack-deploy-dev: copy-vendors-files-dev copy-common-app-dev-files
	/bin/bash scripts/on_node-manager.sh docker stack deploy -c docker-stack-dev.yml dev

stack-rm-dev:
	/bin/bash scripts/on_node-manager.sh docker stack rm dev

stack-reload-dev: copy-vendors-files-dev copy-common-app-dev-files
	-/bin/bash scripts/on_node-manager.sh docker stack rm dev
	/bin/bash scripts/on_node-manager.sh /bin/bash scripts/wait_for_empty_docker_ps.sh
	/bin/bash scripts/on_node-manager.sh docker stack deploy -c docker-stack-dev.yml dev

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
	/bin/bash scripts/on_node-manager.sh docker build -t crx/web-prod services/web-prod/
	/bin/bash scripts/on_node-manager.sh docker build -t crx/launcher-prod services/launcher-prod/
	/bin/bash scripts/on_node-sandbox.sh docker build -t crx/alpine_with_compilers services/alpine_with_compilers/
	/bin/bash scripts/on_node-sandbox.sh docker build -t crx/compile_and_test services/compile_and_test/

backup-images:
	/bin/bash scripts/on_node-manager.sh docker save crx/web-dev > backups/images/web-dev.backup
	/bin/bash scripts/on_node-manager.sh docker save crx/web-prod > backups/images/web-prod.backup
	/bin/bash scripts/on_node-manager.sh docker save crx/launcher-dev > backups/images/launcher-dev.backup
	/bin/bash scripts/on_node-manager.sh docker save crx/launcher-prod > backups/images/launcher-prod.backup

restore-images:
	/bin/bash scripts/on_node-manager.sh docker load -i backups/images/web-dev.backup
	/bin/bash scripts/on_node-manager.sh docker load -i backups/images/web-prod.backup
	/bin/bash scripts/on_node-manager.sh docker load -i backups/images/launcher-dev.backup
	/bin/bash scripts/on_node-manager.sh docker load -i backups/images/launcher-prod.backup


build-prod-no-cache: copy-files-from-dev-to-prod
	/bin/bash scripts/on_node-manager.sh docker build --no-cache -t crx/web-prod services/web-prod/
	/bin/bash scripts/on_node-manager.sh docker build --no-cache -t crx/launcher-prod services/launcher-prod/
	/bin/bash scripts/on_node-sandbox.sh docker build --no-cache -t crx/alpine_with_compilers services/alpine_with_compilers/
	/bin/bash scripts/on_node-sandbox.sh docker build --no-cache -t crx/compile_and_test services/compile_and_test/

stack-deploy-prod:
	/bin/bash scripts/on_node-manager.sh docker stack deploy -c docker-stack-prod.yml prod

stack-rm-prod:
	/bin/bash scripts/on_node-manager.sh docker stack rm prod

stack-reload-prod:
	-/bin/bash scripts/on_node-manager.sh docker stack rm prod
	/bin/bash scripts/on_node-manager.sh /bin/bash scripts/wait_for_empty_docker_ps.sh
	/bin/bash scripts/on_node-manager.sh docker stack deploy -c docker-stack-prod.yml prod

#### For logging
dev-web-logs:
	/bin/bash scripts/on_node-manager.sh docker service logs -f dev_web

dev-launcher-logs:
	/bin/bash scripts/on_node-manager.sh docker service logs -f dev_launcher

dev-db-logs:
	/bin/bash scripts/on_node-manager.sh docker service logs -f dev_mysql

prod-web-logs:
	/bin/bash scripts/on_node-manager.sh docker service logs -f prod_web

prod-launcher-logs:
	/bin/bash scripts/on_node-manager.sh docker service logs -f prod_launcher

prod-db-logs:
	/bin/bash scripts/on_node-manager.sh docker service logs -f prod_mysql

compiler-logs:
	cat volumes/whitebox_program_uploads/compilations/logs/*/*.logs

## Interactions with the MySQL database:
# Get a shell
db-shell:
	scripts/on_node-manager.sh scripts/db-shell.sh

# Print all the programs important information
db-dump-programs:
	scripts/on_node-manager.sh scripts/db-shell.sh "select _id, _funny_name, _basename, _user_id, _timestamp_submitted, _timestamp_published, _timestamp_first_break, _status, _task_id, _timestamp_compilation_start, _timestamp_compilation_finished, _error_message, _pubkey, _proof_of_knowledge from program;"

# Remove a specific program by its id
db-remove-program:
ifneq ($(PROGRAM_TO_DELETE),)
	@echo -n "You asked to remove program $(PROGRAM_TO_DELETE): this is DANGEROUS, are you sure? [y/N] " && read ans && [ $${ans:-N} = y ]
	@echo -n "You asked to remove program $(PROGRAM_TO_DELETE): this is DANGEROUS, are you REALLY sure? [y/N] " && read ans && [ $${ans:-N} = y ]
	scripts/on_node-manager.sh scripts/db-shell.sh "DELETE from program WHERE _id=$(PROGRAM_TO_DELETE);"
else
	@echo "Please export the program to deleted: 'PROGRAM_TO_DELETE=XXX make db-remove-program'"
endif

# Remove all the programs
db-remove-program-all:
	@echo -n "You asked to remove all the programs: this is DANGEROUS, are you sure? [y/N] " && read ans && [ $${ans:-N} = y ]
	@echo -n "You asked to remove all the programs: this is DANGEROUS, are you REALLY sure? [y/N] " && read ans && [ $${ans:-N} = y ]
	scripts/on_node-manager.sh scripts/db-shell.sh "DELETE from program;"

# Save (dump) the database
db-backup:
	BACKUP_FILE=backup_wb_db_`date +%s`.sql && scripts/on_node-manager.sh scripts/db-backup.sh $$BACKUP_FILE && echo "[+] Saved DB to $$BACKUP_FILE"

# Restore the database
db-restore:
ifneq ($(DB_TO_RESTORE),)
	@echo -n "You asked to restore the database $(DB_TO_RESTORE): this is DANGEROUS, are you sure? [y/N] " && read ans && [ $${ans:-N} = y ]
	@echo -n "You asked to restore the database $(DB_TO_RESTORE): this is DANGEROUS, are you REALLY sure? [y/N] " && read ans && [ $${ans:-N} = y ]
	scripts/on_node-manager.sh scripts/db-restore.sh $(DB_TO_RESTORE)
else
	@echo "Please export the SQL database file to be restored: 'DB_TO_RESTORE=XXX.sql make db-restore'"
endif


# Remove a specific user by his id (first remove all his programs, then remove him)
db-remove-userid:
ifneq ($(USERID_TO_DELETE),)
	@echo -n "You asked to remove user id $(USERID_TO_DELETE): this will remove the user and all his programs! This is DANGEROUS, are you sure? [y/N] " && read ans && [ $${ans:-N} = y ]
	@echo -n "You asked to remove user id $(USERID_TO_DELETE): this will remove the user and all his programs! This is DANGEROUS, are you REALLY sure? [y/N] " && read ans && [ $${ans:-N} = y ]
	scripts/on_node-manager.sh scripts/db-shell.sh "DELETE from program WHERE _user_id=$(USERID_TO_DELETE);"
	scripts/on_node-manager.sh scripts/db-shell.sh "DELETE from user WHERE _id='$(USERID_TO_DELETE)';"
else
	@echo "Please export the user id to deleted: 'USERID_TO_DELETE=XXX make db-remove-userid'"
endif

# Print all users ID, names and nickames
db-dump-users:
	scripts/on_node-manager.sh scripts/db-shell.sh "select _id, _username, _nickname, _email from user;"

db-mysqlcheck:
	scripts/on_node-manager.sh scripts/db-mysqlcheck.sh

db-mysqlrepair:
	scripts/on_node-manager.sh scripts/db-mysqlrepair.sh
