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

For Python ``byexample`` uses the ``>>>`` string as the primary prompt and
``...`` as the secondary prompt.

.. code:: python

    >>> 1 + 2
    3

The expression ``1 + 2`` is executed and the output compared with ``3`` to
see if the test passes or not.

.. code:: python

    >>> a = 1
    >>> b = 2
    >>> a + b
    3

    >>> def f(a, b):
    ...     return a + b

    >>> f(2, 6)
    8

    >>> def g(a, b, c):
    ...     c += a
    ...     c += b
    ...     
    ...     return c

    >>> g(1, 2, 3)
    6

    >>> [1, 2,
    ...  3, 4]
    [1, 2, 3, 4]

Instead for Ruby ``byexample`` uses the ``rb>`` string as the primary prompt and
``...`` as the secondary prompt.

The ``=>`` marker is written by the Ruby interpreter and not by ``byexample``.
It is left as is as this is quite common in the Ruby examples and literature.

.. code:: ruby

    rb> 1 + 2
    => 3

    rb> a = 1;
    rb> b = 2;
    rb> a + b
    => 3

    rb> def f(a, b)
    ...   a + b
    ... end;

    rb> f(2, 6)
    => 8

    rb> def g(a, b, c)
    ...     c += a
    ...     c += b
    ...
    ...     return c
    ... end;

    rb> g(1, 2, 3)
    => 6

For Shell, we use the simple ``$`` or ``#`` markers as the primary prompt
and ``>`` as the secondary prompt.
It is common to use ``#`` when user of the shell is ``root`` and to use ``>``
otherwise but nevertheless ``byexample`` treats those prompts like the same.

.. code:: sh

    $ echo $(( 1 + 2 ))
    3

    $ a=1;
    $ b=2;
    $ echo $(( $a + $b ))
    3

    $ f () {
    >   echo $(( $1 + $2 ))
    > }

    $ f 2 6
    8

    # g () {
    >     c=$3
    >     c=$(( $c + $1 ))
    >     c=$(( $c + $2 ))
    >
    >     echo $c
    > }

    # g 1 2 3
    6


The 'match anything' wildcard
-----------------------------

By default, if the expected text has the ``<...>`` marker, that
will match for any string.
Very useful to match long strings with unwanted or uninteresting pieces.

.. code:: python

    >>> print(list(range(20)))
    [0, 1, <...>, 18, 19]

.. code:: ruby

    rb> (0...20).to_a
    => [0, 1, <...>, 18, 19]

.. code:: sh

    $ echo 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19
    0 1 <...> 18 19

Capture
-------

The ``<name>`` marker can be used to capture any string (like ``<...>``)
but also it assigns a name to the capture.

.. code:: python

    >>> X = 42

    >>> [1, 2, X, 4]
    [1, 2, <random-number>, 4]

.. code:: ruby

    rb> X = 42;

    rb> [1, 2, X, 4]
    => [1, 2, <random-number>, 4]

.. code:: sh

    $ X=42;

    $ echo 1 2 $X 4
    1 2 <random-number> 4


If the same name is used in an example, all the string captured must be
the same string.

.. code:: python

    >>> [1, X, 2, X]
    [1, <random-number>, 2, <random-number>]

    >>> # this will fail because X and 4 are not the **same** 'random-number'
    >>> # we use +PASS to force the skip the checks of this test
    >>> [1, X, 2, 4]        # byexample: +PASS
    [1, <random-number>, 2, <random-number>]

.. code:: ruby

    rb> [1, X, 2, X]
    => [1, <random-number>, 2, <random-number>]

    rb> # this will fail because X and 4 are not the **same** 'random-number'
    rb> # we use +PASS to force the skip the checks of this test
    rb> [1, X, 2, 4]        # byexample: +PASS
    => [1, <random-number>, 2, <random-number>]

.. code:: sh

    $ echo 1 $X 2 $X
    1 <random-number> 2 <random-number>

    $ # this will fail because X and 4 are not the **same** 'random-number'
    $ # we use +PASS to force the skip the checks of this test
    $ echo 1 $X 2 4       # byexample: +PASS
    1 <random-number> 2 <random-number>

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

.. code:: ruby

    rb> (0...20).to_a              # byexample: +WS
    => [0,   1,  2,  3,  4,  5,  6,  7,  8,  9,
    10,  11, 12, 13, 14, 15, 16, 17, 18, 19]

.. code:: sh

    $ echo 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19   # byexample: +WS
    0    1   2   3   4   5   6   7   8   9
    10   11  12  13  14  15  16  17  18  19

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

.. code:: ruby

    rb> a = 1;
    rb> a = 2;      # do not run this code # byexample: +SKIP
    rb> a
    => 1

    rb> def f()
    ...   puts("Choosing a random number...")
    ...   return 42
    ... end;

    rb> a = f()     # execute the code but ignore the output # byexample: +PASS
    rb> a
    => 42

.. code:: sh

    $ a=1;
    $ a=2;      # do not run this code # byexample: +SKIP
    $ echo $a
    1

    $ f() {
    >   echo "Choosing a random number..." >&2
    >   echo 42
    > }

    $ a=`f`     # execute the code but ignore the output # byexample: +PASS
    $ echo $a
    42

Timeout
.......

The execution of each example has a timeout which can be changed by
a flag

.. code:: python

    >>> import time
    >>> time.sleep(2.5) # simulates a slow operation # byexample: +TIMEOUT=3

Differences
-----------

``byexample`` will show you the differences when there is a mismatch.
How?  it will depend of flags used.

===========  ==============  ==============  ==============
default      ``UDIFF`` flag  ``NDIFF`` flag  ``CDIFF`` flag
===========  ==============  ==============  ==============
Expected:     Differences:    Differences:    Differences:
one           +zero           + zero          *** 1,4 ****
two            one              one             one
three         -two            - two           ! two
four          -three          - three         ! three
Got:          +tree           ?  -              four
zero           four           + tree          --- 1,4 ----
one                             four          + zero
tree                                            one
four                                          ! tree
                                                four
===========  ==============  ==============  ==============
