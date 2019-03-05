# ``byexample`` tests

## Unit tests

The source code of ``byexample`` has some runnable documentation.
If you want to know how ``byexample`` works, it is the best place
to start.

```shell
$ jobs=1 pretty=none make lib-test         # byexample: +rm=~ +timeout=60 +diff=ndiff
<...>
File byexample/cache.py, 11/11 test ran in <...> seconds
[PASS] Pass: 11 Fail: 0 Skip: 0
~
File byexample/common.py, 11/11 test ran in <...> seconds
[PASS] Pass: 11 Fail: 0 Skip: 0
~
File byexample/differ.py, 23/23 test ran in <...> seconds
[PASS] Pass: 23 Fail: 0 Skip: 0
~
File byexample/expected.py, 95/95 test ran in <...> seconds
[PASS] Pass: 95 Fail: 0 Skip: 0
~
File byexample/finder.py, 45/45 test ran in <...> seconds
[PASS] Pass: 45 Fail: 0 Skip: 0
~
File byexample/options.py, 64/64 test ran in <...> seconds
[PASS] Pass: 64 Fail: 0 Skip: 0
~
File byexample/parser.py, 26/26 test ran in <...> seconds
[PASS] Pass: 26 Fail: 0 Skip: 0
~
File byexample/parser_sm.py, 129/129 test ran in <...> seconds
[PASS] Pass: 129 Fail: 0 Skip: 0
<...>
```

Then, each module (Finder, Parser and Runner) provided by ``byexample`` has
a little documentation and tests as well.

```shell
$ jobs=1 pretty=none make modules-test         # byexample: +rm=~ +timeout=60 +diff=ndiff
<...>
File byexample/modules/cpp.py, 6/6 test ran in <...> seconds
[PASS] Pass: 6 Fail: 0 Skip: 0
~
File byexample/modules/gdb.py, 3/3 test ran in <...> seconds
[PASS] Pass: 3 Fail: 0 Skip: 0
~
File byexample/modules/javascript.py, 5/5 test ran in <...> seconds
[PASS] Pass: 5 Fail: 0 Skip: 0
~
File byexample/modules/python.py, 5/5 test ran in <...> seconds
[PASS] Pass: 5 Fail: 0 Skip: 0
~
File byexample/modules/ruby.py, 11/11 test ran in <...> seconds
[PASS] Pass: 11 Fail: 0 Skip: 0
~
File byexample/modules/shell.py, 3/3 test ran in <...> seconds
[PASS] Pass: 3 Fail: 0 Skip: 0
<...>


```

## Integration tests

If what you are looking for is what is capable of, you definetly need
to see the README.md and the rest of the documentation in ``docs/``

