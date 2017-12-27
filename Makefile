.PHONY: all test dist upload clean doc

python_bin ?= python
pretty ?= all

all:
	@echo "Usage: make deps|meta-test|test|quick-test|dist|upload|doc|clean"
	@echo " - deps: install the dependencies for byexample"
	@echo " - test: run the all the tests and validate the byexample's output."
	@echo " - travis-test: run the all the tests (tweaked for Travis CI)."
	@echo " - dist: make a source and a binary distribution (package)"
	@echo " - upload: upload the source and the binary distribution to pypi"
	@echo " - doc: build a pdf file from the documentation"
	@echo " - clean: restore the environment"
	@exit 1

deps:
	pip install -e .

test:
	@$(python_bin) r.py --timeout 60 --pretty $(pretty) --ff -l shell test/test.rst

travis-test:
	@# run the test separately so we can control which languages will
	@# be used. In a Travis CI environment, the Ruby and the GDB are
	@# not supported
	@$(python_bin) r.py --pretty $(pretty) --ff -l python byexample/*.py
	@$(python_bin) r.py --pretty $(pretty) --ff -l python,shell byexample/modules/*.py
	@$(python_bin) r.py --pretty $(pretty) --ff -l python,shell README.rst
	@$(python_bin) r.py --pretty $(pretty) --ff -l python,shell `find docs -name "*.rst"`

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
