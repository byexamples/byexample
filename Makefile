.PHONY: all test dist upload clean doc

all_languages ?= python,ruby,shell
python_bin ?= python
colors ?=

all:
	@echo "Usage: make deps|meta-test|test|quick-test|dist|upload|doc|clean"
	@echo " - deps: install the dependencies for byexample"
	@echo " - test: run the all the tests and validate the byexample's output."
	@echo " - full-test: run the all the tests in the source code and documentation"
	@echo " - quick-test: run a few tests in the source code of the modules"
	@echo " - dist: make a source and a binary distribution (package)"
	@echo " - upload: upload the source and the binary distribution to pypi"
	@echo " - doc: build a pdf file from the documentation"
	@echo " - clean: restore the environment"
	@exit 1

deps:
	pip install pexpect

test: quick-test full-test
	# run the test again, this time validate the byexample's output itself
	@$(python_bin) r.py $(colors) -f -l shell test/meta-test.rst

full-test:
	@$(python_bin) r.py $(colors) -f -l python byexample/*.py
	@$(python_bin) r.py $(colors) -f -l $(all_languages) README.rst
	@$(python_bin) r.py $(colors) -f -l $(all_languages) --skip docs/how_to_extend.rst -- `find docs -name "*.rst"`
	@$(python_bin) r.py $(colors) -f -l python docs/how_to_extend.rst

quick-test:
	@$(python_bin) r.py $(colors) -f -l python byexample/modules/python.py
	@$(python_bin) r.py $(colors) -f -l ruby   byexample/modules/ruby.py
	@$(python_bin) r.py $(colors) -f -l shell  byexample/modules/shell.py
	@$(python_bin) r.py $(colors) -f -l gdb    byexample/modules/gdb.py

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
