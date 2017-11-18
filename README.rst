``byexample``
=============

``byexample`` is literate programming engine where you can write
ordinary text and snippets the code in the same file
It is intended primary for writing good and live documentation showing
how a piece of software works or it can be used *by example*.

Currently we support
 - Python
 - Ruby
 - Shell (sh and bash)

More languages will be supported in the future. Stay tuned.

Snippets of code
----------------

Any snippet of code that it is detected by ``byexample`` will be executed
and its output compared with the expected one.
This a quite useful way to test and document by example.

The snippets are preceded by the primary prompt. If the code spans
multiple lines, ``byexample`` uses a secondary prompt.

There is not restriction in which snippets you can add. You can even mix
snippets of different languages in the same file!

You can write some Python code

.. code:: python

    >>> 1 + 2
    3

The expression ``1 + 2`` is executed and the output compared with ``3`` to
see if the test passes or not.

And then write some Ruby code

.. code:: ruby

    rb> def f(a, b)
    ...   a + b
    ... end;

    rb> f(2, 6)
    => 8


The 'match anything' wildcard
-----------------------------

By default, if the expected text has the ``<...>`` marker, that
will match for any string.
Very useful to match long strings with unwanted or uninteresting pieces.

.. code:: python
    >>> print(list(range(20)))
    [0, 1, <...>, 18, 19]

Capture
-------

The ``<name>`` marker can be used to capture any string (like ``<...>``)
but also it assigns a name to the capture.

If the same name is used in an example, all the string captured must be
the same string.

.. code:: python
    >>> X = 42

    >>> [1, X, 2, X]
    [1, <random-number>, 2, <random-number>]

    >>> # this will fail because X and 4 are not the **same** 'random-number'
    >>> # we use +PASS to force the skip the checks of this test
    >>> [1, X, 2, 4]        # byexample: +PASS
    [1, <random-number>, 2, <random-number>]


Option flags
------------

``byexample`` support a set of flags or options that can change some
parameters of the execution of the example.
Some flags are generic, others are interpreter-specific.

Normalize whitespace
....................

Replace any sequence of whitespace by a single one. This makes the test
more robust against small differences (trailing spaces, space/tab mismatch)

.. code:: python
    >>> print(list(range(20)))     # byexample: +WS
    [0,   1,  2,  3,  4,  5,  6,  7,  8,  9,
    10,  11, 12, 13, 14, 15, 16, 17, 18, 19]

Skip and Pass
.............

``SKIP`` will skip the example completely while ``PASS`` will execute it
normally but it will not check the output.

.. code:: python
    >>> a = 1
    >>> a = 2       # do not run this code # byexample: +SKIP
    >>> a
    1

    >>> def f():
    ...   print("Choosing a random number...")
    ...   return 42

    >>> a = f()     # execute the code but ignore the output # byexample: +PASS
    >>> a
    42

