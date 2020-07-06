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

### How to ignore the capture tag ``<xxx>``?

If the output of your example has the literal ``<xxx>`` and you want
to take it *literally*, you could disable the
[capture tags](basic/capture-and-paste)

```python
>>> print("<a>, <b>, and <tag>")        # byexample: -tags
<a>, <b>, and <tag>
```

### How to escape a prompt inside of another example?

``byexample`` uses the prompts to detect examples and in which langueges
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
