# C++

To support C++, ``byexample`` relays in the ``cling`` interpreter.

You need to have [cling](https://github.com/root-project/cling) installed first.

It is still an **experimental** feature that works pretty well but it is not
immune to bugs, quirks nor crashes.

Don't forget to send your feedback to the ``cling`` community.

### Variable definition

All the variables are global and can be accessed by other examples

```cpp
double radio = 2.0;
double sup = 3.14 * (radio * radio);

sup

out:
(double) 12.56<...>
```

The last expression without ending with a ``;`` is interpreted by
``cling`` as the expression to not only eval but also to print its value.

### stdlib

You can use the ``stdlib`` as usual.

Here is an example of how to print something
and check the output later:

```cpp
#include <iostream>

int i;
for (i = 0; i < 3; ++i) {
    std::cout << i << std::endl;
}

out:
0
1
2
```

### Syntax errors

``byexample`` will show you the syntax errors detected by ``cling``.
You can even check for them as part of the normal output:

```cpp
for (i = 0; i < unknown; ++i) {
    std::cout << i << std::endl;
}

out:
<...>: error: use of undeclared identifier 'unknown'
 for (i = 0; i < unknown; ++i) {
                 ^
```

## Known limitations

### Gotchas

To print boolean expressions you need to surround them with parenthesis

```cpp
(1 == 2)

out:
(bool) false
```

### Terminal support

To work with the current CPP interpreter, ``cling``, the ANSI
[terminal emulator](/{{ site.uprefix }}/advanced/terminal-emulation) is
enabled by default (``+term=ansi``) and cannot be disabled.

Also, the [terminal geometry](/{{ site.uprefix }}/advanced/geometry)
cannot by changed after launching the interpreter
so the option ``+geometry`` cannot be used in an example (but it can be
used from the command line)

The amount of rows of the terminal has a minimum value of 128 and this limit
is really important: if your outputs have more than 128 lines you will need
to increase the geometry or the results may be undefined.
