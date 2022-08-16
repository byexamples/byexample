<!--
Check that we have byexample installed first
$ hash byexample                                    # byexample: +fail-fast

$ alias byexample=byexample\ --pretty\ none

--
-->

# Frequently Asked Questions

### How to check for empty lines in the middle of the expected output?

``byexample`` uses an empty line to separate one example from the other.
If the output of your example contains such line, you need to *trick*
to ``byexample``.

Pick an unused character and use it as a glue in replace of the empty lines,
instruct to ``byexample`` to
[remove it]()
before performing the comparison and *voila*.

```python
>>> print("Line1\n\nLine3")         # byexample: +rm=~
Line1
~
Line3
```

Tip: you can use the invisible unicode character U+00A0 (` `) instead
of an `~`:

```python
>>> print("Line1\n\nLine3")         # byexample: +rm= 
Line1
 
Line3
```

And instead of typing `+rm= ` on each example, you can write it once in
the command line with [--options](/{{ site.uprefix }}/basic/options).


### How to ignore the tag ``<xxx>``?

If the output of your example has the literal ``<xxx>`` and you want
to take it *literally*, you could disable the
[tags](basic/capture-and-paste)

```python
>>> print("<a>, <a>, and <tag>")        # byexample: -tags
<a>, <a>, and <tag>

>>> print("<a>, <a>, and <tag>")        # byexample: -capture
<a>, <a>, and <tag>
```

The difference between `-tags` and `-capture` is that the former
takes the named `<foo>` and the unnamed `<...>` tags as literal
while the latter only takes the named tags as literal.


### How to escape a prompt inside of another example?

``byexample`` uses the prompts to detect examples and in which languages
are written.

It uses different heuristics to avoid false positives but it is possible
that the *output* of an example could be *confused* with another example
because it contains a prompt.

To avoid this, prefix an unused character and remove it before the comparison:

```shell
>>> print("$ this is not a 'shell' example, just the output of a python example") # byexample: +rm=~
~$ this is not a 'shell' example, just the output of a python example
```

In the example above ``$`` would be confused with the prompt of ``shell``.

Prefixing with ``~`` avoids this and the ``+rm=~`` removes it before the comparison.

### Why my ``<foo_bar>`` tag is not recognized?

Only alphabetic and numeric characters plus the minus are recognized.
An *underscore* is not.

```
bad:  <foo_bar>
good: <foo-bar>
```

Do not worry, I made this mistake a few times too.

### Check for the last line of xxx fails, why?

May be you wrote something like this?

```python
>>> print("last line\n")
last line
<...>
```

That example will work only if the line ends in a new line.

If not it will fail. To avoid that put ``<...>`` in the same line:

```python
>>> print("last line")
last line<...>
```

### Verbose mode in only one language?

The ``-v`` option puts ``byexample`` in verbose mode. More
than one ``-v`` flag can be added increasing the verbosity.

But what if you want to put in verbose mode only *one part*
of ``byexample``?

For this you need the ``-x-log-mask`` option.

For example, to put in ``'chat'`` mode only the *execution*
of Python examples you can do:

```shell
$ byexample -x-log-mask byexample.exec.python:chat -l python test/ds/db-stock-model
[i:exec.python] Initializing Python Runner
[i:exec.python] Spawn command line: /usr/bin/env python -i
[i:exec.python] Python Runner's version: <...>
[i:exec.python] example to run:
    import sqlite3
[i:exec.python] example to run:
    c = sqlite3.connect(':memory:')
[i:exec.python] example to run:
    _ = c.executescript(open('test/ds/stock.sql').read())  # ---> # byexample: +fail-fast
[i:exec.python] example to run:
<...>
File test/ds/db-stock-model, 5/5 test ran in <...>
```

### An example times out. Why?

An example will time out if the example is taking much time to complete
*or* if the interpreter hang.

A quick check would run `byexample` with a really large timeout (30
seconds to say something).

```shell
$ byexample --timeout 30 -l python test/ds/db-stock-model
<...>
File test/ds/db-stock-model, 5/5 test ran in <...>
```

