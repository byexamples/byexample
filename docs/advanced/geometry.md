<!--
Check that we have byexample installed first
$ hash byexample                                    # byexample: +fail-fast

$ alias byexample=byexample\ --pretty\ none

--
-->

# Terminal Geometry

When ``byexample`` runs a set of examples, it spawns one or more runners
inside a [virtual terminal](/{{ site.uprefix }}/advanced/terminal-emulation)
that is 24 lines high and 80 columns wide.

The dimension or geometry can affect how the runner will print in the
terminal.

Consider the following ``Python`` examples that show a short and a long
list of numbers:

```python
>>> list(range(10))
[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

>>> list(range(25))
[0,
 1,
<...>
 24]
```

``Python``'s pretty printer prints the first in one line because its width is
less than 80; the second example, longer than the first, will span multiple
lines.

``byexample`` allows you to control the geometry of the *virtual terminal*:

```python
>>> list(range(25))     # byexample: +geometry 24x127
[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, <...>, 20, 21, 22, 23, 24]
```

The syntax is simply ``<number of lines>x<number of columns>``

## A warning note

Changing the geometry of the *virtual terminal* is **totally dependent**
on the runner/interpreter used.

By default ``byexample`` sends a ``SIGWINCH`` signal to the interpreter
which may or may not have an effect.

In addition to that, for ``Python``, its pretty printer is modified too.

<!--

Hide these examples/tests from the user: they don't add too much
value but they are here because is a simple way that a change
in the geometry doesn't break anything even if the interpreter
decide to ignore the change.

Python:
>>> 1 + 2   # byexample: +geometry 24x60
3

Shell:
$ echo 1    # byexample: +geometry 24x60
1

Ruby:
>> 1 + 2    # byexample: +geometry 24x60
=> 3

C++:
?: 1 + 2      // byexample: +geometry 24x60
(int) 3

PHP
php> echo 1 + 2;      // byexample: +geometry 24x60
3

Javascript:
> 1 + 2    // byexample: +geometry 24x60
3

GDB:
(gdb) help help  # byexample: +geometry 24x60
Print list of commands.
-->

## Changing geometry from the start

You may decide to set the geometry from the beginning. In this
case it will affect all the interpreters.

Consider the examples in ``small-terminal.md``

```shell
$ byexample -l python,shell test/ds/small-terminal.md
<...>
File "test/ds/small-terminal.md", line 2
Failed example:
    echo ${LINES}x${COLUMNS}
Expected:
24x60
Got:
24x80
<...>
File "test/ds/small-terminal.md", line 6
Failed example:
    ['aaaaa', 'aaaaa', 'aaaaa', 'aaaaa', 'aaaaa', 'aaaaa', 'aaaaa']
Expected:
['aaaaa',
 'aaaaa',
 'aaaaa',
<...>
 'aaaaa']
Got:
['aaaaa', 'aaaaa', 'aaaaa', 'aaaaa', 'aaaaa', 'aaaaa', 'aaaaa']
<...>
```

They fail because the examples are expecting to be executed
in a smaller terminal of size 24x60.

Here we have them pass:

```shell
$ byexample -l python,shell -o '+geometry 24x60' test/ds/small-terminal.md
<...>
File test/ds/small-terminal.md, 2/2 test ran in <...> seconds
[PASS] Pass: 2 Fail: 0 Skip: 0
```

``byexample`` will pass the geometry to the runner in two special environment
variables: ``LINES`` and ``COLUMNS``.

This is only done at the beginning, if you change the geometry later these
variables may not be updated.
