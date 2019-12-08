<!--
Check that we have byexample installed first
$ hash byexample                                    # byexample: +fail-fast

$ alias byexample=byexample\ --pretty\ none

--
-->

# Unicode Support

``byexample`` has full support for unicode examples.

```shell
$ echo 'por ejemplo'
por ejemplo

$ echo 'по примеру'
по примеру

$ echo '例によって'
例によって
```

If an example fails, ``byexample`` will show you the differences.
This also works if the output is unicode.

Consider the following examples in ``test/ds/bad-unicode``:

```shell
$ cat test/ds/bad-unicode            # byexample: +rm=~
~Those would fail:
~
~$ echo 'por-éjemplo'
~por ejemplo
~
~$ echo 'по-примеру!'
~по примеру
~
~$ echo '例によっ!て'
~例によって

```

Here are those examples failing:

```shell
$ byexample -l shell,python --diff ndiff test/ds/bad-unicode    # byexample: +rm=~
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
will not put the ``+`` marker in the correct position
if the characters are *wide characters*.

## Encoding

By default, ``byexample`` will use the same encoding that ``Python`` uses
for its standard output, typically ``utf-8``.


You can change the encoding from the command line with ``--encoding``:

```shell
$ byexample -l shell --encoding utf-8 test/ds/bad-unicode
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

The ``--encoding`` option only affects how to decode the files read.

The output that ``byexample`` prints is still interpreted using
the ``Python`` default encoding for the standard output.

If you want to change this behaviour set the environment
variable ``PYTHONIOENCODING``.

```shell
$ PYTHONIOENCODING='utf-8' byexample -l shell test/ds/bad-unicode | cat
<...>
Expected:
por ejemplo
Got:
por-éjemplo
<...>
```

> If you are using ``Python 2.7`` and you are redirecting the output of
> ``byexample`` to a file or pipe you will get an error saying that
> the encoding of the standard output is unset.
>
> This is a known issue of ``Python 2.x`` series which ignores the encoding of
> your terminal.
>
> The solution is to use ``PYTHONIOENCODING`` like before.

## Limitations

If you are running ``byexample`` using ``Python 2.7`` *and* you
enable [ANSI terminal emulation](/{{ site.uprefix }}/advanced/terminal-emulation)
with ``+term=ansi``, any non-ascii characters will be removed.

This is a limitation of one of ``byexample``'s dependencies and
only applies under that specific scenario.

``Python 2.x`` reached to its *end of life* in January 2020. Consider
upgrade it.
