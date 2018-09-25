<!--
Check that we have gcc installed first
$ hash gcc                                          # byexample: +fail-fast
-->

# GDB the GNU debugger

``byexample`` can interpret and run examples for a ``GDB`` session.

You need to have the debugger installed first on your system, check
its [download page](https://www.gnu.org/software/gdb/download/).

To show you this, let's first create a program to debug:

```cpp
$ cat test/ds/param-echo.c                      # byexample: -tags
#include <stdio.h>
int main(int argc, char* argv[]) {
    for (; argc > 0; --argc)
        printf("%s\n", argv[argc-1]);
    return 0;
}
```

```
$ gcc -o w/param-echo.exe -ggdb -O0 test/ds/param-echo.c  # byexample: +timeout=10
```

The program is quite simple, it just prints its parameters in reverse order

```
$ ./w/param-echo.exe
./w/param-echo.exe

$ ./w/param-echo.exe foo bar
bar
foo
./w/param-echo.exe
```

## Find interactive examples

Now, let's debug it with ``GDB``

``byexample`` uses the ``(gdb)`` string as the primary prompt to find
``GDB`` examples like these:

```
(gdb) file ./w/param-echo.exe
Reading symbols <...>

(gdb) start foo bar
<...>
Starting program: <...>

(gdb) print argc
$1 = 3

(gdb) print argv[1]
$2 = "foo"
```
