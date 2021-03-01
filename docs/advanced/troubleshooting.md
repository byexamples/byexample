<!--
Check that we have byexample installed first
$ hash byexample                                    # byexample: +fail-fast

$ alias byexample=byexample\ --pretty\ none

--
-->

# Troubleshooting

`byexample` does its best effort to detect common errors and display a
solution but not always is easy.

## Interpreter not found

`byexample` uses for most of the languages an *external* interpreter
which must be installed already (`byexample` will not install it)
and be available from the `PATH`.

In the following example I'm explicitly using an non-existent `python`
interpreter to show you the error:

```shell
$ byexample -l python -x-shebang 'python:python2.99' test/crash.md    # byexample: +rm= 
[w] Initialization of Python Runner failed.
[!] Something went wrong processing the file 'test/crash.md':
The command was not found or was not executable.
The full command line tried is as follows:
python2.99
 
This could happen because you do not have it installed or
it is not in the PATH.
 
Rerun with -vvv to get a full stack trace.
```

If the interpreter is installed but `byexample` cannot find it, you can
use `-x-shebang` to put an explicit path.

Something like `-x-shebang 'python:/foo/bar/python2.99'`. See more about
[-x-shebang](/{{ site.uprefix }}/advanced/shebang) to
see the complete syntax.

If you still have troubles, considere
[opening a ticket](https://github.com/byexamples/byexample/issues).

## Prompt not found / Timeout

Every example has a timeout. If `byexample` does not detect the *prompt*
from the underlying interpreter it will assume that the example hanged.

```shell
$ byexample -l python --timeout 1 --ff test/ds/too-slow.md      # byexample: +timeout=15
<...>
File "test/ds/too-slow.md", line 7
Failed example:
    sleep(1.1)
=> Execution timedout at example 3 of 5.
- This could be because the example just ran too slow (try add more time
with +timeout=<n>) or the example is "syntactically incorrect" and
the interpreter hang (may be you forgot a parenthesis or something like that?).
<...>
[FAIL] Pass: 2 Fail: 1 Skip: 2
```

A timeout can happen because the example is taking too much time or the
example is *syntactically incorrect*.

When an interpreter runs an *syntactically incorrect* example, it may
confuse and wait for more input from the user, input that it will not
receive.

Solution? Do a quick check increasing the timeout with `+timeout=N`. If
the problem disappears the example was taking too much time.

If the problem persists, it is probably a syntax error somewhere.

If the error happens in the first example or during the initialization
of the interpreter/runner, it may be an incompatibility with
`byexample`.

Consider
[opening a ticket](https://github.com/byexamples/byexample/issues) in
that case.


## Interpreter closed unexpectedly

When you run an example, `byexample` uses a interpreter or runner for
its execution depending of the language that the example was written.

If the example si Python, `byexample` will use a `python` interpreter.

The interpreter may close unexpectedly. `byexample` will detect this and
it will abort the execution.

You will see something like this:

```shell
$ byexample -l python test/crash.md    # byexample: +rm= 
<...>
File "test/crash.md", line 2
Failed example:
    exit() # I am a bad example ;)
=> Execution of example 1 of 1 crashed.
- Interpreter closed unexpectedly: the interpreter or runner closed unexpectedly.
This could happen because the example triggered a close/shutdown/exit action,
the interpreter was killed by someone else or because the interpreter just crashed.
 
If the interpreter is just crashing, it may be possible to find a workaround,
you can open an issue at https://github.com/byexamples/byexample/issues
 
=> Execution aborted at example 1 of 1.
- Some resources may had not been cleaned.
 
File test/crash.md, 1/1 test ran in <...>
[ABORT] Pass: 0 Fail: 0 Skip: 0
```

Why an interpreter may close? There are a few possibilities:

 - the example explicitly request the close of the interpreter (like in
the example above).
 - the example, somehow, typed `ctrl-D` (linux) or `ctrl-z` (windows)
which most of the interpreters see this as a close signal.
 - the interpreter was *killed* by someone else (like someone runs `kill
-15`).
 - if this happens during the *initialization* of the interpreter, may
be it is not supported by `byexample`.
 - the interpreter just crashed.

What to do? Try to write the smallest example possible that triggers the
close. You may find which piece of your example is making the close.

If the interpreter is just crashing or it is failing during the
initialization phase, consider
[opening a ticket](https://github.com/byexamples/byexample/issues). May
be it is possible to code a workaround.


