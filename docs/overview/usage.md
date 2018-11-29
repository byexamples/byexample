<!--
Check that we have byexample installed first
$ hash byexample                                    # byexample: +fail-fast

$ alias byexample=byexample\ --pretty\ none

--
-->

# Usage

Imagine that you are creating a 101 ``Python`` tutorial and you want to explain
the basics of the language writing a blog.

So you open your favorite editor, write some comments, you enhance them with
real ``Python`` examples and you get something like this:

```
$ cat test/ds/python-tutorial.v1.md               # byexample: +rm=~
This is a 101 Python tutorial
The following is an example written in Python about arithmetics
~
~    >>> from __future__ import print_function
~    >>> 1 + 2
~    3
~
The next examples show you about complex numbers in Python
~
~    >>> 2j * 2
~    4
~
~    >>> 2j + 4j
~    6
~
```

Now we want to be sure that the examples in the blog are correct.

Just run ``byexample`` selecting ``python`` as the language target

```
$ byexample -l python test/ds/python-tutorial.v1.md
<...>
Failed example:
    2j * 2
<...>
Expected:
4
Got:
4j
<...>
File test/ds/python-tutorial.v1.md, 4/4 test ran in <...> seconds
[FAIL] Pass: 2 Fail: 2 Skip: 0
```

``byexample`` will show the differences for each failing test and at the end
will print a summary showing how many examples were executed, how many passed,
failed or where skipped.

In normal circumstances there are two possible status: ``PASS`` and ``FAIL``.

If something strange happen like the user pressed ``ctrl-c``, the underlying
runner crashed or an example couldn't get parsed, the status will be ``ABORT``.

For quick regression you may want to stop ``byexample`` at the first failing
example using ``--ff`` or ``--fail-fast`` to skip all the remaining examples.

```
$ byexample --ff -l python test/ds/python-tutorial.v1.md
<...>
File test/ds/python-tutorial.v1.md, 4/4 test ran in <...> seconds
[FAIL] Pass: 2 Fail: 1 Skip: 1
```

Fix the bugs an re-run

```
$ byexample --ff -l python test/ds/python-tutorial.v2.md
<...>
File test/ds/python-tutorial.v2.md, 4/4 test ran in <...> seconds
[PASS] Pass: 4 Fail: 0 Skip: 0
```

## Help included

The help included in ``byexample`` should give you a quick overview of its
capabilities

```
$ byexample -h                                          # byexample: +norm-ws
usage: <byexample> [-h] [-V] [--ff] [--dry] [--skip file [file ...]] [-m dir]
            [-d {none,unified,ndiff,context}] [--no-enhance-diff] -l language
            [--timeout TIMEOUT] [-o OPTIONS_STR] [--show-options]
            [--encoding ENCODING] [--pretty {none,all}]
            [--shebang runner:shebang] [-j JOBS] [-v | -q]
            [file [file ...]]
positional arguments:
  file                  file that have the examples to run.
optional arguments:
  -h, --help            show this help message and exit
  -V, --version         show <...> version and license, then exit
  --ff, --fail-fast     if an example fails, fail and stop all the execution.
  --dry                 do not run any example, only parse them.
  --skip file [file ...]
                        skip these files
  -m dir, --modules dir
                        append a directory for searching modules there.
  -d {none,unified,ndiff,context}, --diff {none,unified,ndiff,context}
                        select diff algorithm.
  --no-enhance-diff     by default, improves are made so the diff are easier
                        to to understand: non-printable characters are
                        visible; captured string shown, and more; this flag
                        disables all of that.
  -l language, --language language
                        select which languages to parse and run. Comma
                        separated syntax is also accepted.
  --timeout TIMEOUT     timeout in seconds to complete each example (2 by
                        default); this can be changed per example with this
                        option.
  -o OPTIONS_STR, --options OPTIONS_STR
                        add additional options; see --show-options to list
                        them.
  --show-options        show the available options for the selected languages
                        (with -l)
  --encoding ENCODING   select the encoding; use the same encoding of stdout
                        by default)
  --pretty {none,all}   control how to pretty print the output.
  --shebang runner:shebang
                        change the command line of the given <runner> by
                        <shebang>; the tokens %e %p %a are replaced by the
                        default values for environment, program name, and
                        arguments (however no all the runners will honor this
                        and some may break).
  -j JOBS, --jobs JOBS  run <jobs> in parallel (1 default); "cpu" means use
                        all the cpus available; "cpu<...>" multiply it by <n>
                        the cpus available.
  -v                    verbosity level, add more flags to increase the level.
  -q, --quiet           quiet mode, do not print anything even if an example
                        fails; supress the progress output.
```
