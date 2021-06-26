# iasm: the interactive assembler

You will have to install `iasm` first:

```shell
$ pip install iasm      # byexample: +skip
```

Or you can download the code from
[here](https://github.com/bad-address/iasm)

> **Stability**: ``experimental`` - non backward compatibility changes are
> possible or even removal between versions (even patch versions).

## Find interactive examples

For ``iasm``, ``byexample`` uses the ``:>`` string as the primary prompt
and ``->`` as the secondary prompt.

In `iasm` the example is compiled and executed as the architecture
configured on start up, ARM by default:

```nasm
:> mov r0, #4
:> mov r1, #8
```

Examples that begin with `;!` are executed as Python statement that can
operate with the registers and with the memory `M`:

```python
:> ;! print(r0 + r1)
12
```

## Showing the registers

`iasm` allows you to show the values of the registers by name or
pattern.

```python
:> ;! show('r*')
------  -  ------  -  ------  -  ------  -----
    r0  4  r1      8  r10     0  r11/fp  0
r12/ip  0  r13/sp  0  r14/lr  0  r15/pc  100:4
    r2  0  r3      0  r4      0  r5      0
    r6  0  r7      0  r8      0  r9/sb   0
------  -  ------  -  ------  -  ------  -----
```

Add `stick=True` to display those registers every time.

## `byexample` options

The `byexample` options can be set in the assembly comments (`;`)
and in the Python comments (`#`):

```nasm
:> r1024-nonexist    ; byexample: +skip
```

```python
:> ;! r1024-nonexist  # byexample: +skip
```

## Known limitations

### Input

The [input](/{{ site.uprefix }}/basic/input)
feature (`+input`) is not supported.

### Terminal support

To work with `iasm`, the ANSI
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

