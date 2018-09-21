export PATH := venv/bin/:$(PATH)
all: venv

venv:
	tox -e venv
	pre-commit install --install-hooks

.PHONY: clean
clean:
	rm -rf venv
	find . -name '*.pyc' -delete

.PHONY: test
test:
	tox
