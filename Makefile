.PHONY: all test dist upload clean doc

all:
	echo "Usage: make test|dist|upload|clean|deps|travistest"
	exit 1

deps:
	pip install pexpect

test:
	@python r.py -f -l python byexample/*.py
	@python r.py -f ${interpreters} README.rst
	@python r.py -f ${interpreters} `find docs -name "*.rst"`

testquick:
	@python r.py -f -l python byexample/interpreters/python.py
	@python r.py -f -l ruby   byexample/interpreters/ruby.py
	@python r.py -f -l shell  byexample/interpreters/shell.py

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
