.PHONY : build doc doc-meta install repo vision-files


build :
	scripts/build.sh repo vision-file
	scripts/install_py_extensions.bash
	scripts/repair.sh


doc :
	python3 scripts/build-complete-doc.py


doc-meta :
	python3 scripts/build-meta-doc.py


install: pull-all vision-files
	scripts/install_dependencies.sh
	scripts/create_catkin_workspace.sh


pull-all:
	git pull
	scripts/pull_all.sh
	scripts/pull_files.bash


vision-files:
	scripts/pull_files.bash


