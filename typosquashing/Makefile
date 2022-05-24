python_bin ?= python

all:
	@exit 1

dist:
	rm -Rf dist/ build/ *.egg-info
	$(python_bin) setup.py sdist bdist_wheel
	rm -Rf build/ *.egg-info

upload: dist
	twine upload dist/*.tar.gz dist/*.whl
