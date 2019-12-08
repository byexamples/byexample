<!--
Check that we have byexample installed first
$ hash byexample                                    # byexample: +fail-fast

$ alias byexample=byexample\ --pretty\ none

--
-->

# Timeout

The execution of each example has a timeout: if the example takes longer
it will abort.

This timeout can be changed of course.

```python
>>> import time
>>> time.sleep(2.5)         # byexample: +timeout=4
```

The timeout can be controlled per example with ``+timeout`` or it
can be changed from the command line with ``--timeout`` to affect the
*all* the examples.

See a timeout in action:

```
$ byexample -l python --timeout 1 --ff test/ds/too-slow.md      # byexample: +timeout=15
<...>
File "test/ds/too-slow.md", line 7
Failed example:
    sleep(1.1)
=> Execution timedout at example 3 of 5.
This could be because the example just ran too slow (try add more time
with +timeout=<n>) or the example is "syntactically incorrect" and
the interpreter hang (may be you forgot a parenthesis or something like that?).
<...>
[FAIL] Pass: 2 Fail: 1 Skip: 2
```

## Why an example could timeout?

The first reason could be that the example is just too slow.

Try to increase the timeout to a larger number and see if it works;
if not, then it is something else.

Another reason could be that the example is *syntactically incorrect*
or *incomplete* and the underlying interpreter is waiting for more
input.

Something like this incomplete ``Python`` print:

```python
>>> print("some...              # byexample: +skip
```

> The use of ``+skip`` is for testing purposes only, otherwise
> the example would timeout of course.

## Recovery of a timeout

A timeout is considered a critical issue.

When an example fails due a timeout, ``byexample`` has no control
over the runner and it will try to *recover it back* typically
sending an *interrupt* or ``ctrl-c`` to the runner.

If ``byexample`` recovers the control, the execution resumes and
continues as usual.

But if not, the interpreter may hang for a long time or forever
so further executions will timeout too.

In this case the execution is *aborted*.

No other example will be executed nor even if they have the ``-skip`` option
which can be problematic for the
[cleaning up](/{{ site.uprefix }}/basic/setup-and-tear-down) process.

If the recovery is a problem, you can disable it with
``-x-not-recover-timeout``.

Compare the output of the following example with the previous one. Note
how the rest of the examples are *not executed* at all and that
the final status is ``ABORT``

```
$ byexample -l python --timeout 1 --ff -x-not-recover-timeout test/ds/too-slow.md      # byexample: +timeout=10
<...>
File "test/ds/too-slow.md", line 7
Failed example:
    sleep(1.1)
=> Execution timedout at example 3 of 5.
This could be because the example just ran too slow (try add more time
with +timeout=<n>) or the example is "syntactically incorrect" and
the interpreter hang (may be you forgot a parenthesis or something like that?).
<...>
=> Execution aborted at example 3 of 5.
Some resources may had not been cleaned.
<...>
[ABORT] Pass: 2 Fail: 1 Skip: 0
```

> **New** in ``byexample 8.0.0``: before, a timeout had always
> ended in an abort.

> **Note:** the ability of recovering depends of each interpreter or runner.
> See their documentation for more details.
