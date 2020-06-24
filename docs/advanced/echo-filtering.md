# Echo filtering

When you type something in a console or in an interactive interpreter,
what you type is *echoed* so you can see what you are typing.

`byexample` disables this so it can capture the output of an example
without having the *typed* example mixed with it.

However not all the interpreters honors this and they may leave turned on
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

Having to expect what you typed is ugly and confusing for your readers.

`byexample` has the *experimental* ability to suppress the echoing with
`+force-echo-filtering`:


```shell
$ echo "normal output"      # byexample: +force-echo-filtering
normal output
```

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

>>> set_echo_mode(True)
<...>

>>> print("normal output")
print("normal output")
normal output

>>> set_echo_mode(False)
<...>

>>> print("normal output")
normal output
```

