.PHONY: all test lib-test docs-test modules-test coverage dist upload clean doc deps

python_bin ?= python
pretty ?= all
languages ?= python,shell
pip_bin ?= pip

docker_priv ?= --cap-add=SYS_PTRACE

all:
	@echo "Usage: make deps[-dev]"
	@echo " - deps: install the dependencies for run byexample"
	@echo " - deps-dev: install the dependencies for run and build byexample"
	@echo
	@echo "Usage: make test"
	@echo "Run all the suite of tests using only Python and Shell."
	@echo
	@echo "Usage: make [lib|modules|docs|examples|corner]-test"
	@echo "Run a suite of tests. We assume a minimum environment where"
	@echo "only Python and Shell are available and therefor we run only"
	@echo "a large but not complete subset of tests."
	@echo "Modify test/minumum.env to add more languages if you have"
	@echo "installed them or to add/modify custom flags."
	@echo " - lib-test: run the tests in the lib (unit test)."
	@echo " - modules-test: run the tests of the modules (unit test)."
	@echo " - docs-test: run the tests in the docs (except docs about languages)."
	@echo " - examples-test: run the examples."
	@echo " - corner-test: run some tests that are corner cases."
	@echo
	@echo "Usage: make [lib]-profiler-[1|2|4]"
	@echo "Run a suite of tests with the profiler enabled with 1, 2 or 4 jobs"
	@echo "The traces will be in prof-traces. See the results with flamegraph as"
	@echo "  cat prof-traces | ./flamegraph.pl > prof.svg"
	@echo
	@echo "Usage: make docker-test"
	@echo "Run the suite of tests of the modules and examples and a few"
	@echo "others using all the languages available inside a docker"
	@echo "container where all the interpreters are installed."
	@echo "Modify test/docker.env to modify the flags of the execution."
	@echo "This should complement the suite of tests executed by 'make test'"
	@echo
	@echo "Usage: make lang-<lang>-test"
	@echo "Run a small suite of tests using <lang> and Shell as the only"
	@echo "interpreters. Designed to be executed in the CI environment"
	@echo
	@echo "Usage: make docker-[build|shell]"
	@echo "Create the docker image (build) used by the tests or run a"
	@echo "container and get a shell (shell) to play with it."
	@echo
	@echo "Usage: make dist|upload"
	@echo "Package byexample (dist) and upload it to pypi (upload)"
	@echo
	@echo "Usage: make format[-test]"
	@echo "Format the source code following the PEP 8 style."
	@echo "Use format-test to verify the complaince without touching"
	@echo "the code"
	@echo
	@echo "Usage: make coverage"
	@echo "Run several times variants of 'make test' with the coverage"
	@echo "activated and show the results."
	@echo
	@echo "Usage: make clean|clean_test"
	@echo "Clean the environment in general (clean) or only related"
	@echo "with the environment for testing (clean_test)."
	@exit 1

deps:
	$(pip_bin) install -e .

deps-dev:
	$(pip_bin) install -r requirements-dev.txt

private-all-test: clean_test
	@$(python_bin) -W error test/r.py --timeout 90 --pretty $(pretty) --ff -l shell test/test.md
	@make -s clean_test

