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

Keep in mind that an *emulated terminal* will honor its own boundaries: if
an example prints a string longer than the width of the terminal, the string
will spawn multiple lines (a newline is added automatically).

```shell
$ echo "aaaaabbbbbcccccdddddaaaaabbbbbcccccdddddaaaaabbbbbcccccddddd" # byexample: +term-emu +geometry 24x40
aaaaabbbbbcccccdddddaaaaabbbbbcccccddddd
aaaaabbbbbcccccddddd
```

