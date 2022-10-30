<!--
Check that we have byexample installed first
$ hash byexample                                    # byexample: +fail-fast

# Make byexample to not turn-off the echo for testing some examples here
$ alias byexample=byexample\ --pretty\ none\ -x-turn-echo-off\ no

--
-->
# Echo filtering

When you type something in a console or in an interactive interpreter,
what you type is *echoed* so you can see what you are typing.

`byexample` disables this so it can capture the output of an example
without having the *typed* example mixed with it.

However not all the interpreters honor this and they may leave turned on
the echo anyway.

For example this shell example uses `stty` to re-enable the echoing:

```shell
$ echo "normal output"
normal output

$ stty echo

$ echo "normal output"
echo "normal output"
normal output
```

> *Changed* in `byexample 11.0.0`: since `11.0.0`, the echo is disabled
> before executing each example. This makes the execution more robust
> against changes in the terminal settings.
> Before `11.0.0` the echo was disabled only on the interpreter startup
> only.
> You may change this using `-x-turn-echo-off` but be careful.

Having to expect what you typed is ugly and confusing for your readers.

`byexample` has the *experimental* ability to suppress the echoing with
`+force-echo-filtering`:


```shell
$ echo "normal output"      # byexample: +force-echo-filtering
normal output
```

You can pass `+force-echo-filtering` from the command line to take effect
on all the examples of all the languages but this is not encouraged
and since `byexample 11.0.0` you can enforce the echo filtering
per language with `+force-echo-filtering-for`

```shell
$ byexample -l shell,python -o "+force-echo-filtering-for=shell" test/ds/echo-filtering-required.md      # byexample: +timeout 8
<...>
File test/ds/echo-filtering-required.md, <...> seconds
[PASS] <...>
```

Both `+force-echo-filtering` and `+force-echo-filtering-for` from the
command line is not allowed.

```shell
$ byexample -l shell,python -o "+force-echo-filtering-for=shell +force-echo-filtering" test/ds/echo-filtering-required.md      # byexample: +timeout 8
<...>
argument +force-echo-filtering: not allowed with argument +force-echo-filtering-for
<...>
```

> *New* in `byexample 11.0.0`: before `11.0.0`, the only way to apply
> the filtering to all the examples was using `+force-echo-filtering`
> from the command line but unfortunately that affects all the rest
> of interpreters that may not require the filtering.
>
> Since `11.0.0` you should use `+force-echo-filtering-for` in the command
> line to affect all the examples of the language(s) selected and
> use `+force-echo-filtering` **only** when you want to enable the
> filtering in a particular example.


## Limitations and restrictions

Forcing a filtering comes with some restrictions:
 - the example will use a full [terminal emulation](/{{ site.uprefix}}/advanced/terminal-emulation),
   in other words `+force-echo-filtering` implies `+term=ansi`.
 - due the emulation, your output will be limited by the
   [geometry](/{{ site.uprefix }}/advanced/geometry)
   of the emulated terminal; you may have to set this too at the begin
   of your document.
 - the echo must exist otherwise the filter may filter part of your
   output.
 - it is an *experimental* feature.

If possible, try to disable the echo from the interpreter itself and
relay on `+force-echo-filtering` as a last resort.

For example, in `python` you can use `termios` to control the echoing:

```python
>>> import sys
>>> from termios import tcgetattr, tcsetattr, TCSANOW, ECHO

>>> def set_echo_mode(enable):
...     fd = sys.stdin.fileno()
...     attrs = tcgetattr(fd)
...
...     if enable:
...         attrs[3] |= ECHO
...     else:
...         attrs[3] &= ~ECHO
...
...     tcsetattr(fd, TCSANOW, attrs)

>>> set_echo_mode(False)
<...>
```

