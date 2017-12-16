.PHONY: all test dist upload clean doc

all_languages ?= python,ruby,shell

all:
	echo "Usage: make test|dist|upload|clean|deps|travistest"
	exit 1

deps:
	pip install pexpect

test:
	@python r.py -f -l python byexample/*.py
	@python r.py -f -l $(all_languages) README.rst
	@python r.py -f -l $(all_languages) --skip docs/how_to_extend.rst -- `find docs -name "*.rst"`
	@python r.py -f -l python docs/how_to_extend.rst

testquick:
	@python r.py -f -l python byexample/modules/python.py
	@python r.py -f -l ruby   byexample/modules/ruby.py
	@python r.py -f -l shell  byexample/modules/shell.py

dist:
	rm -Rf dist/ build/ *.egg-info
	python setup.py sdist bdist_wheel --universal
	rm -Rf build/ *.egg-info

upload: dist
	twine upload dist/*.tar.gz dist/*.whl

doc:
	pandoc -s -o doc.pdf docs/overview.rst docs/languages/*

clean:
	rm -Rf dist/ build/ *.egg-info
	rm -Rf build/ *.egg-info
	find . -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -f doc.pdf