```shell
$ jobs=1 pretty=none make docs-test         # byexample: +rm=~ +timeout=120 +diff=ndiff
<...>
File CONTRIBUTING.md, 5/5 test ran in <...> seconds
[PASS] Pass: 0 Fail: 0 Skip: 5
~
File README.md, 9/9 test ran in <...> seconds
[PASS] Pass: 7 Fail: 0 Skip: 2
~
File docs/advanced/conditional-execution.md, 8/8 test ran in <...> seconds
[PASS] Pass: 7 Fail: 0 Skip: 1
~
File docs/advanced/geometry.md, 12/12 test ran in <...> seconds
[PASS] Pass: 12 Fail: 0 Skip: 0
~
File docs/advanced/greedy-lazy-tags.md, 7/7 test ran in <...> seconds
[PASS] Pass: 7 Fail: 0 Skip: 0
~
File docs/advanced/shebang.md, 5/5 test ran in <...> seconds
[PASS] Pass: 5 Fail: 0 Skip: 0
~
File docs/advanced/terminal-emulation.md, 13/13 test ran in <...> seconds
[PASS] Pass: 13 Fail: 0 Skip: 0
~
File docs/advanced/unicode.md, 9/9 test ran in <...> seconds
[PASS] Pass: 9 Fail: 0 Skip: 0
~
File docs/basic/capture-and-paste.md, 6/6 test ran in <...> seconds
[PASS] Pass: 6 Fail: 0 Skip: 0
~
File docs/basic/normalize-whitespace.md, 3/3 test ran in <...> seconds
[PASS] Pass: 3 Fail: 0 Skip: 0
~
File docs/basic/options.md, 7/7 test ran in <...> seconds
[PASS] Pass: 7 Fail: 0 Skip: 0
~
File docs/basic/setup-and-tear-down.md, 7/7 test ran in <...> seconds
[PASS] Pass: 7 Fail: 0 Skip: 0
~
File docs/basic/skip-and-pass.md, 7/7 test ran in <...> seconds
[PASS] Pass: 6 Fail: 0 Skip: 1
~
File docs/basic/timeout.md, 7/7 test ran in <...> seconds
[PASS] Pass: 6 Fail: 0 Skip: 1
~
File docs/contrib/how-to-define-new-zones-where-to-find-examples.md, 3/3 test ran in <...> seconds
[PASS] Pass: 3 Fail: 0 Skip: 0
~
File docs/contrib/how-to-hook-to-events-with-concerns.md, 2/2 test ran in <...> seconds
[PASS] Pass: 2 Fail: 0 Skip: 0
~
File docs/contrib/how-to-support-new-finders-and-languages.md, 39/39 test ran in <...> seconds
[PASS] Pass: 39 Fail: 0 Skip: 0
~
File docs/index.md, 5/5 test ran in <...> seconds
[PASS] Pass: 3 Fail: 0 Skip: 2
~
File docs/languages/cpp.md, 8/8 test ran in <...> seconds
[PASS] Pass: 8 Fail: 0 Skip: 0
~
File docs/languages/gdb.md, 9/9 test ran in <...> seconds
[PASS] Pass: 9 Fail: 0 Skip: 0
~
File docs/languages/javascript.md, 17/17 test ran in <...> seconds
[PASS] Pass: 17 Fail: 0 Skip: 0
~
File docs/languages/python.md, 42/42 test ran in <...> seconds
[PASS] Pass: 40 Fail: 0 Skip: 2
~
File docs/languages/ruby.md, 10/10 test ran in <...> seconds
[PASS] Pass: 10 Fail: 0 Skip: 0
~
File docs/languages/shell.md, 31/31 test ran in <...> seconds
[PASS] Pass: 31 Fail: 0 Skip: 0
~
File docs/overview/differences.md, 15/15 test ran in <...> seconds
[PASS] Pass: 15 Fail: 0 Skip: 0
~
File docs/overview/faq.md, 5/5 test ran in <...> seconds
[PASS] Pass: 5 Fail: 0 Skip: 0
~
File docs/overview/usage.md, 7/7 test ran in <...> seconds
[PASS] Pass: 7 Fail: 0 Skip: 0
~
File docs/overview/where-should-I-write-the-examples.md, 14/14 test ran in <...> seconds
[PASS] Pass: 14 Fail: 0 Skip: 0
<...>

```

## Example tests

```shell
$ jobs=1 pretty=none make examples-test         # byexample: +rm=~ +timeout=60 +diff=ndiff
<...>
File docs/examples/cpp.cpp, 3/3 test ran in <...> seconds
[PASS] Pass: 3 Fail: 0 Skip: 0
~
File docs/examples/javascript.js, 3/3 test ran in <...> seconds
[PASS] Pass: 3 Fail: 0 Skip: 0
~
File docs/examples/markdown.md, 3/3 test ran in <...> seconds
[PASS] Pass: 3 Fail: 0 Skip: 0
~
File docs/examples/python.py, 3/3 test ran in <...> seconds
[PASS] Pass: 3 Fail: 0 Skip: 0
~
File docs/examples/ruby.rb, 3/3 test ran in <...> seconds
[PASS] Pass: 3 Fail: 0 Skip: 0
<...>
```

## Coverage tests

```shell
$ jobs=1 pretty=none make coverage         # byexample: +rm=~
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
