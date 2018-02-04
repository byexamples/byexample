Python support
==============

``byexample`` is inspired by the Python's ``doctest`` module. I borrowed a
few ideas from it and I also tried to overcome its issues.

This makes a Python example to look very similar to a doctest but it is not
fully compatible with it.

To make it (almost) fully compatible, you need to pass the '+py-doctest' flag to
``byexample`` in the command line.

In the following examples I will pass this flag in the examples themselves.

Compatibility with ``doctest``
------------------------------

If you enabled the compatibility from the command line, nothing needs to be
changed: you can still using the ``doctest`` keyword to change the options
of the example.

But because I'm enabling it form the example itself, I need use the
``byexample`` keyword instead of ``doctest``

.. code:: python

    >>> [1, 2, 3]   # use byexample, not doctest --> # byexample: +py-doctest  +NORMALIZE_WHITESPACE
    [1,   2,   3]


As you can see ``NORMALIZE_WHITESPACE`` is supported.

We support ``SKIP``, ``DONT_ACCEPT_BLANKLINE`` flags and the  ``<blankline>``
tags:

.. code:: python

    >>> True   # byexample: +py-doctest +SKIP
    False

    >>> print("foo\n<blankline>\nbar")   # byexample: +py-doctest +DONT_ACCEPT_BLANKLINE
    foo
    <blankline>
    bar

    >>> print("foo\n\nbar")   # byexample: +py-doctest
    foo
    <blankline>
    bar

As you may guess, the ``byexample``'s cature tags feature are disabled in this
compatibility mode.

But in the other hand, you can use the ``ELLIPSIS`` flag as usual.

.. code:: python

    >>> print("fooxxxbar")   # byexample: +py-doctest +ELLIPSIS
    foo...bar


Compatibility overview
......................

==========================  ============================
``doctest``                 Observations
==========================  ============================
``NORMALIZE_WHITESPACE``    Supported
``DONT_ACCEPT_TRUE_FOR_1``  Ignored
``ELLIPSIS``                Supported
``SKIP``                    Supported
``IGNORE_EXCEPTION_DETAIL`` Ignored
``DONT_ACCEPT_BLANKLINE``   Supported
=========================== ============================

``DONT_ACCEPT_TRUE_FOR_1`` is not supported as it was implemented in ``doctest``
as a workaround for the result of a comparison in Python 2.3: in that time
Python returned 1 and 0 instead of ``True`` and ``False``.


Exceptions
..........

There is not distinction between a normal output and an exception so if
one want to ignore the traceback, one need to use ``<...>``

This is different from ``doctest`` where the exceptions are captured and handled
different from other outputs. This enables ``doctest`` to know when an
exception was raised but in the practice is not critical.

If you didn't enabled the compatibility with ``doctest``, the ``<...>`` is
enabled by default.
If you did, you need to disable it for the particular example

.. code:: python

    >>> raise Exception('oh no!')  # byexample: -py-doctest
    Traceback <...>
    Exception: oh no!

    >>> non_existent_var  # no compatibility, <...> capture enabled by default
    Traceback <...>
    NameError: name 'non_existent_var' is not defined


A difference with ``doctest``, syntax errors are also captured.

.. code:: python

    >>> f(]        # invalid syntax
      File<...>
    SyntaxError: invalid syntax

Migration to the ``byexample``'s way
------------------------------------

As you can see ``byexample`` uses a different set of options. Here
is a summary of the equivalent options:

====================  ==========================  ============================
``byexample``         ``doctest``                 Observations
====================  ==========================  ============================
``norm-ws``           ``NORMALIZE_WHITESPACE``    Same functionality.
*not supported*       ``DONT_ACCEPT_TRUE_FOR_1``  Only useful for Python 2.3.
``capture``           ``ELLIPSIS``                More powerful than ``doctest`` version
``skip``              ``SKIP``                    Same functionality.
``pass``              *not supported*             Execute but do not check.
*better alternative*  ``IGNORE_EXCEPTION_DETAIL`` Use the more general ``capture`` flag.
*better alternative*  ``DONT_ACCEPT_BLANKLINE``   Use the more general ``capture`` flag.
====================  =========================== ============================

``DONT_ACCEPT_BLANKLINE`` and ``IGNORE_EXCEPTION_DETAIL`` are used to ignore
some pieces of the output. The ``capture`` flag of ``byexample`` should cover
those cases and even more.


Bytes/Unicode marker
--------------------

Python 2.x uses ``u'`` and ``u"`` (and ``U'`` and ``U"``) to mark the begin of
an unicode literal. Optionally one can use ``b'`` to mark the begin of a
sequence of bytes (``str`` in Python 2.x)

Unfortunately, in Python 3.x it is the ``u'`` marker optional and the ``b'``
marker mandatory.

This duality forces to have two different sets of expected results one for
Python 2.x and other for Python 3.x or do not relay in the ``pprint``
functionality for testing at all plus some dirty hacks.

The python interpreter of ``byexample`` uses a custom ``pretty printer``
to remove all the markers ``u'`` and ``b'`` for simple and for nested objects
retaining the original alignment.

The following is a valid example for Python 2.x and 3.x as well.

.. code:: python

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

    >>> b'b'            # byexample: +py-doctest
    'b'

    >>> u'u'            # byexample: +py-doctest
    'u'

If it is really important to show the type of the string I would recommend to
make an explicit check or using ``repr``

.. code:: python

    >>> isinstance(b, bytes)
    True

The pretty print is disabled if you are in compatibility mode with doctest.
If you find it useful but you cannot leave the compatibility mode, you can set
the ``+py-pretty-print`` flag to enable it.


Custom prompt
-------------

Internally, we change the primary and secondary prompts to a non trivial
texts to reduce the probability of a collision with the code to be
executed and with the output returned by the interpreter.

.. code:: python

    >>> ">>> "
    '>>> '

    >>> "... "
    '... '

    >>> sys
    Traceback <...>
    NameError: name 'sys' is not defined
