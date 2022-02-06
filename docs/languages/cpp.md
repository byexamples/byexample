# C/C++

Run the `C/C++` examples calling `byexample` as:

```shell
$ byexample -l cpp your-file-here                # byexample: +skip
```

To support C/C++, ``byexample`` relays in the ``cling`` interpreter.

You need to have [cling](https://github.com/root-project/cling) installed first.

It is still an **experimental** feature that works pretty well but it is not
immune to bugs, quirks nor crashes.

Don't forget to send your feedback to the ``cling`` community.

> **Stability**: ``experimental`` - non backward compatibility changes are
> possible or even removal between versions (even patch versions).

Because installing and using `cling` may be a little difficult, we
offer a [docker image](https://hub.docker.com/r/eldipa/cling) with `cling`
pre-installed (the
[dockerfile](https://github.com/byexamples/byexample/tree/master/test/Dockerfile-cling)
is available too).

### How to use the docker image

Download the image:

```shell
$ sudo docker pull eldipa/cling              # byexample: +skip
```

Define a convenient variable; replace the `<dir>` with the **absolute
path** where your documentation/tests are.

```shell
$ cmd="sudo docker run --rm -it -v <dir>:/mnt -w /mnt eldipa/cling cling %a"  # byexample: +skip
```

Inside the container, the `<dir>` content will be in `/mnt` which
it will be the current directory for the `cling` command.

Finally, run `byexample` with a custom
[shebang](/{{ site.uprefix}}/advanced/shebang):

```shell
$ byexample -l cpp -x-shebang="cpp:$cmd" <files>    # byexample: +skip
```


### Variable definition

All the variables are global and can be accessed by other examples

```cpp
?: double radio = 2.0;
?: double sup = 3.14 * (radio * radio);

?: sup
(double) 12.56<...>
```

The last expression without ending with a ``;`` is interpreted by
``cling`` as the expression to not only evaluate but also to print its value.

### stdlib

You can use the ``stdlib`` as usual.

Here is an example of how to print something
and check the output later:

```cpp
?: #include <iostream>

?: int i;
?: for (i = 0; i < 3; ++i) {
::    std::cout << i << std::endl;
:: }
0
1
2
```

### External libs

In addition to ``stdlib`` you can add your own. These can be
in the form of C++ code and it will be compiled by `cling` or in
the form of PIC, shared and dynamically linked library (aka, `.so`)

For the first case you need to pass the path to the source code
with `.L` or these `pragma`

```cpp
?: #pragma cling load("test/ds/mylib1.cpp")   // this will compile mylib1.cpp
?: #include "test/ds/mylib1.h"    // the headers are needed to, as usual

?: mylib1_foo(2)
calling my lib1
(int) 4
```

For the second case, we need to compile the code ourselves:

```shell
$ g++ -shared -fPIC -o test/ds/libmylib2.so test/ds/mylib2.cpp  # byexample: +timeout=16
```

The load then proceeds as before.

```cpp
?: #pragma cling load("test/ds/libmylib2.so")   // already compiled
?: #include "test/ds/mylib2.h"    // the headers are needed to, as usual

?: mylib2_foo(2)
increased performance with lib2
(int) 6
```

We can define where to search for libraries and headers via two `pragma`
so we can avoid some typing

```cpp
?: #pragma cling add_library_path("test/ds/")
?: #pragma cling add_include_path("test/ds/")

?: #pragma cling load("mylib3.cpp")   // works for .so too
?: #include "mylib3.h"

?: mylib3_foo(2)
lib3, four times better
(int) 8
```

> Note: `cling` is quite experimental and at least for the 0.6 version,
> it has not good diagnostic messages.
>
> If you find an error like `fatal error: 'libmylib2.so' file not found`
> it may indicate that you are not configuring the path correctly **or** that
> the library was not compiled as shared.
>
> Best way to troubleshoot is to use explicit paths to distinguish one
> error from the other.
>
> If `cling` tries to load you shared library but it complains that it is not
> an UTF-8 valid file it means that `cling` is trying to see the
> library as source code. I found that this happen if the library is not
> compiled as a shared library.
>
> Double check with `file libmylib2.so`, you should see something like
> `libmylib2.so: ELF 64-bit LSB pie executable, ..., dynamically linked, ...`

### Running C code (and not C++)

`cling` only supports C++ however it is possible to test C code
if it is compiled outside of `cling` and loaded as a library.

```shell
$ gcc -std=c99 -shared -fPIC -o test/ds/libmylibC.so test/ds/mylibC.c   # byexample: +timeout=16
```

```cpp
?: #pragma cling load("test/ds/libmylibC.so")   // C code
?: #include "test/ds/mylibC.h"    // the declarations must be inside the extern "C" {...}

?: mylibC_foo(2)
(int) 3
```

While the examples will be running as C++ code, the function
`mylibC_foo` was compiled as C code.

Keep in mind that the header `mylibC.h` must have all the function
declarations inside `extern "C" { ... }` so `cling` will know that it
has to use the "C" calling convention and not the "C++" one.

See [language linkage](https://en.cppreference.com/w/cpp/language/language_linkage)
for reference.

### Syntax errors

``byexample`` will show you the syntax errors detected by ``cling``.
You can even check for them as part of the normal output:

```cpp
?: for (i = 0; i < unknown; ++i) {
::    std::cout << i << std::endl;
:: }
<...>: error: use of undeclared identifier 'unknown'
 for (i = 0; i < unknown; ++i) {
                 ^
```

## Known limitations

### Gotchas

To print boolean expressions you need to surround them with parenthesis

```cpp
?: (1 == 2)
(bool) false
```

### Terminal support

To work with the current C/C++ interpreter, ``cling``, the ANSI
[terminal emulator](/{{ site.uprefix }}/advanced/terminal-emulation) is
enabled by default (``+term=ansi``) and cannot be disabled.

Also, the [terminal geometry](/{{ site.uprefix }}/advanced/geometry)
cannot by changed after launching the interpreter
so the option ``+geometry`` cannot be used in an example (but it can be
used from the command line)

The amount of rows of the terminal has a minimum value of 128 and this limit
is really important: if your outputs have more than 128 lines you will need
to increase the geometry or the results may be undefined.

The same for the width of the terminal: minimum of 128 columns.

### Echoed input lines

If the C/C++ snippet has a very long line, greater than the terminal's width,
the last part of the line that does not fit in the terminal will be *echoed*
in the output of the example.

This is an annoying artifact due how ``cling`` works.

A simple workaround is to make the lines of the code in the snippet
shorter or increase the
[terminal width](/{{ site.uprefix }}/advanced/geometry).

<!--

Regression test: we expect to see the output even if we didn't send
the std::endl object.

?: std::cout << 1;
1

?: std::cout << 2;
2

?: std::cout << 3 << '\n';
3

?: std::cout << 4 << '\n' << 5;
4
5

-->

### Abort on a timeout

If a C/C++ example takes too long and
[timeout](/{{ site.uprefix }}/basic/timeout), the whole execution
timeout.

### Type text

The [type](/{{ site.uprefix }}/basic/input)
feature (`+type`) is not supported.

<!--
$ rm -f test/ds/libmylib*.so  # byexample: -skip +pass
-->

## C/C++ specific options

```
$ byexample -l cpp --show-options       # byexample: +norm-ws
<...>
cpp's specific options
----------------------
  None.
<...>
```
