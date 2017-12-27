.. image:: https://travis-ci.org/eldipa/byexample.svg?branch=master
   :alt Build Status
   :target https://travis-ci.org/eldipa/byexample

``byexample``
=============

``byexample`` is literate programming engine where you can write
ordinary text and snippets the code in the same file.

It is intended primary for writing good and live tutorials and documentation
showing how a piece of software works or it can be used *by example*.

Currently we support
 - Python
 - Ruby
 - Shell (sh and bash)
 - GDB (the GNU Debugger)

The documentation of each one can be found in ``docs/languages/``.

More languages will be supported in the future. Stay tuned.

Contribute
^^^^^^^^^^

Go ahead, fork this project a start to hack it. Run `make test` to ensure that
everything is working as expected and then propose your Pull Request!

There are some interesting areas where you can contribute like
 - add support to new languages (Javascript, Julia, just listen to you heart)
 - add more examples. How do you use ``byexample``? Give us your feedback!

Usage
^^^^^

Install and run it against any source file(s), like this README.
All the snippets will be collected, executed and checked.

.. code:: sh

    $ pip install --user byexample                # install it # byexample: +SKIP
    $ byexample -l python,ruby,shell README.rst   # run it     # byexample: +SKIP
    ................
    File README.rst, 16/16 test ran in 1.01 seconds
    [PASS] Pass: 16 Fail: 0 Aborted: 0

You can select which languages to run, over which files, how to display the
differences and much more.

The ``doc/usage.rst`` document goes through almost all the flags that the
``byexample`` program has.

For a quick help, you probably will need to just run:

.. code:: sh

    $ byexample -h                                   # byexample: +SKIP
    usage: byexample <...>

Snippets of code
----------------

Any snippet of code that it is detected by ``byexample`` will be executed
and its output compared with the text below.

This is a quite useful way to test and document by example.

Any code that is written inside of a fenced code block will be parsed and
executed depending of the language selected.

Here is an example in Python

.. code::

    ```python
    1 + 2
    
    out:
    3
    ```

The expression ``1 + 2`` is executed and the output compared with ``3`` to
see if the test passes or not.

For some languages, we support the interpreter-session like syntax.

For Python we use ``>>>`` and ``...`` as prompts to find this sessions

.. code:: python

    >>> def add(a, b):
    ...   return a + b

    >>> add(1, 2)
    3

There is not restriction in which snippets you can add. You can even mix
snippets of different languages in the same file!

Here is an example in Ruby

.. code:: ruby

    >> def add(a, b)
    >>   a + b
    >> end;

    >> add(2, 6)
    => 8

The documentation of each language can be found in ``docs/languages/``.

The 'match anything' wildcard
-----------------------------

By default, if the expected text has the ``<...>`` marker, that
will match for any string.

Very useful to match long unwanted or uninteresting strings.

.. code:: python

    >>> print(list(range(20)))
    [0, 1, <...>, 18, 19]

Capture
-------

The ``<name>`` marker can be used to capture any string (like ``<...>``)
but also it assigns a name to the capture.

If a name is used in an example more than once, all the string captured under
that name must be the same string, otherwise the test will fail.

Given the value:

.. code:: python

    >>> X = 42

The following example will pass, as both ``random-number``s are the same (42).

.. code:: python

    >>> [1, X, 2, X]
    [1, <random-number>, 2, <random-number>]

But in the following, both numbers are different and the example will fail

.. code:: python

    >>> [1, X, 2, 4]                                    # byexample: +PASS
    [1, <random-number>, 2, <random-number>]


Option flags
------------

``byexample`` supports a set of flags or options that can change some
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
    >>> a = 2       # this assignment will not be executed # byexample: +SKIP
    >>> a
    1

    >>> def f():
    ...   print("Choosing a random number...")
    ...   return 42

    >>> a = f()     # execute the code but ignore the output # byexample: +PASS
    >>> a
    42

Timeout
.......

The execution of each example has a timeout which can be changed by
a flag

.. code:: python

    >>> import time
    >>> time.sleep(2.5) # simulates a slow operation # byexample: +TIMEOUT=3

Extend ``byexample``
^^^^^^^^^^^^^^^^^^^^

It is possible to extend ``byexample`` adding new ways to find examples in a
document and/or to parse and interpret a new language.

The ``doc/how_to_extend.rst`` is a quick tutorial that shows exactly that.
