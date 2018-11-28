<!--
Check that we have byexample installed first
$ hash byexample                                    # byexample: +fail-fast

$ alias byexample=byexample\ --pretty\ none

--
-->

# Changing the Runner: Shebang

The examples are executed by a specific runner based on the language of
the examples.

In general, the runner is an interactive interpreter like ``irb`` for ``Ruby``
or ``python`` for ``Python``.

Sometimes is convenient to change how the interpreter is executed for:
 - using another one (but compatible)
 - adding or removing environment variables
 - redirecting the standard error
 - executing it remotely

Consider the following example that prints interesting things to standard output
and debug/uninterested things to standard error:

```
$ cat test/ds/blog-database.md                          # byexample: +rm=~
~    >>> from __future__ import print_function
~    >>> import sys
~
~    >>> def load_database():
~    ...     print("Loading...")
~    ...     print("debug 314kb", file=sys.stderr)
~    ...     print("Done")
~
~    >>> load_database()
~    Loading...
~    Done
~
```

Running this will fail because the debug print will be mixed with the normal
prints and the example above expects only the *normal* outputs.

```
$ byexample -l python test/ds/blog-database.md
<...>
Expected:
Loading...
Done
Got:
Loading...
debug 314kb
Done
<...>
```

Yes, changing the example solves this but what happen if you cannot change it?

What you can do is to redirect the standard error of the interpreter,
``python`` in this case, using the ``shebang`` option:

```
$ byexample -l python \
>   --shebang "python:/bin/sh -c '%e %p %a 2>/dev/null'"  \
>   test/ds/blog-database.md
<...>
[PASS] Pass: 4 Fail: 0 Skip: 0
```

Don't be scared, the expression ``python:/bin/sh -c '%e %p %a 2>/dev/null'``
sets how to execute a runner for ``python``.

The ``%e``, ``%p``, ``%a`` tokens are replaced by ``byexample`` with the
environment, program name and arguments.

Each runner has its own set of values for those tokens.

To simplify let's assume that ``%e`` and ``%a`` are empty and ``%p``
is ``python``.

So the shebang after the substitutions is ``/bin/sh -c 'python 2>/dev/null'``

This one in turns means: spawn a ``/bin/sh`` shell with ``-c`` and
``'python 2>/dev/null'`` as arguments.

``-c`` means execute the next argument as a shell command, so this will
execute ``python 2>/dev/null`` and the ``2>/dev/null`` mean that the standard
error should be discarded.

If your shell-fu is a little rusty and the shebang is too magic, don't worry
I had the same problem; *it's for very specific situations* and you should be
away from this most of the time.

If you need more specific customization you may want to consider to
[create your own runner](docs/contrib/how-to-support-new-finders-and-languages.md).
Go ahead, it is much easier than you think.
