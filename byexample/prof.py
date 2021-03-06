from time import perf_counter as mark
import contextlib, functools, inspect
import os.path
import os
'''
This module implements a "deterministic profiler".

To use it, you need to enable the engine first (it should
be enabled by default if the environment variable "BYEXAMPLE_PROFILE"
is "1"):

>>> import byexample.prof
>>> byexample.prof.enabled = True

Only then you can start doing the instrumentation.

>>> import time
>>> from byexample.prof import profile
>>> @profile
... def foo():
...     time.sleep(0.1)

On a call, the wrapped function will print an one-line stack trace
with the elapsed time in nanoseconds:

>>> foo()           # byexample: +timeout=8
stdin>::foo 10<...>

The function name is prefixed by the name of the module. In this case,
"stdin>".

Nested profiled functions will print a larger stack trace:

>>> @profile
... def gus():
...     time.sleep(0.2)
...     foo()

>>> gus()           # byexample: +timeout=8 +paste
stdin>::gus;stdin>::foo 10<...>
stdin>::gus 20<...>

Two one-liner stack traces were printed: one for foo() called from
gus() and the other for gus() only.

The time shown is the "self time": the time that the function took
without counting the time spent in a profiled child.

In this case gus() took 3 seconds: 2 due itself and 1 due foo().

Non-profiled children are *not* taken into account and their
time is *added* to the closest profiled ancestral. This is what happen
with the call to 'time.sleep': there was no trace for it and its
time was added to foo() and gus().

Sometimes you want to profile a part of a function. You can
use a context manager for that.

>>> from byexample.prof import profile_ctx

>>> def bar():
...     time.sleep(0.1)
...     with profile_ctx():
...         time.sleep(0.2)

>>> bar()           # byexample: +timeout=8
stdin>::bar 20<...>

By default the context manager uses the name of the calling function
for the stack trace.

You can add a name to it which it is handy to differentiate two context
managers from the same function:

>>> def baz():
...     with profile_ctx("head"):
...         time.sleep(0.1)
...     with profile_ctx("tail"):
...         time.sleep(0.2)

>>> baz()           # byexample: +timeout=8
stdin>::baz::head 10<...>
stdin>::baz::tail 20<...>

Nested is possible too:

>>> @profile
... def nested():
...     time.sleep(0.1)
...     with profile_ctx():
...         time.sleep(0.2)
...         with profile_ctx():
...             time.sleep(0.3)

>>> nested()           # byexample: +timeout=8
stdin>::nested;stdin>::nested;stdin>::nested 30<...>
stdin>::nested;stdin>::nested 20<...>
stdin>::nested 10<...>
'''

enabled = os.getenv("BYEXAMPLE_PROFILE", "0") != "0"

_callees_measures = [0]
_call_stack = []


@contextlib.contextmanager
def profile_ctx(name=None, _func=None):
    ''' Profile the given code and emit a call trace of
        the ancestors calling callers that are being profiled
        too.

        For the top most function of the call trace, it will
        be used the function that has this context manager.

        More than one context manager can be put in a single
        function (even nested context managers).

        In that case, the optional parameter '<name>' can be used
        to add suffix to differentiate one manager from other
        in the call traces.

        The internal (private) <_func> servers to use that function
        instead of the calling function for the same purpose.
        '''
    global _callees_measures
    global _call_stack
    global enabled

    if not enabled:
        yield
        return

    ini_mark = mark()
    _callees_measures.append(0)

    # If we have a function it means that we are being
    # called from the profile decorator
    if _func:
        assert name is None
        name = _name_from_func(_func)
    else:
        # We have the following situation:
        # def func():
        #   with profile_ctx():
        #     bar()
        # And we want to know the name of "func()" from profile_ctx's __enter__
        # so we need to inspect the stack and ignore the 2 top most elements
        # which are profile_ctx's __enter__ and profile_ctx.
        # The next element below is going to be our func()
        frame = inspect.stack(context=0)[:3][-1]
        parent_name = _name_from_frame(frame)

        # Optionally add the name of the context manager (user defined)
        if name:
            name = parent_name + '::' + name
        else:
            name = parent_name

    assert name
    name = name.replace("<", "")
    _call_stack.append(name)

    begin_mark = mark()
    try:
        yield
    finally:
        end_mark = mark()

        # Build a "stack trace"
        stack = ';'.join(_call_stack)

        # pop "func" name
        _call_stack.pop()

        # calculate the total elapsed time (temporal)
        elapsed = round(
            (end_mark - begin_mark) * 1000000000
        )  # elapsed time in nanoseconds

        # how much time our children (callees) spent
        ours = _callees_measures.pop()

        # calculate the "self" elapsed time
        elapsed -= ours
        assert elapsed >= 0

        # print
        print("%s %i" % (stack, elapsed))
        del stack

        # notify to our parent (caller) how much time we spent
        # including the time spent by the profile instrumentation
        callee_t = round(
            (mark() - ini_mark) * 1000000000
        )  # elapsed time in nanoseconds
        _callees_measures[-1] += callee_t


def _name_from_frame(frame):
    P = os.path
    return P.splitext(P.basename(frame.filename))[0] + '::' + frame.function


def _name_from_func(func):
    P = os.path
    try:
        filename = inspect.getfile(func)
        prefix = P.splitext(P.basename(filename))[0]
    except:
        prefix = '??'

    return prefix + '::' + func.__name__


def profile(func):
    global enabled
    if not enabled:
        return func

    @functools.wraps(func)
    def wrapped(*args, **kargs):
        with profile_ctx(_func=func):
            return func(*args, **kargs)

    return wrapped
