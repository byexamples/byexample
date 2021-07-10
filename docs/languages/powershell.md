<!--
Check that we have byexample installed first
$ hash byexample                                    # byexample: +fail-fast
$ hash pwsh                                         # byexample: +fail-fast

$ alias byexample=byexample\ --pretty\ none

--
-->

# PowerShell

``byexample`` supports Microsoft's ``PowerShell``.

Run the Microsoft's `PowerShell` examples calling `byexample` as:

```shell
$ byexample -l pwsh your-file-here                # byexample: +skip
```

Currently `byexample` only supports the version for Linux that
you can install from the [official
site](https://docs.microsoft.com/en-us/powershell/scripting/install/installing-powershell-core-on-linux)).

To run the `PowerShell` examples in a file you need to select `pwsh` as
the language:

```shell
$ byexample -l pwsh docs/languages/powershell.md    # byexample: +timeout=8
<...>
[PASS] Pass: <...>
```

> **Stability**: ``experimental`` - non backward compatibility changes are
> possible or even removal between versions (even patch versions).

> *New* in ``byexample 10.1.0``.

## Find interactive examples

For ``PowerShell``, ``byexample`` uses the ``PS>`` string as the primary prompt
and ``-->`` as the secondary prompt.

```shell
PS> $ComputerName = 'DC01', 'WEB01'

PS> foreach ($Computer in $ComputerName) {
-->    echo $Computer
--> }
DC01
WEB01
```

### Syntax errors

Syntax errors are detected and can be part of the example. The format of
the message will depend of the version of `PowerShell` however.

```shell
PS> echo @"this
ParserError:
Line |
   1 |  echo @"this
     |         ~
     | No characters are allowed after a here-string header but
     | before the end of the line.
```

## Known limitations

### Type text

The [type](/{{ site.uprefix }}/basic/input)
feature (`+type`) is supported *but* you have to `+pass` the example.

In other words, you cannot check its output.

This limitation comes from `PowerShell` that it does not disable the
echo of the terminal and what you type gets mixed with the output in
unexpected/unpredictable ways.

```shell
PS> $num = Read-Host        # byexample: +input +pass
[i love 42]
PS> echo $num
i love 42

PS> $num = Read-Host num    # byexample: +input +pass
num: [i prefer 47!]
PS> echo $num
i prefer 47!
```

If you don't set `+pass` you will get a warning.

### Terminal support

To work with `PowerShell`, the ANSI
[terminal emulator](/{{ site.uprefix }}/advanced/terminal-emulation) is
enabled by default (``+term=ansi``) and cannot be disabled.

Also, the [terminal geometry](/{{ site.uprefix }}/advanced/geometry)
cannot by changed after launching the interpreter
so the option ``+geometry`` cannot be used in an example (but it can be
used from the command line)

The amount of rows of the terminal has a minimum value of 128 and this limit
is really important: if your outputs have more than 128 lines you will need
to increase the geometry or the results may be undefined.

The same for the width of the terminal: minimum of 128 columns.

## PowerShell specific options

```
$ byexample -l pwsh --show-options       # byexample: +norm-ws
<...>
pwsh's specific options
-----------------------
  None.
<...>
```
