<!--
Check that we have byexample installed first
$ hash byexample                                    # byexample: +fail-fast

$ alias byexample=byexample\ --pretty\ none

--
-->

# Unicode support

``byexample`` has full support for unicode.

Here are some examples:

```shell
$ echo "por ejemplo"
por ejemplo

$ echo "по примеру"
по примеру

$ echo "例によって"
例によって
```

The diff is also supported. Consider the following examples
quite similar the previous but with small differences:

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
$ byexample -l shell --diff ndiff test/ds/bad-unicode.md    # byexample: +rm=~
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

**Note:** you may noticed, the ``ndiff`` algorithm will not put the marker ``+``
in the correct position if the characters are *wide characters*.

The following should fail too and its diff
should show a pretty ? marker (see enhance-diff)

>>> print("\x00\x1ffoo\x7f")
xxfoox

$ echo "\0777"
