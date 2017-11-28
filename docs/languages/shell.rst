Shell support
=============

``byexample`` can execute shell commands using by default ``/bin/sh``.


Using other shells (long story)
-------------------------------

There is no problem in spawning another shell even if the shell is not
``/bin/sh``

The only caveat is that the spawned shell *must* use the same prompts
that ``byexample`` uses internally.

Exporting all the prompts to the other subshell should be enough.
For example to use ``/bin/bash`` instead of ``/bin/sh``

.. code:: sh
    $ export PS1
    $ export PS2
    $ export PS3
    $ export PS4

    $ echo $0
    /bin/sh

    $ /bin/bash --norc -i
    $ echo $0
    /bin/bash

    $ exit
    exit

The ``--norc`` flag is to make sure that ``bash`` will not load any ``.bashrc``
configuration script. It is quite common that on those scripts the prompts
are changed, overriding ours.

If you are sure that it is ok, you can remove the flag.

Using other shells (short story)
--------------------------------

``byexample`` already has a shortcut to use a different shell.
Use the ``+bash`` option like this:

.. code:: sh
    $ echo $0
    /bin/sh

    $ # byexample: +bash
    $ echo $0
    /bin/bash

    $ # byexample: +sh
    $ echo $0
    /bin/sh

We support currently ``/bin/sh`` and ``/bin/bash``. We are accepting Pull
Request for adding support to other shells!



