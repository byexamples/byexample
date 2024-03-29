<!--
Check that we have byexample installed first
$ hash byexample                                    # byexample: +fail-fast

$ alias byexample=byexample\ --pretty\ none

--
-->

# Options

You can control certain behaviours of the examples through a set of
options.

If the option is set per example using ``byexample: <opt>``, it will affect only
that example.

```python
>>> list(range(10))             # byexample: +norm-ws
[0,  1,  2,  3,  4,
 5,  6,  7,  8,  9]
```

If the option is set in the command line using ``-o <opt>``, it will affect all
the examples.

```shell
$ byexample -l python -o "+norm-ws" test/ds/python-tutorial.v2.md
<...>
File test/ds/python-tutorial.v2.md, 4/4 test ran in <...> seconds
[PASS] Pass: 4 Fail: 0 Skip: 0
```

If the option begins with `-`, `byexample` may get confuse and it will
complain that no argument was given to `--options`:

```shell
$ byexample -l python -o -warn-tab test/ds/example-with-tabs-in-code.md
<...>
byexample: error: argument -o/--options: expected one argument
If you wrote --options -foo, try put an equal like --options=-foo
and use quotes if you want to set multiples options like --options='-foo +bar'
```

The error is because `byexample` presumes that `-warn-tab` is another
command line flag like `-l` and `-o` and not the argument for `-o`.

As the error message suggests you can workaround this *joining* `-o`
with its argument with an `=`:

```shell
$ byexample -l python -o=-warn-tab test/ds/example-with-tabs-in-code.md
<...>
File test/ds/example-with-tabs-in-code.md, <...>
[PASS] Pass: 1 Fail: 0 Skip: 0
```

If you need to pass multiple options to `-o` you can quote them together:

```shell
$ byexample -l python -o='-warn-tab +norm-ws' test/ds/example-with-tabs-in-code.md
<...>
File test/ds/example-with-tabs-in-code.md, <...>
[PASS] Pass: 1 Fail: 0 Skip: 0
```

## Show all the options

You can know what options are available for a given language running the help
integrated in ``byexample``.

For ``Python`` you could do:

```shell
$ byexample -l python --show-options
byexample's options
-------------------
<...>:
  +fail-fast            if an example fails, fail and stop all the execution.
  +norm-ws              ignore the amount of whitespaces.
  <...>
python's specific options
-------------------------
<...>
  +py-doctest           enable the compatibility with doctest.
  +py-pretty-print      enable the pretty print enhancement.
  <...>
```

There is a set of common options supplied by ``byexample`` and can be
used in any example.

Other languages and concerns may add their owns.

## Loading options from a file

If the amount of options is a little overwhelming for you, you can
write them down to a file and let ``byexample`` load them for you.

The only convention that you need to follow is to write **one** option
per line. If the option receives one argument you can separate them by
`=` or by a space but if there is more than one argument you will have
to write the option and the arguments one by one in its own line.

```shell
$ cat test/ds/options_file
# Options and their arguments are separated by a = or by a space
-l python
--options=+norm-ws
<...>
# But if the option receives more than one argument, all of them
# must be in its own line
--skip
test/ds/pkg/foo1.py
test/ds/pkg/foo2.py
<...>
# This wouldn't work:
#--skip test/ds/pkg/foo1.py test/ds/pkg/foo2.py
```

Then load it with ``@`` and the file; you can use multiple files
and combine them with more options from the command line:

```shell
$ byexample @test/ds/options_file -- test/ds/python-tutorial.v2.md
<...>
File test/ds/python-tutorial.v2.md, 4/4 test ran in <...> seconds
[PASS] Pass: 4 Fail: 0 Skip: 0
```

> **Note:** before `10.5.2` the options in the file required to be followed by an
> `=` like `-l=python`; spaces were not allowed.

## File pattern expansions

Consider the following:

```shell
$ byexample -l python test/ds/pkg/*.py | grep pkg | sort    # byexample: +timeout=8
File test/ds/pkg/bar1.py, 1/1 test ran in <...> seconds
File test/ds/pkg/foo1.py, 1/1 test ran in <...> seconds
File test/ds/pkg/foo2.py, 1/1 test ran in <...> seconds
```

Your *shell* usually expands `test/ds/pkg/*.py` into a list of files:
`test/ds/pkg/bar1.py`, `test/ds/pkg/foo1.py` and `test/ds/pkg/foo2.py`

The same happens with the argument list for `--skip`, it is expanded by
your *shell*.

```shell
$ byexample -l python --skip test/ds/pkg/foo* -- test/ds/pkg/*.py | grep pkg | sort    # byexample: +timeout=8
File test/ds/pkg/bar1.py, 1/1 test ran in <...> seconds
```

Since `10.0.3`, `byexample` does the same *glob expansion* even if you shell does not.
This is in particular useful if the list of files is in a file (where your shell
never ever see).

```shell
$ cat test/ds/pkg/bopts
--skip=test/ds/pkg/foo*.py
--
test/ds/pkg/*.py

$ byexample -l python @test/ds/pkg/bopts | grep pkg | sort    # byexample: +timeout=8
File test/ds/pkg/bar1.py, 1/1 test ran in <...> seconds
```

Since `11.0.0`, `byexample` also does the so called *brace expansion*:

```shell
$ cat test/ds/pkg/bopts-brace
--skip=test/ds/pkg/foo{1..2}.py
--
test/ds/pkg/*.{py,md}

$ byexample -l python @test/ds/pkg/bopts-brace | grep pkg | sort    # byexample: +timeout=8
File test/ds/pkg/bar1.py, 1/1 test ran in <...> seconds
File test/ds/pkg/zaz.md, 1/1 test ran in <...> seconds
```

The following is a handy example for selecting all the Python files at
any depth in the folder tree:

```shell
$ byexample -l python cryptonita{,/**}/*.py     # byexample: +skip
```

The `cryptonita{,/**}/*.py` looks magic but it says: search for any
`cryptonita/*.py` and any `cryptonita/**/*.py`. The former are all the
`.py` files in the folder `cryptonita` and the latter are all the `.py`
in any sub folder.


## Arguments per environment

If you run you tests under different environments and you need to pass
different options in each one, you may benefit of writing a *single*
argument file to work as a template and use a template engine like
[Jinja2](https://jinja.palletsprojects.com/en/3.1.x/) to generate
different argument files based on the environment.

This is probably a real exotic super-advanced use of `byexample` but
it may save you some typing! Check the
[recipe]({{ site.uprefix }}/recipes/arguments-per-environment)
for a full example.


<!--

Extra test checking that options in a file with multiple spaces are
interpreted correctly now that we support separate the flag from its
value with a space (before an '=' was always required)

So the following lines are equivalent
    -skip=foo bar
    -skip foo bar

$ cat test/ds/pkg/bopts2
<...>skip
test/ds/pkg/foo1.py
test/ds/pkg/foo2.py
<...>

More extra tests to ensure that no file is missing

$ byexample -l python @test/ds/pkg/bopts2 | grep pkg | wc -l | xargs   # byexample: +timeout=8
1

$ cat test/ds/pkg/bopts3
<...>skip=test/ds/pkg/foo1.py test/ds/pkg/foo2.py
<...>

$ byexample -l python @test/ds/pkg/bopts2 | grep pkg | wc -l | xargs    # byexample: +timeout=8
1

$ byexample -l python @test/ds/pkg/bopts | grep pkg | wc -l | xargs     # byexample: +timeout=8
1

$ byexample -l python @test/ds/pkg/bopts-brace | grep pkg | wc -l | xargs  # byexample: +timeout=8
2

-->