If that works it means that the example is just to slow. You may want to
try to optimize it or tag it with [+timeout](/{{ site.uprefix }}/basic/timeout).

If the example *still* times out it means that or the example is
syntactically incorrect or incomplete or the interpreter hang.

The first possibility is more likely. It is when you type an example but
you miss to type a ending quote or parenthesis.

Most of the interpreters don't see this as an error
and instead assume that you are going to
type more which it is not the case. You will have to review the example
more closely.

### I cannot run a single example, `byexample` fails.

There can be a few reasons why this is happening.

The interpreter that you want to use does not exists. This could happens
because the interpreter is not in the PATH or it is not installed at
all.

```shell
$ byexample -l python -x-shebang python:python99 test/ds/db-stock-model  # byexample: +norm-ws
[w] Initialization of Python Runner failed.
[!] Something went wrong processing the file 'test/ds/db-stock-model':
The command was not found or was not executable.
The full command line tried is as follows:
 python99
This could happen because you do not have it installed or
it is not in the PATH.
<...>
```

If you are sure that the interpreter is installed, you could try to use
a [shebang](/{{ site.uprefix }}/advanced/shebang) to specify the exact
location of the binary.

Other error could be an *unexpected close*:

```shell
$ byexample -l python -x-shebang 'python:env python99' test/ds/db-stock-model   # byexample: +norm-ws
[w] Initialization of Python Runner failed.
[!] Something went wrong processing the file 'test/ds/db-stock-model':
Interpreter closed unexpectedly.
This could happen because the example triggered a close/shutdown/exit action,
the interpreter was killed by someone else or because the interpreter just crashed.
<...>
Last 1000 bytes read:
/usr/bin/env: ‘python99’: No such file or directory
<...>
```

This could happen because the binary was found but it was never ready.
In the example above, the program `env` was found and executed and in
turns executed the non-existing `python99` program.

The solution may be the same as above: check that the interpreter is
installed and in the PATH and
use [shebang](/{{ site.uprefix }}/advanced/shebang) to specify the exact
location of it if necessary.

If you want to know the exact command line used by `byexample`, you can
find it adding more verbosity:

```shell
$ byexample -l python -x-shebang 'python:env python99' -v test/ds/db-stock-model   # byexample: +norm-ws +diff=ndiff
[i] Initializing Python Runner
[i] Spawn command line: env python99
[w] Failed to obtain Python Runner's version <...>
[w] Initialization of Python Runner failed.
<...>
```

