<!--
Check that we have gcc installed first
$ hash gcc                                          # byexample: +fail-fast
-->

# GDB the GNU debugger

``byexample`` can interpret and run examples for a ``GDB`` session.

Run `byexample` as:

```shell
$ byexample -l gdb your-file-here                # byexample: +skip
```

You need to have the debugger installed first on your system, check
its [download page](https://www.gnu.org/software/gdb/download/).

> **Stability**: ``experimental`` - non backward compatibility changes are
> possible or even removal between versions (even patch versions).

<!-- matrix CI begin -->
<!-- matrix CI end -->

## Quick example

To show you this, let's first create a program to debug:

```cpp
$ cat test/ds/param-echo.c                      # byexample: -capture
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

## GDB specific options

```
$ byexample -l gdb --show-options       # byexample: +norm-ws
<...>
gdb's specific options
----------------------
  None.
```
