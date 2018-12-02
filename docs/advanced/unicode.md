<!--
Check that we have byexample installed first
$ hash byexample                                    # byexample: +fail-fast

$ alias byexample=byexample\ --pretty\ none

--
-->

# Unicode Support

``byexample`` has full support for unicode examples.

```shell
$ echo "por ejemplo"
por ejemplo

$ echo "по примеру"
по примеру

$ echo "例によって"
例によって
```

If an example fails, ``byexample`` will show you the differences.
These also work if the output is unicode.

Consider the following examples in ``test/ds/bad-unicode.md``:

```shell
$ cat test/ds/bad-unicode.md            # byexample: +rm=~
~Those would fail:
~
~$ echo "por-éjemplo"
~por ejemplo
~
~$ echo "по-примеру!"
~по примеру
~
~$ echo "例によっ!て"
~例によって

```

Here are those examples failing:

```shell
$ byexample -l shell,python --diff ndiff test/ds/bad-unicode.md    # byexample: +rm=~
<...>
Differences:
- por ejemplo
?    ^^
~
+ por-éjemplo
?    ^^
<...>
Differences:
- по примеру
?   ^
~
+ по-примеру!
?   ^       +
<...>
Differences:
- 例によって
+ 例によっ!て
?     +
<...>
```

**Note:** the [``ndiff`` algorithm](/{{ site.uprefix }}/overview/differences)
will not put the marker ``+`` in the correct position
if the characters are *wide characters*.

## Encoding

By default, ``byexample`` will use the same encoding that ``Python`` uses
for its standard output, typically ``utf-8``.

You can change the encoding from the command line with ``--encoding``:

```shell
$ byexample -l shell --encoding utf-8 test/ds/bad-unicode.md
<...>
Expected:
por ejemplo
Got:
por-éjemplo
<...>
Expected:
по примеру
Got:
по-примеру!
<...>
Expected:
例によって
Got:
例によっ!て
<...>
```

## Limitations

If you are running ``byexample`` using ``Python 2.7`` *and* you
enable the [ANSI terminal emulation](/{{ site.uprefix }}/advanced/terminal-emulation)
with ``+term=ansi``, any non-ascii character will be removed.

This is a limitation of one of the ``byexample``'s dependencies and
only apply under that specific scenario.

