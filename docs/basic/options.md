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

## Show all the options

You can know what options are available for a given language running the help
integrated in ``byexample``.

For ``Python`` you could do:

```shell
$ byexample -l python --show-options
byexample's options
-------------------
optional arguments:
  +fail-fast            if an example fails, fail and stop all the execution.
  +norm-ws              ignore the amount of whitespaces.
  <...>
python's specific options
-------------------------
optional arguments:
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

The only convention that you need to follow is to write one option
per line and use ``=`` for the arguments.

```shell
$ cat test/ds/options_file
-l=python
--options="+norm-ws"
```

Then load it with ``@`` and the file; you can use multiple files
and combine them with more options from the command line:

```shell
$ byexample @test/ds/options_file test/ds/python-tutorial.v2.md
<...>
File test/ds/python-tutorial.v2.md, 4/4 test ran in <...> seconds
[PASS] Pass: 4 Fail: 0 Skip: 0
```

