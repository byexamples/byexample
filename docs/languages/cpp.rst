C++
===

To support C++, ``byexample`` relays in the ``cling`` interpreter.

You need to have `cling <https://github.com/root-project/cling>`_ installed first.

It is still an **experimental** feature that works pretty well but it is not
immune to bugs, quirks nor crashes.

Don't forget to send your feedback to the ``cling`` community.

Variable definition
-------------------

All the variable are global and can be accessed by other examples

.. code:: cpp

    ```cpp
    double radio = 2.0;
    double sup = 3.14 * (radio * radio);

    sup

    out:
    (double) 12.56<...>

    ```

The last expression with out ending by ';' is interpreted by ``cling`` as the
expression to not only eval but also to print its value.

stdlib
------

You can use the ``stdlib`` as usual. Here is an example of how to print something
and check the output later:

.. code:: cpp

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