## Python + Shell tests only
#  =========================
lib-test: clean_test
	@$(python_bin) -W error  test/r.py @test/minimum.env -- byexample/*.py
	@make -s clean_test

filter-echo-tagging-test: clean_test
	@$(python_bin) -W error  test/r.py @test/filter-echo-tagging.env -- byexample/*.py
	@make -s clean_test

corner-test: clean_test
	@$(python_bin) -W error  test/r.py @test/corner.env -- test/corner_cases.md
	@make -s clean_test

timming-corner-test: clean_test
	@$(python_bin) -W error  test/r.py @test/corner.env -- test/timming_corner_cases.md
	@make -s clean_test

modules-test: clean_test
	@$(python_bin) -W error  test/r.py @test/minimum.env -- byexample/modules/*.py
	@make -s clean_test

docs-test: clean_test
	@$(python_bin) -W error  test/r.py @test/minimum.env -- *.md
	@$(python_bin) -W error  test/r.py @test/minimum.env --skip docs/advanced/echo-filtering.md docs/recipes/python-doctest.md -- `find docs \( -name languages -prune -o  -name "*.md" \) -type f`
	@$(python_bin) -W error  test/r.py -l shell --pretty=all --ff --timeout 4 -x-turn-echo-off no docs/advanced/echo-filtering.md
	@$(python_bin) -W error  test/r.py @test/minimum.env -o '+py-doctest' docs/recipes/python-doctest.md
	@$(python_bin) -m doctest docs/recipes/python-doctest.md
	@$(python_bin) -W error  test/r.py @test/minimum-term-ansi.env -- test/ds/terminal-ansi-unicode.md
	@make -s clean_test

examples-test: clean_test
	@$(python_bin) -W error  test/r.py @test/minimum.env -- docs/examples/*
	@make -s clean_test

index-links-test: clean_test
	@echo "Running index-links-test"
	@./test/idx.sh

version-test:
	@$(python_bin) -W error  test/r.py @test/minimum.env test/consistent-version.md

test: lib-test modules-test docs-test examples-test index-links-test corner-test timming-corner-test

#
##

## Performance
#  ===========
lib-profiler-1: clean_test
	@echo "Running profile"
	@BYEXAMPLE_PROFILE=1 $(python_bin) test/r.py --jobs 1 @test/profiler.env -- byexample/*.py > prof-traces
	@make -s clean_test

lib-profiler-2: clean_test
	@echo "Running profile"
	@BYEXAMPLE_PROFILE=1 $(python_bin) test/r.py --jobs 2 @test/profiler.env -- byexample/*.py > prof-traces
	@make -s clean_test

lib-profiler-4: clean_test
	@echo "Running profile"
	@BYEXAMPLE_PROFILE=1 $(python_bin) test/r.py --jobs 4 @test/profiler.env -- byexample/*.py > prof-traces
	@make -s clean_test
#
##

## Tests for specific interpreters to be used in CI
#  ================================================
lang-ruby-test: clean_test
	@$(python_bin) -W error  test/r.py @test/lang-ruby.env

lang-python-test: clean_test
	@$(python_bin) -W error  test/r.py @test/lang-python.env

lang-shell-test: clean_test
	@$(python_bin) -W error  test/r.py @test/lang-shell.env

lang-iasm-test: clean_test
	@$(python_bin) -W error  test/r.py @test/lang-iasm.env

lang-pwsh-test: clean_test
	@$(python_bin) -W error  test/r.py @test/lang-powershell.env

lang-cpp-test: clean_test
	@$(python_bin) -W error  test/r.py @test/lang-cpp.env

lang-gdb-test: clean_test
	@$(python_bin) -W error  test/r.py @test/lang-gdb.env

lang-javascript-test: clean_test
	@$(python_bin) -W error  test/r.py @test/lang-javascript.env

lang-go-test: clean_test
	@$(python_bin) -W error  test/r.py @test/lang-go.env

lang-rust-test: clean_test
	@$(python_bin) -W error  test/r.py @test/lang-rust.env

lang-java-test: clean_test
	@$(python_bin) -W error  test/r.py @test/lang-java.env

# not supported
lang-elixir-test: clean_test
	@$(python_bin) -W error  test/r.py @test/lang-elixir.env

# not supported
lang-php-test: clean_test
	@$(python_bin) -W error  test/r.py @test/lang-php.env
#
##

## Docker manager
#  ==============

# Docker image build for running the full suite of tests
docker-build:
	@sudo docker build -q -t byexample-test -f test/Dockerfile .

# Drop an interactive shell inside the docker
docker-shell: docker-build
	@sudo docker run $(docker_priv) -it --rm -v `pwd`:/srv -w /srv byexample-test bash

#
##

## Tests for specific interpreters to be used in the docker container
#  ==================================================================

# Run the tests where other languages than Python and Shell are used
# inside the docker where all the interpreters are installed
docker-test: docker-build
	@sudo docker run $(docker_priv) -it --rm -v `pwd`:/srv -w /srv byexample-test bash -c 'pip3 install -e . && byexample @test/docker.env -- byexample/modules/*.py docs/languages/*.md docs/examples/* docs/advanced/{geometry,terminal-emulation}.md ;  byexample @test/docker.no-python-shell.env -- docs/basic/input.md ; make -s clean_test'

#
##

## Coverage
#  ========

coverage: clean_test
	rm -f .coverage .coverage.work.*
	@cp test/r.py .
	@echo "Run the byexample's tests with the Python interpreter."
	@echo "to start the coverage, use a hook in test/ to initialize the coverage"
	@echo "engine at the begin of the execution (and to finalize it at the end)"
	$(python_bin) r.py @test/coverage.env --modules test/ -q byexample/*.py
	@echo
	@echo "Run the rest of the tests with an environment variable to make"
	@echo "r.py to initialize the coverage too"
	BYEXAMPLE_COVERAGE_TEST=1 $(python_bin) r.py @test/coverage.env -q `find docs -name "*.md"`
	BYEXAMPLE_COVERAGE_TEST=1 $(python_bin) r.py @test/coverage.env -q *.md
	@echo
	@echo "Run again, but with different flags to force the"
	@echo "execution of different parts of byexample"
	PYTHONIOENCODING=utf-8 BYEXAMPLE_COVERAGE_TEST=1 $(python_bin) r.py @test/coverage.env -vvvvvvvvvvvv --no-enhance-diff README.md > /dev/null
	PYTHONIOENCODING=utf-8 BYEXAMPLE_COVERAGE_TEST=1 $(python_bin) r.py @test/coverage.env --pretty none -vvvvvvvvvvvv README.md > /dev/null
	@echo
	@echo "Results:"
	coverage report --include="byexample/*"

#
##

## Formatting
#  ==========

format:
	yapf -vv -i --style=.style.yapf --recursive byexample/

format-test:
	yapf -vv --style=.style.yapf --diff --recursive byexample/
#
##

## Packaging and clean up
#  ======================

generate-autocomplete:
	register-python-argcomplete --no-defaults -s bash byexample > autocomplete/autocomplete_bash

dist:
	rm -Rf dist/ build/ *.egg-info
	$(python_bin) setup.py sdist bdist_wheel
	rm -Rf build/ *.egg-info

install-from-pkg-wheel: dist
	@pip uninstall -y byexample || true
	pip install dist/byexample-*.whl

install-from-pkg-tgz: dist
	@pip uninstall -y byexample || true
	pip install dist/byexample-*.tar.gz

upload: dist version-test
	twine upload dist/*.tar.gz dist/*.whl

# Describe the HEAD and if it is not a tag, fail; othewise get
# the annotation of the tag and ensure that the indentation is removed
# from it (tail + sed) and then create a Github release with that.
release:
	gh auth status
	@X=`git describe --exact-match HEAD` && ( git tag -n1000 "$$X" | tail -n +3 | sed 's/^[[:blank:]]\{,4\}\(.*\)$$/\1/' | tee .release-notes | gh release create --generate-notes "$$X" --notes-file - )
	@cat .release-notes

runner-version-matrix:
	gh auth status
	@X=`gh run list --repo byexamples/byexample --workflow test --limit 1 | awk '{print $$(NF-2)}'` && gh run view --repo byexamples/byexample --log "$$X" > .workflow-log
	@python test/runner_version_matrix.py .workflow-log

clean_test:
	@rm -f r.py
	@rm -Rf w/
	@mkdir -p w/

clean: clean_test
	rm -f .coverage .coverage.work.* .release-notes .workflow-log
	rm -Rf dist/ build/ *.egg-info
	rm -Rf build/ *.egg-info
	find . -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -f README.rst prof-traces

#
##
