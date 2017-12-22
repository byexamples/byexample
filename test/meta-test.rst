Meta Test
=========

This is a meta test. Instead of test every aspect of ``byexample`` here,
we just run ``make test`` to run the examples of the documentation (in ``doc/``)

The output of that execution will be compared with the expected output here.

This is the expected output for a quick-test

.. code:: sh

    $ colors="--no-color" make -s quick-test
    ..
    File byexample/modules/python.py, 2/2 test ran in <...> seconds
    [PASS] Pass: 2 Fail: 0 Aborted: 0
    ..
    File byexample/modules/ruby.py, 2/2 test ran in <...> seconds
    [PASS] Pass: 2 Fail: 0 Aborted: 0
    ..
    File byexample/modules/shell.py, 2/2 test ran in <...> seconds
    [PASS] Pass: 2 Fail: 0 Aborted: 0
    ..
    File byexample/modules/gdb.py, 2/2 test ran in <...> seconds
    [PASS] Pass: 2 Fail: 0 Aborted: 0


And this is the expected output for a full test (it takes a little longer)

.. code:: sh

    $ colors="--no-color" make -s full-test   # byexample: +TIMEOUT=30
    .................................
    File byexample/options.py, 33/33 test ran in <...> seconds
    [PASS] Pass: 33 Fail: 0 Aborted: 0
    ...........................
    File byexample/parser.py, 27/27 test ran in <...> seconds
    [PASS] Pass: 27 Fail: 0 Aborted: 0
    ...................
    File byexample/runner.py, 19/19 test ran in <...> seconds
    [PASS] Pass: 19 Fail: 0 Aborted: 0
    .................
    File README.rst, 17/17 test ran in <...> seconds
    [PASS] Pass: 17 Fail: 0 Aborted: 0
    ..........
    File docs/usage.rst, 10/10 test ran in <...> seconds
    [PASS] Pass: 10 Fail: 0 Aborted: 0
    .............
    File docs/languages/shell.rst, 13/13 test ran in <...> seconds
    [PASS] Pass: 13 Fail: 0 Aborted: 0
    .....
    File docs/languages/gdb.rst, 5/5 test ran in <...> seconds
    [PASS] Pass: 5 Fail: 0 Aborted: 0
    .................
    File docs/languages/python.rst, 17/17 test ran in <...> seconds
    [PASS] Pass: 17 Fail: 0 Aborted: 0
    ......
    File docs/languages/ruby.rst, 6/6 test ran in <...> seconds
    [PASS] Pass: 6 Fail: 0 Aborted: 0
    ...............................................
    File docs/overview.rst, 47/47 test ran in <...> seconds
    [PASS] Pass: 47 Fail: 0 Aborted: 0
    ...............................
    File docs/how_to_extend.rst, 31/31 test ran in <...> seconds
    [PASS] Pass: 31 Fail: 0 Aborted: 0

