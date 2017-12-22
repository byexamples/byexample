Usage
=====

The help included in ``byexample`` should give you a quick overview of its
capabilities

.. code:: sh

    $ # ignore this
    $ alias byexample=python\ r.py

    $ byexample -h                      # byexample: +WS
    usage: <...> [-h] [-f] [--dry] [--skip file [file ...]] [--search dir]
                [-d {unified,ndiff,context}] [--no-enhance-diff] -l language
                [--encoding ENCODING] [--no-color] [-v | -q]
                file [file ...]
    <blankline>
    positional arguments:
      file                  file that have the examples to run.
    <blankline>
    optional arguments:
      -h, --help            show this help message and exit
      -f, --fail-fast, --ff
                            if an example fails, fail and stop all the execution.
      --dry                 do not run any example, only parse them.
      --skip file [file ...]
                            skip these files
      --search dir          append a directory for searching modules there.
      -d {unified,ndiff,context}, --diff {unified,ndiff,context}
                            select diff algorithm.
      --no-enhance-diff     by default, some non-printable characters are replaced
                            by printable ones in the diffs to make them easier to
                            spot; this flag disables that.
      -l language, --language language
                            select which languages to parse and run. Comma
                            separated syntax is also accepted.
      --encoding ENCODING   select the encoding (supported in Python 3 only, use
                            the same encoding of stdout by default)
      --no-color            do not output any escape sequence for coloring.
      -v                    verbosity level, add more flags to increase the level.
      -q, --quiet           quiet mode, do not print anything even if an example
                            fails.

The most direct way to use ``byexample`` is to select the language(s) to use
and the files where the examples are.

Let's create a syntetic file with some examples. Some should run without
problems, but others should fail.

.. code:: sh

    $ cat <<EOF > syntetic.doc
    > This is a syntetic file.
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

Now we just run ``byexample`` selecting ``python`` as the language target:

.. code:: sh

    $ byexample --no-color -l python syntetic.doc       # byexample: +WS
    <...>
    File syntetic.doc, 4/4 test ran in <...> seconds
    [FAIL] Pass: 2 Fail: 2 Aborted: 0

At the end of the execution a summary shows how many examples were executed,
how many passed and how many failed.
An aborted examples means that the user aborted it (pressing ctrl-c) or the
underlying interpreter crashed.

Instead of running all the examples, you can run them but stopping at the first
failure:

.. code:: sh

    $ byexample --ff --no-color -l python syntetic.doc       # byexample: +WS
    <...>
    File syntetic.doc, 3/4 test ran in <...> seconds
    [FAIL] Pass: 2 Fail: 1 Aborted: 0

Let's see how the failing examples are shown

.. code:: sh

    $ byexample --no-color -l python syntetic.doc       # byexample: +WS
    ..F
    **********************************************************************
    File "syntetic.doc", line 10
    Failed example:
        2 + 2
    <...>
    Expected:
    6
    Got:
    4
    <...>
    **********************************************************************
    File "syntetic.doc", line 15
    <...>
    File syntetic.doc, 4/4 test ran in <...> seconds
    [FAIL] Pass: 2 Fail: 2 Aborted: 0

Each test is found, parsed and executed. For each test or example that failed
``byexample`` will print the example followed by the expected and the got
outputs.


Let's run this again but this time I want to show you only the last example.

.. code:: sh

    $ byexample --no-color -l python syntetic.doc       # byexample: +WS
    <...>
    File "syntetic.doc", line 15
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

``byexample`` will highlight some whitespaces character both in the expected
and in the got outputs to make easier to see the differences.
In this case, the example is printing 'hi everyone' followed by 2 trailing
spaces.
This is hard to be notice! Fortunately ``byexample`` will mark any trailing
space with a '$'.
As the example above shows, other non-printable characters are also highlighted.

You can disable this:

.. code:: sh

    $ byexample --no-color --no-enhance-diff -l python syntetic.doc  # byexample: +WS
    <...>
    File "syntetic.doc", line 15
    Failed example:
        print('hi', 'everyone  ')
    Expected:
    hi everyone
    Got:
    hi everyone
    <...>

Is harder to spot the difference, isn't?

``byexample`` supports other diff algorithms. You can select one like this

.. code:: sh

    $ byexample --no-color --diff ndiff -l python syntetic.doc  # byexample: +WS
    <...>
    **********************************************************************
    File "syntetic.doc", line 10
    Failed example:
        2 + 2
    <...>
    Differences:
    - 6
    + 4
    <...>
    **********************************************************************
    File "syntetic.doc", line 15
    Failed example:
        print('hi', 'everyone  ')
    <...>
    Differences:
    - hi everyone
    + hi everyone$$
    ?            ++
    <...>

