# Python

``byexample`` supports ``Python``.

I'm assuming that you have ``Python`` installed in your system as ``byexample``
needs it to run but just in case, this is the [download page](https://www.python.org/downloads/)
for this interpreter.

## Find interactive examples

For ``Python``, ``byexample`` uses the ``>>>`` string as the primary and ``...``
as the secondary prompts.

```python
>>> def f():
...    return 42

>>> f()
42
```

## Compatibility with ``doctest``

In fact, ``byexample`` is inspired by the Python's ``doctest`` module.

I borrowed a few ideas from it and I also tried to overcome its issues.

This makes a Python example to look very similar to a doctest but it is not
fully compatible with it.

To make it (almost) fully compatible, you need to pass the ``+py-doctest`` flag to
``byexample`` in the command line.

In the following examples I will pass this flag in the examples themselves.

If you enabled the compatibility from the command line, *nothing* needs to be
changed: you can still using the ``doctest`` keyword to change the options
of the example.

But because I'm enabling it from the example itself, I need use the
``byexample`` keyword instead of ``doctest``

```python
>>> [1, 2, 3]   # use byexample, not doctest --> # byexample: +py-doctest  +NORMALIZE_WHITESPACE
[1,   2,   3]
```

As you can see ``NORMALIZE_WHITESPACE`` is supported.

We support ``SKIP``, ``IGNORE_EXCEPTION_DETAIL``, ``DONT_ACCEPT_BLANKLINE``
flags and the  ``<BLANKLINE>`` marker:

```python
>>> True   # byexample: +py-doctest +SKIP
False

>>> raise Exception("foo")   # byexample: +py-doctest +IGNORE_EXCEPTION_DETAIL
Traceback (most recent call last):
 -- stack trace
 -- ignored
module.ignored.Exception: -- this will be ignored --

>>> print("foo\n<BLANKLINE>\nbar")   # byexample: +py-doctest +DONT_ACCEPT_BLANKLINE
foo
<BLANKLINE>
bar

>>> print("foo\n\nbar")   # byexample: +py-doctest
foo
<BLANKLINE>
bar
```

And also the report flags: ``REPORT_UDIFF``, ``REPORT_CDIFF`` and ``REPORT_NDIFF``

As you may guess, the ``byexample``'s
[cature tags](docs/basic/capture-and-paste.md) feature are disabled in this
compatibility mode.

But in the other hand, you can use the ``ELLIPSIS`` flag as usual.

```python
>>> print("fooxxxbar")   # byexample: +py-doctest +ELLIPSIS
foo...bar
```

### Compatibility overview

```
==========================  ============================
``doctest``                 Observations
==========================  ============================
``NORMALIZE_WHITESPACE``    Supported
``DONT_ACCEPT_TRUE_FOR_1``  Ignored
``ELLIPSIS``                Supported
``SKIP``                    Supported
``IGNORE_EXCEPTION_DETAIL`` Supported
``DONT_ACCEPT_BLANKLINE``   Supported
``REPORT_UDIFF``            Supported
``REPORT_CDIFF``            Supported
``REPORT_NDIFF``            Supported
=========================== ============================
```

``DONT_ACCEPT_TRUE_FOR_1`` is not supported as it was implemented in ``doctest``
as a workaround for the result of a comparison in Python 2.3: in that time
Python returned 1 and 0 instead of ``True`` and ``False``.


### Exceptions

There is not distinction between a normal output and an exception so if
one want to ignore the traceback, one need to use ``<...>``

This is different from ``doctest`` where the exceptions are captured and handled
different from other outputs. This enables ``doctest`` to know when an
exception was raised but in the practice is not critical.

If you didn't enabled the compatibility with ``doctest``, the ``<...>`` is
enabled by default.

```python
>>> raise Exception('oh no!')
Traceback <...>
Exception: oh no!

>>> non_existent_var
Traceback <...>
NameError: name 'non_existent_var' is not defined
```

At difference with ``doctest``, syntax errors are also captured.

```python
>>> f(]        # invalid syntax
  File<...>
SyntaxError: invalid syntax
```

If you enabled the compatibility mode, any output that it looks like an
exception will be captured and mangled like doctest does: the traceback header
and the stacktrace are ignored.

```python
>>> raise Exception('oh no!')       # byexample: +py-doctest
Traceback (most recent call last):
 -- stack trace
 -- ignored
Exception: oh no!
```

Also note that we will relax the check of the prefix of the exception message.

In ``Python 2.x`` it was common to print only the exception class name but in
``Python 3.x``, the default is to print the full exception name (a dotted name
including its modules)

Testing this it is hard in ``doctest``.

One option is ignore the exception's
details but this also disables the check of the whole exception message
defeating the purpose of checking an exception.

The other was to use ``...`` but ``doctest`` doesn't allow to use it at the
begin of a line.

Because of this, add a ``<...>`` at the begin of the message to avoid these
quirks.

As a side effect, we can check loosely the name of an exception:

```python
>>> raise ValueError('oh no!')       # byexample: +py-doctest
Traceback (most recent call last):
Error: oh no!

>>> raise IndexError('oh no!')       # byexample: +py-doctest
Traceback (most recent call last):
Error: oh no!
```

## Migration to the ``byexample``'s way

As you can see ``byexample`` uses a different set of options. Here
is a summary of the equivalent options:

```
====================  ==========================  ============================
``byexample``         ``doctest``                 Observations
====================  ==========================  ============================
``norm-ws``           ``NORMALIZE_WHITESPACE``    Same functionality.
*not supported*       ``DONT_ACCEPT_TRUE_FOR_1``  Only useful for ``Python 2.3``.
``tags``              ``ELLIPSIS``                More powerful than ``doctest`` version
``skip``              ``SKIP``                    Same functionality.
``pass``              *not supported*             Execute but do not check.
*better alternative*  ``IGNORE_EXCEPTION_DETAIL`` Use the more general ``tags`` flag.
*better alternative*  ``DONT_ACCEPT_BLANKLINE``   Use the more general ``tags`` flag.
``diff``              ``REPORT_UDIFF``            With ``unified`` as argument.
``diff``              ``REPORT_CDIFF``            With ``context`` as argument.
``diff``              ``REPORT_NDIFF``            With ``ndiff`` as argument.
====================  =========================== ============================
```

``DONT_ACCEPT_BLANKLINE`` and ``IGNORE_EXCEPTION_DETAIL`` are used to ignore
some pieces of the output. The ``tags`` flag of ``byexample`` should cover
those cases and even more.

See [norm-ws](docs/basic/normalize-whitespace.md),
[tags](docs/basic/capture-and-paste.md),
[skip](docs/basic/skip-and-pass.md),
[pass](docs/basic/skip-and-pass.md) and
[diff](docs/overview/differences.md) for more info.

## Pretty print display hook

By default, ``byexample`` uses a custom display hook based on the Python's
``pprint`` module.

The custom display hook will pretty print the object instead of using ``repr``

```python
>>> l = ["foo bar %i" % i for i in range(10)]
>>> l
['foo bar 0',
 'foo bar 1',
 'foo bar 2',
 'foo bar 3',
 'foo bar 4',
 'foo bar 5',
 'foo bar 6',
 'foo bar 7',
 'foo bar 8',
 'foo bar 9']
```

If we don't do this, long and complex structures could be hard to print:

```python
>>> print(repr(l))
['foo bar 0', 'foo bar 1', <...>, 'foo bar 8', 'foo bar 9']
```

This feature is disabled if you enabled the ``doctest`` compatibility mode but
it can be reenabled with ``+py-pretty-print``.

Note that ``byexample`` uses the ``pprint`` module of the Python interpreter
running the example.
``pprint`` *doesn't warranty* that its output will be stable between Python
versions. Keep that in mind.

In the future, ``byexample`` may provide a different ``pprint`` stable
implementation.

## Bytes/Unicode marker

``Python 2.x`` uses ``u'`` and ``u"`` (and ``U'`` and ``U"``) to mark the begin of
an unicode literal. Optionally one can use ``b'`` to mark the begin of a
sequence of bytes (``str`` in ``Python 2.x``)

Unfortunately, in ``Python 3.x`` it is the ``u'`` marker optional and the ``b'``
marker mandatory.

This duality forces to have two different sets of expected results one for
``Python 2.x`` and other for ``Python 3.x`` or do not relay in the ``pprint``
functionality for testing at all plus some dirty hacks.

The python interpreter of ``byexample`` uses a custom ``pretty printer``
to remove all the markers ``u'`` and ``b'`` for simple and for nested objects
retaining the original alignment.

The following is a valid example for ``Python 2.x`` and ``3.x`` as well.

```python
>>> u = u'foo'
>>> b = b'bar'

>>> u
'foo'

>>> b
'bar'

>>> du = {u'aaaaaaaa': {u'bbbbbbbbbb': u'asasaaaaaaaaaaaaaasasa', u'c': u'asaaaaaaaaaaaaaaaaaaaaa'}}
>>> db = {b'aaaaaaaa': {b'bbbbbbbbbb': b'asasaaaaaaaaaaaaaasasa', b'c': b'asaaaaaaaaaaaaaaaaaaaaa'}}

>>> du
{'aaaaaaaa': {'bbbbbbbbbb': 'asasaaaaaaaaaaaaaasasa',
              'c': 'asaaaaaaaaaaaaaaaaaaaaa'}}

>>> db
{'aaaaaaaa': {'bbbbbbbbbb': 'asasaaaaaaaaaaaaaasasa',
              'c': 'asaaaaaaaaaaaaaaaaaaaaa'}}

>>> b'b'
'b'

>>> u'u'
'u'
```

If it is really important to show the type of the string I would recommend to
make an explicit check or using ``repr``

```python
>>> isinstance(b, bytes)
True
```

The pretty print is disabled if you are in compatibility mode with doctest.
If you find it useful but you cannot leave the compatibility mode, you can set
the ``+py-pretty-print`` flag to enable it.

## Internals

### Custom prompt

Internally, we change the primary and secondary prompts to a non trivial
texts to reduce the probability of a collision with the code to be
executed and with the output returned by the interpreter.

```python
>>> ">>> "
'>>> '

>>> "... "
'... '

>>> sys
Traceback <...>
NameError: name 'sys' is not defined
```

### Empty lines

Consider the following function definition. It is obvious for a human beign
that the ``return`` statetment belongs to the function definition.

```python
>>> def foo():
...   a = 42
...
...
...   return a
```

But ``Python`` interprets the empty line between ``a = 42`` and ``return a``
as the end of the definition.

``byexample`` removes any empty line that it is followed by an indented
line so the whole example makes sense to ``Python``.

```python
>>> i = 0
>>> for j in range(2):
...   i += j
...
...
... print(i)
1
```

Keep in mind that "empty line" means that, if it is not working for you double
check for any trailing whitespace.

We can disable this fix with ``-py-remove-empty-lines``

```python
>>> def foo():      # byexample: -py-remove-empty-lines
...   a = 42
...
...
...   return a
  File <...>
    return a
    ^
IndentationError: unexpected indent
```

You may ask why if the ``byexample`` fix works, why anyone would like to disable
it. Well, the fix comes with some side effects.

See the following multiline string definition

```python
>>> blob = '''
...
...   foo
... '''
```

How many lines it has? 4 right? well....

```python
>>> blob
'\n  foo\n'

>>> len(blob.split('\n'))
3
```

It has actually 4 but ``byexample`` suppress the empty line because it is
followed by a indented line ``foo`` so we got 3.

In my personal experience, I didn't find an issue with this in the field but if
you need to disable it, you can

```python
>>> # byexample: -py-remove-empty-lines
... blob = '''
...
...   foo
... '''

>>> blob
'\n\n  foo\n'

>>> len(blob.split('\n'))
4
```