If you still have troubles then it may be a real problem. It will be
super helpful if you
[open an issue](https://github.com/byexamples/byexample/issues) with a
minimal code to exemplify the issue.

### The executed code is *echoed* in the output

`byexample` tries hard to force the interpreters to not echo the code
but sometimes is not possible.

In the following example, part of the code executed is *echoed* and
appears in the output of the example, something that it is unwanted of
course.

```python
Failed example:
    print("foo")
Expected:
foo
Got:
print("foo")
foo
```

In this case you can run `byexample` with `-o +force-echo-filtering` to
filter the unwanted strings.

See [echo-filtering](/{{ site.uprefix }}/advanced/echo-filtering) for more information.

### The executed code is outputs weird things in MacOS

`byexample 11.0.0` has a better support for MacOS but in previous
versions, `byexample` was not able to turn the echo off.

The result was that in MacOS the examples you execute are echo'ed back.

If you cannot upgrade, the only solution then is an active filter with
`-o +force-echo-filtering`. See above question and answer.

### It seems that the first lines of the output are missing

If you are using `-o +force-echo-filtering` or `+term=ansi`, the output
of your examples are passed through an
[ANSI terminal emulator](/{{ site.uprefix }}/advanced/terminal-emulation).

Like any terminal, this one has some
[geometry](/{{ site.uprefix }}/advanced/geometry)
which defines how many
lines/rows and columns the terminal has.

Anything outside will be lost.

If the first lines of the output are missing, chances are that the
example's output is so large that the terminal had to *"scroll"*.

You can change the [geometry](/{{ site.uprefix }}/advanced/geometry)
with `+geometry=LINESxCOLS`: try to
increase the amount of lines (aka, the height or rows of the terminal) so all
the output fits in the terminal.


### Example expecting ^t (tab) instead of spaces

Some editors write a few spaces when the user presses the TAB key but
some others honor the user's intention and write a literal tab.

This is hard to notice because both are non-visible characters.

When there is a mismatch due what the example prints and what the
example expects (what the user with his/her editor typed), `byexample`
will make a clear distinction for tabs, noted with the `^t` symbol:

```shell
$ byexample -l python test/ds/example-with-tabs.md
<...>
File "test/ds/example-with-tabs.md", line 3
Failed example:
    print("        <-spaces")
Some non-printable characters were replaced by printable ones.
    ^t: tab
(You can disable this with '--no-enhance-diff')
Expected:
^t<-spaces
Got:
        <-spaces
<...>
```

In the above example, the code printed spaces but the user expected
(typed) a tab.

You can confirm this reviewing the hexdecimal dump of the file:

```shell
$ hexdump -C test/ds/example-with-tabs.md
00000000  0a 60 60 60 70 79 74 68  6f 6e 0a 3e 3e 3e 20 70  |.```python.>>> p|
00000010  72 69 6e 74 28 22 20 20  20 20 20 20 20 20 3c 2d  |rint("        <-|
00000020  73 70 61 63 65 73 22 29  0a 09 3c 2d 73 70 61 63  |spaces")..<-spac|
00000030  65 73 0a 60 60 60 0a                              |es.```.|
00000037
```

### Warning about tabs in the example code that could interfere

Some interpreters/runners are sensible to the tabs in their inputs (in
the code).

In some cases the runner may output weird messages or it may even hang
(and `byexample` will then make the example fail due a timeout)

Considere the following example:

```python
>>> print("        <-this is a tab")       # byexample: +term=as-is
        <-this is a tab
```

You probably cannot see it but what the `print()` prints is a tab; perhaps
reading the hexdecimal dump is better:

```shell
$ hexdump -C test/ds/example-with-tabs-in-code.md
00000000  0a 60 60 60 70 79 74 68  6f 6e 0a 3e 3e 3e 20 70  |.```python.>>> p|
00000010  72 69 6e 74 28 22 09 3c  2d 74 68 69 73 20 69 73  |rint(".<-this is|
00000020  20 61 20 74 61 62 22 29  20 20 20 20 20 20 20 23  | a tab")       #|
00000030  20 62 79 65 78 61 6d 70  6c 65 3a 20 2b 74 65 72  | byexample: +ter|
00000040  6d 3d 61 73 2d 69 73 0a  09 3c 2d 74 68 69 73 20  |m=as-is..<-this |
00000050  69 73 20 61 20 74 61 62  0a 60 60 60 0a           |is a tab.```.|
0000005d
```

Since `11.0.0`, `byexample` will emit a warning telling you that the
code in the example has a tab.

```shell
$ byexample -l python test/ds/example-with-tabs-in-code.md
[w] The source code has a tab character that may interfere with the interpreter/runner.
You can remove the tab or disable this warning with '-warn-tab'.
<...>
    print("     <-this is a tab")       # byexample: +term=as-is
<...>
```

If you are sure that you want a tab in the code you can disable the
warning adding `-warn-tab` in the example or from the command line:

```shell
$ byexample -l python -o=-warn-tab test/ds/example-with-tabs-in-code.md
<...>
File test/ds/example-with-tabs-in-code.md, <...>
[PASS] Pass: 1 Fail: 0 Skip: 0
```

### `byexample` fails with `argument -o/--options: expected one argument`

The `-o` or `--options` expects a single argument, a string with the
[options to set](/{{ site.uprefix }}/basic/options).

You may forgot to pass it.

But probably is not the case, isn't? You may be passing an argument
like:

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
