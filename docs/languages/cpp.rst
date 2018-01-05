C/C++
=====

Let's play with some basic maths. What is the surface of a circle?

TODO
The last line of code, if it is an expression, it will evaluated and
the output compared with the expected below
OR mark it with ".p"

.. code:: cpp

    ```cpp
    double radio = 2.0;
    double sup = 3.14 * (radio * radio);
    
    sup
    
    out:
    (double) 12.56<...>
    
    ```

Cool but ``3.14`` it isn't the most precise approximation to the number PI.
We could do this better.

Preprocessors are supported as well and affect the example and all the examples
below.

To add more linking flags, the ``+LINK`` option is used. This flag affects this
example and all the examples below as well.

.. code:: cpp

    ```cpp
    #include <math.h>  /* byexample: +LINK=-lm */
    #define PI 3.141592653589793
    
    radio = 2.0;
    sup = PI * pow(radio, 2);
    
    sup
    
    out:
    (double) 12.56<decimals>
    ```

We could refactor this into a function

.. code:: cpp

    ```cpp
    double circle_surface(double radio) {
        return PI * pow(radio, 2);
    }
    
    circle_surface(radio)
    
    out:
    (double) 12.56<decimals>
    ```

Let's calculate the surface of several circles

.. code:: cpp

    ```cpp
    double j = 0;
    int i;
    for (i = 1; i < 4; ++i)
        j += circle_surface(i);
    
    j
    
    out:
    (double) 50.26<...>
    ```


TODO
====
See -fvisibility=
