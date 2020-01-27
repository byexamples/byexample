# C++

To support C++, ``byexample`` relays in the ``cling`` interpreter.

You need to have [cling](https://github.com/root-project/cling) installed first.

It is still an **experimental** feature that works pretty well but it is not
immune to bugs, quirks nor crashes.

Don't forget to send your feedback to the ``cling`` community.

> **Stability**: ``experimental`` - non backward compatibility changes are
> possible or even removal between versions (even patch versions).

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

### Abort on a timeout

If a C/C++ example takes too long and
[timeout](/{{ site.uprefix }}/basic/timeout), the whole execution
timeout.

### Input

The [input](/{{ site.uprefix }}/basic/input)
feature (`+input`) is not supported.
