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
    <...>
    File byexample/differ.py, 17/17 test ran in <...> seconds
    [PASS] Pass: 17 Fail: 0 Skip: 0
    <...>
    File byexample/expected.py, 98/98 test ran in <...> seconds
    [PASS] Pass: 98 Fail: 0 Skip: 0
    <...>
    File byexample/finder.py, 56/56 test ran in <...> seconds
    [PASS] Pass: 56 Fail: 0 Skip: 0
    <...>
    File byexample/options.py, 64/64 test ran in <...> seconds
    [PASS] Pass: 64 Fail: 0 Skip: 0
    <...>
    File byexample/parser.py, 126/126 test ran in <...> seconds
    [PASS] Pass: 126 Fail: 0 Skip: 0

Then, each module (Finder, Parser and Runner) provided by ``byexample`` has
a little documentation.

.. code:: sh

    $ byexample -l python byexample/modules/python.py
    <...>
    File byexample/modules/python.py, 3/3 test ran in <...> seconds
    [PASS] Pass: 3 Fail: 0 Skip: 0

    $ byexample -l ruby   byexample/modules/ruby.py
    <...>
    File byexample/modules/ruby.py, 3/3 test ran in <...> seconds
    [PASS] Pass: 3 Fail: 0 Skip: 0

    $ byexample -l shell  byexample/modules/shell.py
    <...>
    File byexample/modules/shell.py, 3/3 test ran in <...> seconds
    [PASS] Pass: 3 Fail: 0 Skip: 0

    $ byexample -l gdb    byexample/modules/gdb.py
    <...>
    File byexample/modules/gdb.py, 2/2 test ran in <...> seconds
    [PASS] Pass: 2 Fail: 0 Skip: 0

    $ byexample -l cpp    byexample/modules/cpp.py
    <...>
    File byexample/modules/cpp.py, 2/2 test ran in <...> seconds
    [PASS] Pass: 2 Fail: 0 Skip: 0

If what you are looking for is what is capable of, you definetly need
to see the readme

.. code:: sh

    $ byexample -l $all_languages README.md
    <...>
    File README.md, 11/11 test ran in <...> seconds
    [PASS] Pass: 8 Fail: 0 Skip: 3

But the readme is just the peak of the icerberg, the rest of the documentation
can be found under the ``doc`` folder

.. code:: sh

    $ byexample -l $all_languages --skip docs/how_to_extend.rst -- `find docs -name "*.rst"`
    <...>
    File docs/huff/usage.rst, 13/13 test ran in <...> seconds
    [PASS] Pass: 13 Fail: 0 Skip: 0
    <...>
    File docs/differences.rst, 10/10 test ran in <...> seconds
    [PASS] Pass: 10 Fail: 0 Skip: 0
    <...>
    File docs/usage.rst, 12/12 test ran in <...> seconds
    [PASS] Pass: 12 Fail: 0 Skip: 0
    <...>
    File docs/options.rst, 7/7 test ran in <...> seconds
    [PASS] Pass: 7 Fail: 0 Skip: 0
    <...>
    File docs/languages/cpp.rst, 2/2 test ran in <...> seconds
    [PASS] Pass: 2 Fail: 0 Skip: 0
    <...>
    File docs/languages/shell.rst, 15/15 test ran in <...> seconds
    [PASS] Pass: 15 Fail: 0 Skip: 0
    <...>
    File docs/languages/gdb.rst, 9/9 test ran in <...> seconds
    [PASS] Pass: 9 Fail: 0 Skip: 0
    <...>
    File docs/languages/python.rst, 39/39 test ran in <...> seconds
    [PASS] Pass: 38 Fail: 0 Skip: 1
    <...>
    File docs/languages/ruby.rst, 9/9 test ran in <...> seconds
    [PASS] Pass: 9 Fail: 0 Skip: 0

I left out the ``how_to_extend`` doc. It is not something that you will need
everyday.

But if you want to create your own modules (Finder, Parser, Runner) and
contrib with the community, this doc is for you.
Go ahead!!

.. code:: sh

    $ byexample -l python docs/how_to_extend.rst
    <...>
    File docs/how_to_extend.rst, 36/36 test ran in <...> seconds
    [PASS] Pass: 36 Fail: 0 Skip: 0

