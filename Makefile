.PHONY: all test lib-test docs-test modules-test travis-test coverage dist upload clean doc deps

python_bin ?= python
pretty ?= all
languages ?= python,shell,ruby,gdb,cpp

all:
	@echo "Usage: make deps|meta-test|test|quick-test|dist|upload|doc|clean"
	@echo " - deps: install the dependencies for byexample"
	@echo " - test: run the all the tests and validate the byexample's output."
	@echo " - travis-test: run the all the tests (tweaked for Travis CI)."
	@echo " - docs-test: run the tests in the docs."
	@echo " - lib-test: run the tests in the lib (unit test)."
	@echo " - modules-test: run the tests of the modules (unit test)."
	@echo " - coverage: run the all the tests under differnet envs to measure the coverage."
	@echo " - dist: make a source and a binary distribution (package)"
	@echo " - upload: upload the source and the binary distribution to pypi"
	@echo " - clean: restore the environment"
	@exit 1

deps:
	pip install -e .

test:
	@mkdir -p w
	@$(python_bin) r.py --timeout 60 --pretty $(pretty) --ff -l shell test/test.md
	@make -s clean_test

lib-test:
	@mkdir -p w
	@$(python_bin) r.py --pretty $(pretty) --ff -l python byexample/*.py

modules-test:
	@mkdir -p w
	@$(python_bin) r.py --pretty $(pretty) --ff -l $(languages) byexample/modules/*.py

docs-test:
	@mkdir -p w
	@$(python_bin) r.py --pretty $(pretty) --ff -l $(languages) *.md
	@$(python_bin) r.py --pretty $(pretty) --ff -l $(languages) --skip docs/huff/usage.md -- `find docs -name "*.md"`

travis-test: lib-test modules-test docs-test
	@# run the test separately so we can control which languages will
	@# be used. In a Travis CI environment,  Ruby, GDB and C++ are
	@# not supported
	@make -s clean_test

coverage:
	@rm -f .coverage
	@mkdir -p w
	@echo "Run the byexample's tests with the Python interpreter."
	@echo "to start the coverage, use a hook in test/ to initialize the coverage"
	@echo "engine at the begin of the execution (and to finalize it at the end)"
	@$(python_bin) r.py --modules test/ -q --ff -l python byexample/*.py
	@echo
	@echo "Run the rest of the tests with an environment variable to make"
	@echo "r.py to initialize the coverage too"
	@BYEXAMPLE_COVERAGE_TEST=1 $(python_bin) r.py -q --ff -l $(languages) `find docs -name "*.md"`
	@BYEXAMPLE_COVERAGE_TEST=1 $(python_bin) r.py -q --ff -l $(languages) *.md
	@echo
	@echo "Run again, but with different flags to force the"
	@echo "execution of different parts of byexample"
	@BYEXAMPLE_COVERAGE_TEST=1 BYEXAMPLE_PROGRESS_ASCII=1 $(python_bin) r.py -vvvvvvvvvvvv --ff --no-enhance-diff -l python,shell README.md > /dev/null
	@BYEXAMPLE_COVERAGE_TEST=1 $(python_bin) r.py --pretty none -vvvvvvvvvvvv --ff -l python,shell README.md > /dev/null
	@echo
	@echo "Results:"
	@coverage report --omit=byexample/huff.py
	@make -s clean_test

dist:
	rm -Rf dist/ build/ *.egg-info
	$(python_bin) setup.py sdist bdist_wheel --universal
	rm -Rf build/ *.egg-info

upload: dist
	twine upload dist/*.tar.gz dist/*.whl

clean_test:
	rm -f blog-101-python-tutorial.md wiki-about-license.doc license.doc
	rm -f param-echo.exe param-echo.c
	rm -f w

clean: clean_test
	rm -Rf dist/ build/ *.egg-info
	rm -Rf build/ *.egg-info
	find . -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -f README.rst
