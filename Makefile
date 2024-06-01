#* Variables
SHELL := /usr/bin/env bash
PYTHON := python
PYTHONPATH := `pwd`

#* Docker variables
IMAGE := fsri_mcc
VERSION := latest

.ONESHELL:
USING_HATCH		          	=	$(shell grep "tool.hatch" pyproject.toml && echo "yes")
ENV_PREFIX		        	=.venv/bin/
VENV_EXISTS           		=	$(shell python3 -c "if __import__('pathlib').Path('.venv/bin/activate').exists(): print('yes')")
SRC_DIR               		=src
BUILD_DIR             		=dist

install-pipx: 										## Install pipx
	@python3 -m pip install --upgrade --user pipx

install-hatch: 										## Install Hatch, UV, and Ruff
	@pipx install hatch --force
	@pipx inject hatch ruff uv hatch-pip-compile hatch-vcs hatch-mypyc mypy --include-deps --include-apps --force

upgrade-hatch: 										## Update Hatch, UV, and Ruff
	@pipx upgrade hatch --include-injected

install:											## Install the project and
	@if [ "$(VENV_EXISTS)" ]; then echo "=> Removing existing virtual environment"; $(MAKE) destroy-venv; fi
	@$(MAKE) clean
	@if ! pipx --version > /dev/null; then echo '=> Installing `pipx`'; $(MAKE) install-pipx ; fi
	@if ! hatch --version > /dev/null; then echo '=> Installing `hatch` with `pipx`'; $(MAKE) install-hatch ; fi
	@if ! hatch-pip-compile --version > /dev/null; then echo '=> Updating `hatch` and installing plugins'; $(MAKE) upgrade-hatch ; fi
	@echo "=> Install complete! Note: If you want to re-install re-run 'make install'"

.PHONY: pre-commit-install
pre-commit-install:
	poetry run pre-commit install

.PHONY: lint
lint: 												## Runs pre-commit hooks; includes ruff linting, codespell, black
	@echo "=> Running pre-commit process"
	@hatch run pre-commit run --all-files
	@echo "=> Pre-commit complete"

.PHONY: format
format: 												## Runs code formatting utilities
	@echo "=> Running pre-commit process"
	@hatch run ruff check . --fix
	@echo "=> Pre-commit complete"

.PHONY: coverage
coverage:  											## Run the tests and generate coverage report
	@echo "=> Running tests with coverage"
	@hatch run pytest tests --cov=app
	@hatch run coverage html
	@hatch run coverage xml
	@echo "=> Coverage report generated"

.PHONY: test
test:  												## Run the tests
	@echo "=> Running test cases"
	@hatch run pytest tests
	@echo "=> Tests complete"

#* Cleaning
.PHONY: pycache-remove
pycache-remove:
	find . | grep -E "(__pycache__|\.pyc|\.pyo$$)" | xargs rm -rf

.PHONY: dsstore-remove
dsstore-remove:
	find . | grep -E ".DS_Store" | xargs rm -rf

.PHONY: mypycache-remove
mypycache-remove:
	find . | grep -E ".mypy_cache" | xargs rm -rf

.PHONY: ipynbcheckpoints-remove
ipynbcheckpoints-remove:
	find . | grep -E ".ipynb_checkpoints" | xargs rm -rf

.PHONY: pytestcache-remove
pytestcache-remove:
	find . | grep -E ".pytest_cache" | xargs rm -rf

.PHONY: build-remove
build-remove:
	rm -rf build/

.PHONY: cleanup
cleanup: pycache-remove dsstore-remove mypycache-remove ipynbcheckpoints-remove pytestcache-remove
