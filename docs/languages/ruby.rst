Ruby support
============

``byexample`` can execute Ruby code using the default interpreter ``irb``.

The object returned
-------------------

``rb>`` and ``...`` are the only prompts the ``byexample`` uses.

The ``=>`` marker is written by the Ruby interpreter and not by ``byexample``.
It is left as is as this is quite common in the Ruby examples and literature.

.. code:: ruby

    rb> 1 + 2
    => 3

Because everything in Ruby is an expression, everything return a result.
This is annoying if you want to write several Ruby lines without checking
the results.

The semicolon ``;`` at the end of each expression will suppress the print of
the returned object.
But it has also a side effect: all the expressions that end with ``;`` are not
executed until an expression without ``;`` is written.
This is how ``irb`` works behind scenes, so be careful with the use of
semicolons. It is easy to get confused with this weird effect.

.. code:: ruby
    rb> a = 1;
    rb> b = 2;
    rb> a + b     # nice without side effects
    => 3

    rb> puts '4'; # nothing is printed (what a surprise!)

    irb> nil  # this dummy expression is enough to flush the previous one
    4
    => nil

An alternative could be group all the expression using the secondary prompt
and run the example with the ``PASS`` option to ignore the intermediate results.

.. code:: ruby
    rb> a = 1       # byexample: +PASS
    ... b = 2

    rb> a + b
    => 3

