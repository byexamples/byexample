<!--
Check that we have byexample installed first
$ hash byexample                                    # byexample: +fail-fast

$ alias byexample=byexample\ --pretty\ none

--
-->

# Compatibility with Python Doctest

`byexample` is fully compatible with
[doctest](https://docs.python.org/3/library/doctest.html)

Take for the example this same document that you are reading:
it has `doctest` examples that can be executed with both `doctest` and
`byexample`.

Execute it with `doctest`:

```shell
$ python -m doctest -v docs/recipes/python-doctest.md   # byexample: +skip
```

Execute it with `byexample`, with the compatibility mode enabled:

```shell
$ byexample -l python -o '+py-doctest' docs/recipes/python-doctest.md   # byexample: +skip
```

## Brief introduction

Like `doctest`, `byexample` uses `>>>` to detect the examples to execute
and test:

```python
>>> def factorial(n):
...     if n <= 2:
...         return n
...     return n * factorial(n-1)

>>> factorial(5)
120

```

`doctest` is designed to find the examples in the `docstrings` of Python
code or text files. `byexample` goes a little beyond and can find the
examples in the `code-fenced` blocks of Markdown, HTML and others.

This is very important. If you see the original markdown of this file,
you will see in the examples inside of `code-fenced` blocks.

`doctest` has no notion of this and it will not distinguish where an
example ends and it will confuse the ending part of the `code-fenced`
block with the expected output of the example.

The solution? Add a new line at end of the example.

`byexample` since `8.0.0` has not this limitation.

Output is captured as well; `byexample` also captures the standard
error.

```python
>>> def knights(n):
...     print('\n\n'.join("Ni!\nNi! Ni!" for i in range(n)))

>>> knights(1)
Ni!
Ni! Ni!

```

## Tracebacks

When a traceback is expected, `doctest` ignores the header which may
differ depending of the context:

```python
>>> [1, 2, 3].remove(42)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ValueError: list.remove(x): x not in list

>>> [1, 2, 3].remove(42)
Traceback (innermost last):
  File "<stdin>", line 1, in <module>
ValueError: list.remove(x): x not in list

```

The call stack is ignored by `doctest`. Most of the time you want to
omit it or replace it by `...` or something else:

```python
>>> [1, 2, 3].remove(42)
Traceback (most recent call last):
ValueError: list.remove(x): x not in list

>>> [1, 2, 3].remove(42)
Traceback (most recent call last):
  ...
ValueError: list.remove(x): x not in list

>>> [1, 2, 3].remove(42)
Traceback (most recent call last):
  :::
ValueError: list.remove(x): x not in list

```

In some occasions the details of the traceback are too specific and you
can omit them too enabling the `IGNORE_EXCEPTION_DETAIL` option:

```python
>>> [1, 2, 3].remove(42)        # doctest: +IGNORE_EXCEPTION_DETAIL
Traceback (most recent call last):
ValueError: element not found

```

Under the hood `byexample` treats all these special cases as the same
and uses [capture tags](/{{ site.uprefix }}/basic/capture-and-paste).

## Ellipsis

`doctest` has the ability to ignore part of an output with `...`. This
is enabled with the `ELLIPSIS` option:

```python
>>> knights(8)      # doctest: +ELLIPSIS
Ni!
...
Ni! Ni!

```

It is super useful when you want to ignore long and boring outputs or
small but unpredictable output.

A classic example is a decimal number which last digits may not be the
same across all the platforms.

```python
>>> 1./7            # doctest: +ELLIPSIS
0.142857...

```

One of the drawback of `doctest` is that if an example fails, the diff
generated may be hard to debug if the expected output is large and it
has some ellipsis:

This is one example. Can you spot where is the difference?

```shell
$ python -m doctest -o REPORT_NDIFF  test/ds/doctest-hard-diff.md	# byexample: +tags
<...>
Differences (ndiff with -expected +actual):
    - {'debugger-id': ...
    ?                 ^^^
    + {'debugger-id': 4641,
    ?                 ^^^^^
    -  'results': {'bkpts': [{'addr': ...,
    ?                                 ^^^
    +  'results': {'bkpts': [{'addr': '0x18172',
    ?                                 ^^^^^^^^^
                              'file': 'example.c',
    -                         'fullname': ...,
    +                         'fullname': 'workdir-random-path-here/example.c',
                              'func': 'main',
                              'line': '5',
    -                         'original-location': ...,
    ?                                              ^^^
    +                         'original-location': 98674,
    ?                                              ^^^^^
                              'thread': ['1', '1'],
    -                         'thread-group': ['i1'],
    +                         'thread-groups': ['i1'],
    ?                                      +
                              'times': '0',
                              'type': 'breakpoint'}]},
       'type': 'Sync'}
<...>

```

Super hard! The problem is that `doctest` treats the `...` as literals
at the moment of calculating the diff. Therefore it generates a lot of
differences that are not real.

`byexample` instead uses [capture tags](/{{ site.uprefix }}/basic/capture-and-paste):
they don't just ignore part
of the outputs but they capture them and when a diff is calculated they
are used to reduce the differences.

This is the same run but with `byexample` with the compatibility mode
enabled:

```shell
$ byexample -l python -o '+py-doctest' --diff ndiff test/ds/doctest-hard-diff.md    # byexample: +rm=~ +tags
<...>
Differences:
  {'debugger-id': 4641,
   'results': {'bkpts': [{'addr': '0x18172',
                          'file': 'example.c',
                          'fullname': 'workdir-random-path-here/example.c',
                          'func': 'main',
                          'line': '5',
                          'original-location': 98674,
                          'thread': ['1', '1'],
-                         'thread-group': ['i1'],
+                         'thread-groups': ['i1'],
?                                      +
~
                          'times': '0',
                          'type': 'breakpoint'}]},
   'type': 'Sync'}
<...>
```

What a typo!! Easier to spot it now, eh?

The [capture tags](/{{ site.uprefix }}/basic/capture-and-paste)
allows you to capture and [paste](/{{ site.uprefix }}/basic/capture-and-paste)
the captured
text later. But advanced used of these are not available in the
compatibility mode with `doctest`.

## Reports

Known also as "comparison flags", `doctest` and `byexample` supports
different ways to present the differences when an example fails.

These are: `REPORT_UDIFF`, `REPORT_CDIFF` and the already shown
`REPORT_NDIFF`.

You can enable one of them per example or globally from the command
line:

```shell
$ byexample -l python -o '+py-doctest +REPORT_CDIFF' test/ds/doctest-hard-diff.md  # byexample: +tags
<...>
Differences:
*** 7,11 ****
                          'original-location': 98674,
                          'thread': ['1', '1'],
!                         'thread-group': ['i1'],
                          'times': '0',
                          'type': 'breakpoint'}]},
--- 7,11 ----
                          'original-location': 98674,
                          'thread': ['1', '1'],
!                         'thread-groups': ['i1'],
                          'times': '0',
                          'type': 'breakpoint'}]},
<...>

$ byexample -l python -o '+py-doctest +REPORT_UDIFF' test/ds/doctest-hard-diff.md   # byexample: +tags
<...>
Differences:
@@ -7,5 +7,5 @@
                         'original-location': 98674,
                         'thread': ['1', '1'],
-                        'thread-group': ['i1'],
+                        'thread-groups': ['i1'],
                         'times': '0',
                         'type': 'breakpoint'}]},
<...>
```

In general if you want to enable them globally, you may want to use
the `--diff` command line option which it is more powerful:

```shell
$ byexample -l python -o '+py-doctest' --diff ndiff test/ds/doctest-hard-diff.md    # byexample: +rm=~ +tags
<...>
Differences:
  {'debugger-id': 4641,
   'results': {'bkpts': [{'addr': '0x18172',
                          'file': 'example.c',
                          'fullname': 'workdir-random-path-here/example.c',
                          'func': 'main',
                          'line': '5',
                          'original-location': 98674,
                          'thread': ['1', '1'],
-                         'thread-group': ['i1'],
+                         'thread-groups': ['i1'],
?                                      +
~
                          'times': '0',
                          'type': 'breakpoint'}]},
   'type': 'Sync'}
<...>
```

<!--
Hide this from the public webpage. These are here to make sure that
byexample can understand those flags but not further testing is done.

>>> factorial(5)        # doctest: +REPORT_UDIFF
120

>>> factorial(5)        # doctest: +REPORT_CDIFF
120

>>> factorial(5)        # doctest: +REPORT_NDIFF
120

#>>> factorial(5)        # doctest: +REPORT_ONLY_FIRST_FAILURE
#120

-->

There is also a `REPORT_ONLY_FIRST_FAILURE` option that shows the first
failure but suppress the rest.

The examples are still executed and validated but any further failure is
not shown.

```shell
$ byexample -l python -o '+py-doctest +REPORT_ONLY_FIRST_FAILURE' test/ds/doctest-hard-diff.md  # byexample: +tags
<...>
File test/ds/doctest-hard-diff.md, 5/5 test ran in <...> seconds
[FAIL] Pass: 3 Fail: 2 Skip: 0
```


## Whitespace

`doctest` and `byexample` are very strict when they compare the outputs.
Any extra space will make the test fail.

You can relax this with `NORMALIZE_WHITESPACE`:

```python
>>> knights(1)          # doctest: +NORMALIZE_WHITESPACE
Ni!    Ni!    Ni!

```

If the example has empty lines, you need to glue the text with
`<BLANKLINE>`

```python
>>> knights(2)
Ni!
Ni! Ni!
<BLANKLINE>
Ni!
Ni! Ni!

```

If you literally want to check for the `<BLANKLINE>` string, you can
disable the feature with `DONT_ACCEPT_BLANKLINE`:

```python
>>> print("<BLANKLINE>")    # doctest: +DONT_ACCEPT_BLANKLINE
<BLANKLINE>

```

# Skip and Fast Fail

An example can be skipped with `SKIP`: the example is not executed at
all:

```python
>>> destroy_world()         # doctest: +SKIP
True

```

On the other hand, if an example has the `FAIL_FAST` option and it
fails, all the remaining examples will be skipped.

`byexample` is more versatile than just [skip](/{{ site.uprefix }}/basic/skip-and-pass):
you can [pass](/{{ site.uprefix }}/basic/skip-and-pass) an example
(execute it but do not check it), you cannot force to
[not skip](/{{ site.uprefix }}/basic/skip-and-pass) an example (execute it
unconditionally) or execute it only if a
[condition is met](/{{ site.uprefix }}/advanced/conditional-execution).


<!--
Ensure that "FAIL_FAST" is tested

$ byexample -l python -o '+py-doctest +FAIL_FAST' test/ds/doctest-hard-diff.md  # byexample: +tags
<...>
File test/ds/doctest-hard-diff.md, 5/5 test ran in <...> seconds
[FAIL] Pass: 3 Fail: 1 Skip: 1

-->


## Migration to the ``byexample``'s way

As you can see ``byexample`` in non-compatibility mode
uses a different set of options. Here is a summary of the equivalent options:

```
====================  ============================  ============================
``byexample``         ``doctest``                   Observations
====================  ============================  ============================
``norm-ws``           ``NORMALIZE_WHITESPACE``      Same functionality.
*not supported*       ``DONT_ACCEPT_TRUE_FOR_1``    Only useful for ``Python 2.3``.
``tags``              ``ELLIPSIS``                  More powerful than ``doctest`` version
``skip``              ``SKIP``                      Same functionality.
``pass``              *not supported*               Execute but do not check.
``tags``              ``IGNORE_EXCEPTION_DETAIL``   ``tags`` is more general
``tags`` or ``rm``    ``DONT_ACCEPT_BLANKLINE``     ``rm`` may be used instead of ``tags``.
``diff``              ``REPORT_UDIFF``              With ``unified`` as argument.
``diff``              ``REPORT_CDIFF``              With ``context`` as argument.
``diff``              ``REPORT_NDIFF``              With ``ndiff`` as argument.
``fail-fast``         ``FAIL_FAST``                 Same functionality.
``show-failures`      ``REPORT_ONLY_FIRST_FAILURE`` Same as `+show-failures 1`
====================  ============================= ============================
```

See [norm-ws](/{{ site.uprefix }}/basic/normalize-whitespace),
[tags](/{{ site.uprefix }}/basic/capture-and-paste),
[skip](/{{ site.uprefix }}/basic/skip-and-pass),
[pass](/{{ site.uprefix }}/basic/skip-and-pass) and
[diff](/{{ site.uprefix }}/overview/differences) for more info.
