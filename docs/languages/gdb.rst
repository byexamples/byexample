GDB the GNU debugger
====================

``byexample`` can interpret and run examples for a GDB session.

To show you this, let's first create a program to debug:

.. code:: sh

    $ cat <<EOF > test.c
    > #include <stdio.h>
    > int main(int argc, char* argv[]) {
    >     for (; argc > 0; --argc)
    >         printf("%s\n", argv[argc-1]);
    >
    >     return 0;
    > }
    > EOF

    $ gcc -o test.bin -ggdb -O0 test.c  # byexample: +TIMEOUT=5

The program is quite simple, it just prints its parameters in reverse order

.. code:: sh

    $ ./test.bin
    ./test.bin

    $ ./test.bin foo bar
    bar
    foo
    ./test.bin

Find interactive examples
-------------------------

Now, let's debug it with GDB

``byexample`` uses the ``(gdb)`` string as the primary prompt to find
GDB examples like these:

.. code::

    (gdb) file ./test.bin
    Reading symbols <...>

    (gdb) start foo bar
    <...>
    Starting program: <...>

    (gdb) print argc
    $1 = 3

    (gdb) print argv[1]
    $2 = "foo"

Be a gentlemen and clean up the environment

.. code:: sh

    $ rm -f ./test.bin ./test.c
