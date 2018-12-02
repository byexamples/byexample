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
import time
time.sleep(2.5) # simulates a slow operation # byexample: +timeout=4
```

The timeout can be controlled per example with ``+timeout`` or it
can be changed from the command line with ``--timeout`` to affect the
all the examples.

See a timeout in action:

```
$ byexample -l python --timeout 0.0001 --ff test/ds/python-tutorial.v1.md
<...>
File "test/ds/python-tutorial.v1.md", line 4
Failed example:
    from __future__ import print_function
=> Execution timedout at example 1 of 4.
This could be because the example just ran too slow (try add more time
with +timeout=<n>) or the example is "syntactically incorrect" and
the interpreter hang (may be you forgot a parenthesis or something like that?).
<...>
[ABORT] Pass: 0 Fail: 0 Skip: 0
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

## Abort

A timeout is considered a critical issue and it will *abort* the execution.

This is because the interpreter may still hang so further executions
will timeout too.

No other example will be executed nor even if they have the ``-skip`` option
which can be problematic for the
[cleaning up](/{{ site.uprefix }}/basic/setup-and-tear-down) process.
