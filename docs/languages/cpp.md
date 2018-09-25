# C++

To support C++, ``byexample`` relays in the ``cling`` interpreter.

You need to have [cling](https://github.com/root-project/cling) installed first.

It is still an **experimental** feature that works pretty well but it is not
immune to bugs, quirks nor crashes.

Don't forget to send your feedback to the ``cling`` community.

## Variable definition

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

## stdlib

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

## Gotchas

To print boolean expressions you need to surround them with parenthesis

```cpp
(1 == 2)

out:
(bool) false
```
