export PATH := venv/bin/:$(PATH)
all: venv

venv:
	virtualenv -p python3.6 venv
	pip install -r requirements-dev.txt -r requirements.txt -e .
	pre-commit install --install-hooks

.PHONY: clean
clean:
	rm -rf venv
	find . -name '*.pyc' -delete

.PHONY: test
test: venv
	pre-commit run --all-files
	pytest tests
	pylint devdocs_cli tests
