# ``byexample`` tests

## Unit tests

The source code of ``byexample`` has some runnable documentation.
If you want to know how ``byexample`` works, it is the best place
to start.

```shell
$ pretty=none make lib-test         # byexample: +rm=~ +timeout=60 +diff=ndiff
<...>
File byexample/differ.py, 17/17 test ran in <...> seconds
[PASS] Pass: 17 Fail: 0 Skip: 0
~
File byexample/expected.py, 95/95 test ran in <...> seconds
[PASS] Pass: 95 Fail: 0 Skip: 0
~
File byexample/finder.py, 77/77 test ran in <...> seconds
[PASS] Pass: 77 Fail: 0 Skip: 0
~
File byexample/options.py, 64/64 test ran in <...> seconds
[PASS] Pass: 64 Fail: 0 Skip: 0
~
File byexample/parser.py, 132/132 test ran in <...> seconds
[PASS] Pass: 132 Fail: 0 Skip: 0
<...>


```

Then, each module (Finder, Parser and Runner) provided by ``byexample`` has
a little documentation and tests as well.

```shell
$ pretty=none make modules-test         # byexample: +rm=~ +timeout=60 +diff=ndiff
<...>
File byexample/modules/cpp.py, 2/2 test ran in <...> seconds
[PASS] Pass: 2 Fail: 0 Skip: 0
~
File byexample/modules/gdb.py, 2/2 test ran in <...> seconds
[PASS] Pass: 2 Fail: 0 Skip: 0
~
File byexample/modules/python.py, 3/3 test ran in <...> seconds
[PASS] Pass: 3 Fail: 0 Skip: 0
~
File byexample/modules/ruby.py, 15/15 test ran in <...> seconds
[PASS] Pass: 15 Fail: 0 Skip: 0
~
File byexample/modules/shell.py, 3/3 test ran in <...> seconds
[PASS] Pass: 3 Fail: 0 Skip: 0
<...>


```

## Integration tests

If what you are looking for is what is capable of, you definetly need
to see the README.md and the rest of the documentation in ``docs/``

```shell
$ pretty=none make docs-test         # byexample: +rm=~ +timeout=60 +diff=ndiff
<...>
File CONTRIBUTING.md, 5/5 test ran in <...> seconds
[PASS] Pass: 0 Fail: 0 Skip: 5
~
File README.md, 9/9 test ran in <...> seconds
[PASS] Pass: 7 Fail: 0 Skip: 2
~
File docs/how_to_support_new_finders_and_languages.md, 41/41 test ran in <...> seconds
[PASS] Pass: 41 Fail: 0 Skip: 0
~
File docs/index.md, 9/9 test ran in <...> seconds
[PASS] Pass: 7 Fail: 0 Skip: 2
~
File docs/where_should_I_write_the_examples.md, 9/9 test ran in <...> seconds
[PASS] Pass: 9 Fail: 0 Skip: 0
~
File docs/languages/cpp.md, 3/3 test ran in <...> seconds
[PASS] Pass: 3 Fail: 0 Skip: 0
~
File docs/languages/gdb.md, 9/9 test ran in <...> seconds
[PASS] Pass: 9 Fail: 0 Skip: 0
~
File docs/languages/ruby.md, 17/17 test ran in <...> seconds
[PASS] Pass: 17 Fail: 0 Skip: 0
~
File docs/languages/python.md, 41/41 test ran in <...> seconds
[PASS] Pass: 40 Fail: 0 Skip: 1
~
File docs/languages/shell.md, 30/30 test ran in <...> seconds
[PASS] Pass: 30 Fail: 0 Skip: 0
~
File docs/usage.md, 44/44 test ran in <...> seconds
[PASS] Pass: 43 Fail: 0 Skip: 1
~
File docs/differences.md, 12/12 test ran in <...> seconds
[PASS] Pass: 12 Fail: 0 Skip: 0
~
File docs/how_to_hook_to_events_with_concerns.md, 2/2 test ran in <...> seconds
[PASS] Pass: 2 Fail: 0 Skip: 0
<...>


```

## Coverage tests

```shell
$ pretty=none make coverage         # byexample: +rm=~
<...>
Run the byexample's tests with the Python interpreter.
to start the coverage, use a hook in test/ to initialize the coverage
engine at the begin of the execution (and to finalize it at the end)
~
Run the rest of the tests with an environment variable to make
r.py to initialize the coverage too
~
Run again, but with different flags to force the
execution of different parts of byexample
~
<...>

```
