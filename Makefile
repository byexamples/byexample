.PHONY: all test dist upload clean

all:
	echo "Usage: make test|dist|upload|clean|deps|travistest"
	exit 1

deps:
	pip install pexpect

test:
	@python r.py -f -i python byexample/*.py
	@python r.py -f ${interpreters} README.rst
	@python r.py -f ${interpreters} `find docs -name "*.rst"`

dist:
	rm -Rf dist/ build/ *.egg-info
	python setup.py sdist bdist_wheel --universal
	rm -Rf build/ *.egg-info

upload: dist
	twine upload dist/*.tar.gz dist/*.whl

clean:
	rm -Rf dist/ build/ *.egg-info
	rm -Rf build/ *.egg-info
	find . -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
