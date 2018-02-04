Change how to run the examples through options
==============================================

The parsing and execution of the examples can be changed through flags and
options.

You can set them globally or set them for a particular example.

Options for a particular example
--------------------------------

Let's see this in action. The following is a Python example which output
will be checked ignoring the whitespaces.

.. code:: python

    >>> [1, 2, 3]               # byexample: +norm-ws
    [1,     2,     3]

The option ``+norm-ws`` is a standard option of ``byexample`` and because we set
it in the example itself, it will apply to it only.

Options for all the examples
----------------------------

Let's recreate the same example above in another file but without the
``+norm-ws`` flag:

.. code:: sh

    $ cat <<EOF > synthetic.doc
    > >>> [1, 2, 3]
    > [1,     2,     3]
    >
    > EOF

If we run it it will fail because ``norm-ws`` is not activated by default

.. code:: sh

    $ # ignore this
    $ alias byexample=python\ r.py

    $ byexample --pretty none -l python synthetic.doc
    <...>
    File synthetic.doc, 1/1 test ran in <...> seconds
    [FAIL] Pass: 0 Fail: 1 Skip: 0

But we can enable ``norm-ws`` globally using ``--options``

    $ byexample --pretty none -l python --options "+norm-ws" synthetic.doc
    <...>
    File synthetic.doc, 1/1 test ran in <...> seconds
    [PASS] Pass: 1 Fail: 0 Skip: 0

Show all the options
--------------------

To know what options are available and what they do, use the ``--show-options``.
``byexample`` will print the options for the languages specified with ``-l``

.. code:: sh

    $ byexample --pretty none -l python --show-options
    byexample's options
    -------------------
    optional arguments:
      +fail-fast            if an example fails, fail and stop all the execution.
      +norm-ws              ignore the amount of whitespaces.
      <...>
    python's specific options
    -------------------------
    optional arguments:
      +py-doctest           enable the compatibility with doctest.
      +py-pretty-print      enable the pretty print enhancement.
      <...>
