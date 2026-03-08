.PHONY: venv install run clean

venv:
	@test -d .venv || python -m venv .venv

install: venv
	.venv/bin/python -m pip install -r requirements.txt

run:
	.venv/bin/python cide.py

run-debug:
	.venv/bin/python cide.py --debug 

tree:
	tree --gitignore > tree_project.txt