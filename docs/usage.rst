Usage
=====

The help included in ``byexample`` should give you a quick overview of its
capabilities

.. code:: sh

    $ # ignore this
    $ alias byexample=python\ r.py

    $ byexample -h                      # byexample: +WS
    usage: r.py [-h] [-V] [--ff] [--dry] [--skip file [file ...]] [-m dir]
                [-d {none,unified,ndiff,context}] [--no-enhance-diff] -l language
                [--timeout TIMEOUT] [-o OPTIONS] [--encoding ENCODING]
                [--pretty {none,all}] [--interact] [-v | -q]
                file [file ...]
    <blankline>
    positional arguments:
      file                  file that have the examples to run.
    <blankline>
    optional arguments:
      -h, --help            show this help message and exit
      -V, --version         show program's version number and exit
      --ff, --fail-fast     if an example fails, fail and stop all the execution.
      --dry                 do not run any example, only parse them.
      --skip file [file ...]
                            skip these files
      -m dir, --modules dir
                            append a directory for searching modules there.
      -d {none,unified,ndiff,context}, --diff {none,unified,ndiff,context}
                            select diff algorithm.
      --no-enhance-diff     by default, some non-printable characters are replaced
                            by printable ones in the diffs to make them easier to
                            spot; this flag disables that.
      -l language, --language language
                            select which languages to parse and run. Comma
                            separated syntax is also accepted.
      --timeout TIMEOUT     timeout in seconds to complete each example (2 by
                            default); this can be changed per example with TIMEOUT
                            option.
      -o OPTIONS, --option OPTIONS
                            add additional options of the form key=val.
      --encoding ENCODING   select the encoding (supported in Python 3 only, use
                            the same encoding of stdout by default)
      --pretty {none,all}   control how to pretty print the output.
      --interact, --debug   interact with the interpreter manually if an example
                            fails.
      -v                    verbosity level, add more flags to increase the level.
      -q, --quiet           quiet mode, do not print anything even if an example
                            fails; supress the progress output.


The most direct way to use ``byexample`` is to select the language(s) to use
and the files where the examples are.

Let's create a synthetic file with some examples. Some should run without
problems, but others should fail.

.. code:: sh

    $ cat <<EOF > synthetic.doc
    > This is a synthetic file.
    > The following is an example written in Python that should PASS
    >
    >     >>> from __future__ import print_function
    >     >>> 1 + 2
    >     3
    >
    > The next example, however, it should FAIL and this in on purpose
    >
    >     >>> 2 + 2
    >     6
    >
    > This a more interesting example
    >
    >     >>> print('hi', 'everyone  ')
    >     hi everyone
    > EOF


Run
---

Now we just run ``byexample`` selecting ``python`` as the language target
(for now, ignore the ``--pretty none``):

.. code:: sh

    $ byexample --pretty none -l python synthetic.doc       # byexample: +WS
    <...>
    File synthetic.doc, 4/4 test ran in <...> seconds
    [FAIL] Pass: 2 Fail: 2 Skip: 0

At the end of the execution a summary shows how many examples were executed,
how many passed, failed or where skipped.

A skipped example means that the example has a ``+SKIP`` option and it was not
executed.

In normal circumstances there are two possible status: ``PASS`` and ``FAIL``.

If something strange happen like the user pressed ``ctrl-c`` or the underlying
interpreter crashed, the status will be ``ABORT``.

For quick regression you may want to stop ``byexample`` at the first failing
example: *fail fast*

.. code:: sh

    $ byexample --ff --pretty none -l python synthetic.doc       # byexample: +WS
    <...>
    File synthetic.doc, 3/4 test ran in <...> seconds
    [FAIL] Pass: 2 Fail: 1 Skip: 0

Output differences
------------------

Let's see how the failing examples are shown (the ``<...>`` are meant to be
ignored for you, me, and ``byexample``)

.. code:: sh

    $ byexample --pretty none -l python synthetic.doc       # byexample: +WS
    <...>
    **********************************************************************
    File "synthetic.doc", line 10
    Failed example:
        2 + 2
    <...>
    Expected:
    6
    Got:
    4
    <...>
    **********************************************************************
    File "synthetic.doc", line 15
    <...>
    File synthetic.doc, 4/4 test ran in <...> seconds
    [FAIL] Pass: 2 Fail: 2 Skip: 0

Each test is found, parsed and executed. For each test or example that failed
``byexample`` will print the example followed by the expected and the got
outputs.

In the example at line 10, the code executed was ``2 + 2`` and we expected
``6`` but instead we got ``4`` as a result.

Whitespace differences
----------------------

Let's run this again but this time I want to show you only the last example
(once again, I'm using ``<...>`` to ignore the uninterested output).

.. code:: sh

    $ byexample --pretty none -l python synthetic.doc       # byexample: +WS
    <...>
    File "synthetic.doc", line 15
    Failed example:
        print('hi', 'everyone  ')
    Notes:
        <...>
        $: trailing spaces  ?: non-printable    ^t: tab
        ^v: vertical tab   ^r: carriage return  ^f: form feed
    Expected:
    hi everyone
    Got:
    hi everyone$$
    <...>

This time the difference is subtle.

``byexample`` will highlight some whitespace characters both in the expected
and in the got outputs to make easier to see the differences like this.

In this case, the example is printing 'hi everyone' followed by 2 trailing
spaces.

This is hard to be notice! Fortunately ``byexample`` will mark any trailing
space with a '$'.

As the example above shows, other non-printable characters are also highlighted.

You can disable this:

.. code:: sh

    $ byexample --pretty none --no-enhance-diff -l python synthetic.doc  # byexample: +WS
    <...>
    File "synthetic.doc", line 15
    Failed example:
        print('hi', 'everyone  ')
    Expected:
    hi everyone
    Got:
    hi everyone
    <...>

Is harder to spot the difference, isn't?

New lines at the end are ignored
--------------------------------

``byexample`` will ignore any empty line(s) at the end of the expected string
and the got string from the executed examples.

Look at this successful example:

.. code:: python

    >>> print("bar\n\n")
    bar

This is because most of the time an empty new line is added for aesthetics
purposes in the example or produced by the interpreter as an artifact.

If you want to check them explicitly, use a capture tag:

.. code:: python

    >>> print("bar\n\n")
    bar
    <nl>
    <nl>


Diff algorithms
---------------

``byexample`` supports diff algorithms. Instead of printing the expected
and the got outputs separately, you can select one diff and print both outputs
in the same context.

For large outputs this is an awesome tool

.. code:: sh

    $ byexample --pretty none --diff ndiff -l python synthetic.doc  # byexample: +WS
    <...>
    **********************************************************************
    File "synthetic.doc", line 10
    Failed example:
        2 + 2
    <...>
    Differences:
    - 6
    + 4
    <...>
    **********************************************************************
    File "synthetic.doc", line 15
    Failed example:
        print('hi', 'everyone  ')
    <...>
    Differences:
    - hi everyone
    + hi everyone$$
    ?            ++
    <...>


This is a summary of the three diff algorithms plus the default method:

::

    ===========  ==============  ==============  ==============
      default      UDIFF flag      NDIFF flag      CDIFF flag
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


    $ rm -f synthetic.doc
