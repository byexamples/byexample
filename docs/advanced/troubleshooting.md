<!--
Check that we have byexample installed first
$ hash byexample                                    # byexample: +fail-fast

$ alias byexample=byexample\ --pretty\ none

--
-->

# Troubleshooting

`byexample` does its best effort to detect common errors and display a
solution but not always is easy.

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
 - the interpreter just crashed.

What to do? Try to write the smallest example possible that triggers the
close. You may find which piece of your example is making the close.

If the interpreter is just crashing, considere
[opening a ticket](https://github.com/byexamples/byexample/issues). May
be it is possible to code a workaround.


