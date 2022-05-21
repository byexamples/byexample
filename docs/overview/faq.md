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
ex:
    import sqlite3
ex:
    c = sqlite3.connect(':memory:')
ex:
    _ = c.executescript(open('test/ds/stock.sql').read())  # ---> # byexample: +fail-fast
ex:
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

This is particular true in MacOS.

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

See above.

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

