``byexample`` regression tests
==============================

The source code of ``byexample`` has some runnable documentation.
If you want to know how ``byexample`` works, it is the best place
to start.

.. code:: sh

    $ # ignore this
    $ alias byexample=python\ r.py\ --pretty\ none\ --ff
    $ all_languages=python,shell,ruby,gdb,cpp

    $ byexample -l python byexample/*.py
    <nl>
    File byexample/checker.py, 60/60 test ran in <...> seconds
    [PASS] Pass: 60 Fail: 0 Skip: 0
    <nl>
    File byexample/finder.py, 56/56 test ran in <...> seconds
    [PASS] Pass: 56 Fail: 0 Skip: 0
    <nl>
    File byexample/options.py, 64/64 test ran in <...> seconds
    [PASS] Pass: 64 Fail: 0 Skip: 0
    <nl>
    File byexample/parser.py, 84/84 test ran in <...> seconds
    [PASS] Pass: 84 Fail: 0 Skip: 0

Then, each module (Finder, Parser and Runner) provided by ``byexample`` has
a little documentation.

.. code:: sh

    $ byexample -l python byexample/modules/python.py
    <nl>
    File byexample/modules/python.py, 3/3 test ran in <...> seconds
    [PASS] Pass: 3 Fail: 0 Skip: 0

    $ byexample -l ruby   byexample/modules/ruby.py
    <nl>
    File byexample/modules/ruby.py, 3/3 test ran in <...> seconds
    [PASS] Pass: 3 Fail: 0 Skip: 0

    $ byexample -l shell  byexample/modules/shell.py
    <nl>
    File byexample/modules/shell.py, 3/3 test ran in <...> seconds
    [PASS] Pass: 3 Fail: 0 Skip: 0

    $ byexample -l gdb    byexample/modules/gdb.py
    <nl>
    File byexample/modules/gdb.py, 2/2 test ran in <...> seconds
    [PASS] Pass: 2 Fail: 0 Skip: 0

    $ byexample -l cpp    byexample/modules/cpp.py
    <nl>
    File byexample/modules/cpp.py, 2/2 test ran in <...> seconds
    [PASS] Pass: 2 Fail: 0 Skip: 0

If what you are looking for is what is capable of, you definetly need
to see the readme

.. code:: sh

    $ byexample -l $all_languages README.md
    <nl>
    File README.md, 14/14 test ran in <...> seconds
    [PASS] Pass: 11 Fail: 0 Skip: 3

But the readme is just the peak of the icerberg, the rest of the documentation
can be found under the ``doc`` folder

.. code:: sh

    $ byexample -l $all_languages --skip docs/how_to_extend.rst -- `find docs -name "*.rst"`
    <nl>
    File docs/usage.rst, 12/12 test ran in <...> seconds
    [PASS] Pass: 12 Fail: 0 Skip: 0
    <nl>
    File docs/options.rst, 7/7 test ran in <...> seconds
    [PASS] Pass: 7 Fail: 0 Skip: 0
    <nl>
    File docs/languages/cpp.rst, 2/2 test ran in <...> seconds
    [PASS] Pass: 2 Fail: 0 Skip: 0
    <nl>
    File docs/languages/shell.rst, 15/15 test ran in <...> seconds
    [PASS] Pass: 15 Fail: 0 Skip: 0
    <nl>
    File docs/languages/gdb.rst, 9/9 test ran in <...> seconds
    [PASS] Pass: 9 Fail: 0 Skip: 0
    <nl>
    File docs/languages/python.rst, 36/36 test ran in <...> seconds
    [PASS] Pass: 35 Fail: 0 Skip: 1
    <nl>
    File docs/languages/ruby.rst, 9/9 test ran in <...> seconds
    [PASS] Pass: 9 Fail: 0 Skip: 0

I left out the ``how_to_extend`` doc. It is not something that you will need
everyday.

But if you want to create your own modules (Finder, Parser, Runner) and
contrib with the community, this doc is for you.
Go ahead!!

.. code:: sh

    $ byexample -l python docs/how_to_extend.rst
    <nl>
    File docs/how_to_extend.rst, 36/36 test ran in <...> seconds
    [PASS] Pass: 36 Fail: 0 Skip: 0

