# Java

Run the `Java` examples calling `byexample` as:

```shell
$ byexample -l java your-file-here                # byexample: +skip
```

You need the have installed `jshell`, an interactive interpreter
for `Java`. It is installed by default as part of the
[`openjdk`](https://openjdk.java.net/).

> **Stability**: ``experimental`` - non backward compatibility changes are
> possible or even removal between versions (even patch versions).

> *New* in ``byexample 10.3.0``.

### Versions tested

We tested `byexample` with the following versions of the language
and the underlying runner or interpreter:

<!-- matrix CI begin -->

| Language   | Runner/Interpreter   |
|------------|----------------------|
| 11         | 11.0.15              |
| 13         | 13.0.11              |
| 15         | 15.0.7               |

<!-- matrix CI end -->

## Find interactive examples

For ``Java``, ``byexample`` uses the ``j>`` string as the primary prompt
and ``..`` as the secondary prompt.


```java
j> int a = 1
j> int b = 2
j> a + b
=> 3

j> int g(int a, int b, int c) {
..   c += a;
..   c += b;
..
..   return c;
.. }

j> g(1, 2, 3)
=> 6
```

Not necessary but it is sometimes convenient to use `+norm-ws`
when printing nested data structures so the output can be arranged into
multiple lines:

```java
j> String[][] names = {             // byexample: +norm-ws
..             {"Alice", "Bob", "Charlie"},
..             {"Eve", "Mallory"}
..         };
=> String[2][] {
        String[3] { "Alice", "Bob", "Charlie" },
        String[2] { "Eve", "Mallory" }
}
```

### The object returned

Because everything in `jshell`, the interpreter of `Java`, is evaluated
as an expression, everything returns something.

This is annoying if you want to write several ``Java`` lines without checking
the results.

For this reason, ``byexample`` suppress the representation of the object
returned unless the example has a ``=>``.

In the following case, the first example is executed but the value of
its expression evaluated is not checked while in the second example
it is checked.

```java
j> 1 + 2

j> 1 + 2
=> 3
```

Notice how the second example has a `=>` to mark the value of the
expression to be compared. This mark is used by `byexample` to know when
or when not suppress the value.

This affects only the value of the expression, it has no effect on the
output of the example in general.

For example the prints are not suppressed:

```java
j> System.out.println("hello")
hello
```

You can change the behavior of `byexample` with:

 - `+java-expr-print=true` to print always the expression, disabling the
suppression
 - `+java-expr-print=false` to never print the expression.
 - `+java-expr-print=auto` to let `byexample` decide when to suppress or
not based on the mark `=>`. This is the default.

This and any other flag/option can be set in the example's comment.

```java
j> System.out.println("hello      world")       // byexample: +norm-ws
hello world
```

> Currently the flags/options can only be set in the single-line
> comments (`//`); block comments are not supported (`/* .. */`).

### Class-path and module-path

`byexample` allows you to change the *class path* and *module path*
from the command line with `+java-class-path` and `+java-module-path`.

*Modules* and *exports* can be added with `+java-add-modules` and
`+java-add-exports`.

```shell
$ byexample -l java -o '+java-class-path=test/ds/' somefiles        # byexample: +skip
```

Run `byexample -l java --show-options` for more information about those
options and their syntax. Refer to the official Java and `jshell`
documentation to know what they do exactly.


## Known limitations

### Type text

The [type](/{{ site.uprefix }}/basic/input)
feature (`+type`) is not supported.

### Terminal support

To work with the current `Java` interpreter, ``jshell``, the ANSI
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

## Java specific options

```
$ byexample -l java --show-options       # byexample: +norm-ws -capture
<...>
java's specific options
-----------------------
<...>:
  +java-expr-print {auto,true,false}
                        print the expression's value (true); suppress it
                        (false); or print it only if the example has a =>
                        (auto, the default)
  +java-class-path <path>
                        List of directories, JAR archives, and ZIP archives to
                        search for class files separated by a colon (:). On
                        Windows use a semicolon (;).
  +java-module-path <path>
                        List of directories, JAR archives, and ZIP archives to
                        search for modules separated by a colon (:). On
                        Windows use a semicolon (;).
  +java-add-modules <name>[,<name>...]
                        Root modules to resolve in addition to the initial
                        module. <name> can also be ALL-DEFAULT, ALL-SYSTEM,
                        ALL-MODULE-PATH.
  +java-add-exports <module>/<package>=<target>[,<target>...]
                        Updates <module> to export <package> to <target-
                        module>, regardless of module declaration. <target-
                        module> can be ALL-UNNAMED to export to all unnamed
                        modules. In jshell, if the <target-module> is not
                        specified then ALL-UNNAMED is used.
<...>
```
