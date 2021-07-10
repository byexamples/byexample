<!--
Check that we have byexample installed first
$ hash byexample                                    # byexample: +fail-fast
$ hash iasm                                         # byexample: +fail-fast

$ alias byexample=byexample\ --pretty\ none

--
-->

# iasm: the interactive assembler

Run the `iasm` examples calling `byexample` as:

```shell
$ byexample -l iasm your-file-here                # byexample: +skip
```

You will have to install `iasm` first:

```shell
$ pip install iasm      # byexample: +skip
```

Or you can download the code from
[here](https://github.com/bad-address/iasm)

> **Stability**: ``experimental`` - non backward compatibility changes are
> possible or even removal between versions (even patch versions).

> *New* in ``byexample 10.1.0``.

## Set architecture and operation mode

`iasm` is capable to emulate different architectures.

The settings can be passed to `iasm` from the command line of
`byexample`. Once set they cannot be changed at runtime.

```shell
$ byexample -l iasm -o '+iasm-arch=x86 +iasm-mode=64 +iasm-code-size=102400 +iasm-pc=0' test/ds/iasm.md  # byexample: +timeout=8
<...>
[PASS] Pass: 1 Fail: 0 Skip: 0
```

See the [`iasm` documentation](https://github.com/bad-address/iasm)
for more information about those.

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
:> ;! show('r[0-9]', 'r1[0-9]')
------  -  ------  -  ------  -  ------  -----
    r0  4  r1      8  r2      0  r3      0
    r4  0  r5      0  r6      0  r7      0
    r8  0  r9/sb   0  r10     0  r11/fp  0
r12/ip  0  r13/sp  0  r14/lr  0  r15/pc  100:4
------  -  ------  -  ------  -  ------  -----
```

Add `stick=True` to display those registers every time.

```python
:> ;! show('r[0-3]', stick=True)
--  -  --  -  --  -  --  -
r0  4  r1  8  r2  0  r3  0
--  -  --  -  --  -  --  -

:> mov r2, r1
--  -  --  -  --  -  --  -
r0  4  r1  8  r2  8  r3  0
--  -  --  -  --  -  --  -
```

Call `show(stick=True)` to restore the defaults:

```python
:> ;! show(stick=True)
```

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

### Type text

The [type](/{{ site.uprefix }}/basic/input)
feature (`+type`) is not supported.

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

## iasm specific options

```
$ byexample -l iasm --show-options       # byexample: +norm-ws
<...>
iasm's specific options
-----------------------
optional arguments:
  +iasm-arch <arch>     architecture name (arm, x86, sparc, ...); see iasm
                        documentation.
  +iasm-mode <mode>     mode (arm, 32, 64, ...); see iasm documentation.
  +iasm-code-size <sz>  size of the code segment; see iasm documentation.
  +iasm-pc <addr>       starting address, value of the program counter; see
                        iasm documentation.
<...>
```
