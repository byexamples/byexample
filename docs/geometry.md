<!--
Check that we have byexample installed first
$ hash byexample                                    # byexample: +fail-fast

$ alias byexample=byexample\ --pretty\ none

--
-->

When ``byexample`` runs a set of examples he spawns one o more runners
inside a terminal.

This terminal has a default geometry or dimensions of 24 lines and
80 columns.

This can affect how the runner will print the output and therefore,
how the examples should be written.

``byexample`` allows to control the geometry at startup time using
``+geometry LxC``.

Here the following examples fail because they are expecting a 24x127
geometry:

$ byexample -l python,shell test/ds/long-lines.md
<...>
File "test/ds/long-lines.md", line 2
Failed example:
    echo ${LINES}x${COLUMNS}
<...>
Expected:
24x127
Got:
24x80
<...>
File "test/ds/long-lines.md", line 5
Failed example:
    ['aaaaa', 'aaaaa', 'aaaaa', 'aaaaa', 'aaaaa', 'aaaaa', 'aaaaa', 'aaaaa', 'aaaaa']
<...>
Expected:
['aaaaa', 'aaaaa', 'aaaaa', 'aaaaa', 'aaaaa', 'aaaaa', 'aaaaa', 'aaaaa', 'aaaaa']
Got:
['aaaaa',
 'aaaaa',
 'aaaaa',
<...>

And here we have them pass:

$ byexample -l python,shell -o '+geometry 24x127' test/ds/long-lines.md
<...>
File test/ds/long-lines.md, 2/2 test ran in <...> seconds
[PASS] Pass: 2 Fail: 0 Skip: 0

Keep in mind that even if ``byexample`` sets the geometry the runner/interpreter
*may decide to ignore it*: [open an issue](https://github.com/byexamples/byexample/issues)
if this is a problem related to the default printers of the runner.


