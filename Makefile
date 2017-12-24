.PHONY: all test dist upload clean doc

all_languages ?= python,ruby,shell
python_bin ?= python
pretty ?= all

all:
	@echo "Usage: make deps|meta-test|test|quick-test|dist|upload|doc|clean"
	@echo " - deps: install the dependencies for byexample"
	@echo " - test: run the all the tests and validate the byexample's output."
	@echo " - dist: make a source and a binary distribution (package)"
	@echo " - upload: upload the source and the binary distribution to pypi"
	@echo " - doc: build a pdf file from the documentation"
	@echo " - clean: restore the environment"
	@exit 1

deps:
	pip install pexpect

test:
	@$(python_bin) r.py --timeout 60 --pretty $(pretty) --ff -l shell test/test.rst

dist:
	rm -Rf dist/ build/ *.egg-info
	$(python_bin) setup.py sdist bdist_wheel --universal
	rm -Rf build/ *.egg-info

upload: dist
	twine upload dist/*.tar.gz dist/*.whl

doc:
	pandoc -s -o doc.pdf docs/overview.rst docs/languages/* docs/how_to_extend.rst

clean:
	rm -Rf dist/ build/ *.egg-info
	rm -Rf build/ *.egg-info
	find . -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -f doc.pdf
