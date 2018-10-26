<!--
Check that we have byexample installed first
$ hash byexample                                    # byexample: +fail-fast

$ alias byexample=byexample\ --pretty\ none

--
-->

# ANSI Terminal Emulation

``byexample`` uses a *virtual terminal* with a defined geometry but it does
not add any further semantic nor put limits or boundaries: the example
can print a string longer than the width of the terminal.

But some programs may need a real terminal or at least an
*emulated terminal*.

``byexample`` can emulate an ANSI Terminal capable of interpret and emulate
all the control sequences and escape codes.

> **Note:** the terminal emulation has little support in ``Python 2.7``.
> It should work but if you can use a modern ``Python`` version, better.

## Removing color

If you have an example that is printing text with color, you probably see
something like:

```shell
$ echo "\033[31mmessage in red\033[0m"
<...>[31mmessage in red<...>[0m
```

To get rid off of those weird symbols you can enable the terminal emulation:

```shell
$ echo "\033[31mmessage in red\033[0m"      # byexample: +term-emu
message in red
```

## Terminal boundaries

Keep in mind that an *emulated terminal* will honor its own boundaries: if
an example prints a string longer than the width of the terminal, the string
will spawn multiple lines (a newline is added automatically).

```shell
$ echo "aaaaabbbbbcccccdddddaaaaabbbbbcccccdddddaaaaabbbbbcccccddddd" # byexample: +term-emu +geometry 24x40
aaaaabbbbbcccccdddddaaaaabbbbbcccccddddd
aaaaabbbbbcccccddddd
```

This is specially useful to work with ``ncurses`` or other
technology-like programs.

``man``, for example, uses a ``pager`` to print the manual page
that spans all the width of the terminal:

```shell
$ man python                      # byexample: +term-emu +rm=~ +stop-on-silence
PYTHON(1)                   General Commands Manual                  PYTHON(1)
~
NAME
       python  - an interpreted, interactive, object-oriented programming lan‐
       guage
<...>
```

> Try the above example without ``+term-emu``.

<!--
$ kill %%     # byexample: -skip +pass
-->

## Performance

The emulation it is typically 3 times slower than the normal mode.
Keep that in mind and try to not enable it by default.

