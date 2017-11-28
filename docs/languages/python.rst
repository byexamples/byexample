Python support
==============

``byexample`` is inspired by the Python's ``doctest`` module. I borrowed a
few ideas from it and I also tried to overcome its issues.
This makes a Python example to look very similar to a doctest but it is not
fully compatible with it.

Differences with ``doctest``
----------------------------

The first is that the options are enabled using the ``byexample`` keyword
instead of ``doctest``

.. code:: python

    >>> [1, 2, 3]   # use byexample, not doctest --> # byexample: +WS
    [1,   2,   3]

As you can see ``byexample`` uses a different set of options. Here
is a summary:

====================  ==========================  ============================
``byexample``         ``doctest``                 Observations
====================  ==========================  ============================
``WS``                ``NORMALIZE_WHITESPACE``    Same functionality.
*not supported*       ``DONT_ACCEPT_TRUE_FOR_1``  Only useful for Python 2.3.
``CAPTURE``           ``ELLIPSIS``                ``doctests`` uses ``...``; ``byexample`` uses ``<...>``
``SKIP``              ``SKIP``                    Same functionality.
``PASS``              *not supported*             Execute but do not check.
*better alternative*  ``IGNORE_EXCEPTION_DETAIL`` Use the more general ``CAPTURE`` flag.
*better alternative*  ``DONT_ACCEPT_BLANKLINE``   Use the more general ``CAPTURE`` flag.
====================  =========================== ============================

``DONT_ACCEPT_TRUE_FOR_1`` is not supported as it was implemented in ``doctest``
as a workaround for the result of a comparison in Python 2.3: in that time
Python returned 1 and 0 instead of ``True`` and ``False``.

``DONT_ACCEPT_BLANKLINE`` and ``IGNORE_EXCEPTION_DETAIL`` are used to ignore
some pieces of the output. The ``CAPTURE`` flag of ``byexample`` should cover
those cases.

Ellipsis
........

By default, if the expected text has the ``<...>`` marker, that
will match for any string.

This is different from ``doctest`` where the marker is ``...`` and needs
to be enabled with the ``+ELLIPSIS`` option but the net effect is the same.

.. code:: python

    >>> print(list(range(20)))
    [0, 1, <...>, 18, 19]


Exceptions
..........

There is not distinction between a normal output and an exception so if
one want to ignore the traceback, one need to use ``<...>``

This is different from ``doctest`` where the exceptions are captured and handled
different from other outputs. This enables ``doctest`` to know when an
exception was raised but in the practice is not critical.

.. code:: python

    >>> raise Exception('oh no!')
    Traceback <...>
    Exception: oh no!

    >>> non_existent_var
    Traceback <...>
    NameError: name 'non_existent_var' is not defined


Syntax errors are also captured.

.. code:: python

    >>> f(]        # invalid syntax
      File<...>
    SyntaxError: invalid syntax


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

If it is really important to show the type of the string I would recommend to
make an explicit check or using ``repr``

.. code:: python

    >>> isinstance(b, bytes)
    True


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
