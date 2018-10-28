<!--
Check that we have byexample installed first
$ hash byexample                                    # byexample: +fail-fast

$ alias byexample=byexample\ --pretty\ none

--
-->

# Terminal Emulation

``byexample`` can use different emulation modes to process the output of the
runners.

By default ``byexample`` uses a *dumb terminal* (``+term=dumb``) which
it is fast and works well for most of the cases.

But you can change this to disable the emulation with ``+term=as-is`` or
to enable a full ANSI terminal emulation with ``+term=ansi``.

## Dumb terminal

In this mode, ``byexample`` emulate a very simple terminal processing
only the white spaces.

It does not have the concept of a cursor, does not
interpret escape codes and does not break lines automatically.

Even if a geometry is defined with ``+geometry``, the *dumb terminal*
does not force any boundaries: the example
can print a string longer than the width of the terminal.

```python
>>> print("aaaabbbb" * 8)      # byexample: +geometry 24x32
aaaabbbbaaaabbbbaaaabbbbaaaabbbbaaaabbbbaaaabbbbaaaabbbbaaaabbbb
```

### White space processing

The dumb terminal removes any trailing whitespace, converts to spaces the tabs
and uniforms the new lines.

This fits for most of the examples reducing the need of adding tabs into the
examples or relaxing the comparision using ``+norm-ws``.

```python
>>> print("\tfoo\tbar\nbaz\tsaz    \rtaz")
        foo     bar
baz     saz
taz
```

If you need to check those, you can use ``+term=as-is`` to disable
the terminal emulation

## As-is terminal

When ``+term=as-is`` is activated the output is passed *as is* without
any modification except for *standardize* the new lines.

It can be useful in some especial cases to check some of the white spaces
removed by the dumb or the ansi terminals.

```python
>>> print("\tfoo\tbar\nbaz\tsaz    \rtaz")       # byexample: +term=as-is
	foo	bar
baz	saz    
taz
```

## ANSI terminal

Some programs may need a real terminal or at least an
*emulated ANSI terminal*.

``byexample`` can emulate one capable of interpret and emulate
all the control sequences and escape codes using ``+term=ansi``.

> **Note:** the terminal emulation has little support in ``Python 2.7``.
> It should work but if you can use a modern ``Python`` version, better.

### Removing color

If you have an example that is printing text with color, you probably see
something like:

```shell
$ echo "\033[31mmessage in red\033[0m"
<...>[31mmessage in red<...>[0m
```

To get rid off of those weird symbols you can enable the terminal emulation:

```shell
$ echo "\033[31mmessage in red\033[0m"      # byexample: +term=ansi
message in red
```

### Terminal boundaries

Keep in mind that an *emulated terminal* will honor its own boundaries: if
an example prints a string longer than the width of the terminal, the string
will spawn multiple lines (a newline is added automatically).

```python
>>> print("aaaabbbb" * 8)      # byexample: +term=ansi +geometry 24x32
aaaabbbbaaaabbbbaaaabbbbaaaabbbb
aaaabbbbaaaabbbbaaaabbbbaaaabbbb
```

This is specially useful to work with ``ncurses`` or other
technology-like programs.

``man``, for example, uses a ``pager`` to print the manual page
that spans all the width of the terminal:

```shell
$ man python                      # byexample: +term=ansi +rm=~ +stop-on-silence
PYTHON(1)                   General Commands Manual                  PYTHON(1)
~
NAME
       python  - an interpreted, interactive, object-oriented programming lan‐
       guage
<...>
```

> Try the above example without ``+term=ansi``.

<!--
$ kill %%     # byexample: -skip +pass
-->

### Performance

The emulation it is typically 3 times slower than the normal mode
(``+term=dumb``).
Keep that in mind and try to not enable it by default.


