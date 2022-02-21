# Elixir

Run the `Elixir` examples calling `byexample` as:

```shell
$ byexample -l elixir your-file-here                # byexample: +skip
```

You need the default interpreter ``iex`` installed first.
Check its [download page](https://elixir-lang.org)

> **Stability**: ``unsupported`` - it may work but currently it is not
> possible to offer *any* guarantees.
> [Contributions from the community are needed!](https://github.com/byexamples/byexample/tree/master/CONTRIBUTING.md)

> **Note**: ``byexample`` will work with older version of the interpreter,
``IEx`` however it will do several *hacks*. The recommended version is
1.9.0 or superior.

## Pretty print

``byexample`` changes the default IEx's ``width`` to a smaller
value (32) so nested structures are break into multiline prints.
(pretty print).

```elixir
iex> %{:a => 1, 2 => :b, 3 => %{:c => 0, :d => %{:x => 0, :y => :e}}}
=> %{
  2 => :b,
  3 => %{
    c: 0,
    d: %{x: 0, y: :e}
  },
  :a => 1
}
```

**Note:** ``byexample`` uses ``Inspect`` to pretty print and the output of
this had changed in the past so there are not any warranties.
The output shown correspond to ``IEx`` version 1.9.2.


### The object returned

Because everything in ``Elixir`` is an expression, everything returns a result
and it is printed by ``IEx``.

This is annoying if you want to write several ``Elixir`` lines without checking
the results of each one.

For this reason, ``byexample`` suppress the representation of the object
returned unless the example has a ``=>``.

In the following case, the result of each expression is not printed and
therefor they are **not** checked:

```elixir
iex> 1 + 2

iex> IO.puts("hello")
hello
```

Now, compare it with this. It is the same example but the objects returned
are checked too.

```elixir
iex> 1 + 2
=> 3

iex> IO.puts("hello")
hello
=> :ok
```

If you want to check all the expressions, you can force to print all the
objects returned using the ``+elixir-expr-print=true``.

On the other hand, you can disable it forever
with ``+elixir-expr-print=false``.

The default is ``+elixir-expr-print=auto``.

**Note:** ``byexample`` uses ``inspect_fun`` to customize this which it is
available since ``IEx`` version 1.9. If you are stuck with an older version
you can use the ``dont_display_result`` hack.

### ``dont_display_result`` hack

For older version of ``IEx``, the only way to suppress the display of
a result is adding ``; IEx.dont_display_result`` at the end of each
``Elixir`` line.

``byexample`` can do this automatically if you enable this with
``+elixir-dont-display-hack``.

However this is a *hack* and it will not always will work.

For example, if your example ends with a comment, you will be commenting
out also the ``; IEx.dont_display_result``:

```
valid example here   # valid comment ; IEx.dont_display_result
```

Also, the ``;`` *may* create unexpected warnings.

### Terminal support

To work with the current Elixir interpreter, ``iex``, the ANSI
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

If the snippet has a very long line, greater than the terminal's width,
the last part of the line that does not fit in the terminal will be *echoed*
in the output of the example.

This is an annoying artifact due how ``iex`` works.

A simple workaround is to make the lines of the code in the snippet
shorter or increase the
[terminal width](/{{ site.uprefix }}/advanced/geometry).

### Type text

The [type](/{{ site.uprefix }}/basic/input)
feature (`+type`) is not supported.

## Elixir specific options

```
$ byexample -l elixir --show-options       # byexample: +norm-ws
<...>
elixir's specific options
-------------------------
<...>:
  +elixir-dont-display-hack
                        required for IEx < 1.9.
  +elixir-expr-print {auto,true,false}
                        print the expression's value (true); suppress it
                        (false); or print it only if the example has a =>
                        (auto, the default)
<...>
```
