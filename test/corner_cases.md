<!--
Check that we have byexample installed first
$ hash byexample                                    # byexample: +fail-fast

$ alias byexample=byexample\ --pretty\ none

--
-->

## Arguments

A `--` is missing to separate the files from being skipped from the ones
to be executed:

```shell
$ byexample -l python --skip byexample/prof.py byexample/*.py
[!] No files were found (you passed 0 files, <...> were skipped)
[w] You are probably skipping more files than you want.
You may need to add a '--' to separate the files that
you want to skip from the ones that you want to execute:
<...>
  byexample --skip <files to skip> -- <files to execute>
```


Ensure that `byexample` works even in a super-verbose mode.

```shell
$ byexample -l python  -vvvvvvvvvvvvvvvvvvvvv --skip byexample/prof.py -- byexample/*.py > /dev/null  # byexample: +timeout=60
$ echo $?
0
```

Ensure that `byexample` works even if it has to process N
files but it is configured to use M jobs where N < M

```shell
$ byexample -l python --jobs 2 -- byexample/parser.py > /dev/null  # byexample: +timeout=60
$ echo $?
0
```

Ensure that it works with only 1 job

```shell
$ byexample -l python --jobs 1 -- byexample/parser.py > /dev/null  # byexample: +timeout=60
$ echo $?
0
```

## Encoding

Pick a file that requires to be open in `utf-8` but, for some reason
`byexample` opens it with an incorrect encoding.

`byexample` should print a nice message about `--encoding`:

```shell
$ byexample -l shell --encoding ascii docs/advanced/unicode.md      # byexample: +norm-ws
[!] Reading the file 'docs/advanced/unicode.md' using the 'ascii' encoding failed due decoding errors.
Try a different encoding with '--encoding' from the command line.
'ascii' codec can't decode byte 0xd0 in position 304: ordinal not in range(128)
Rerun with -vvv to get a full stack trace.


$ byexample -l shell --encoding ascii -vvv docs/advanced/unicode.md      # byexample: +norm-ws
[!] Reading the file 'docs/advanced/unicode.md' using the 'ascii' encoding failed due decoding errors.
Try a different encoding with '--encoding' from the command line.
Traceback (most recent call last):
<...>
UnicodeDecodeError: 'ascii' codec can't decode byte 0xd0 in position 304: ordinal not in range(128)
```

If the file is okay but the example executed prints in an unexpected
encoding we also should print a nice message about `--encoding`.

Given the innocent file (ascii) that prints an unicode (utf-8) output:

```shell
$ cat test/ds/ascii_with_unicode_example.md
<...>$ cat docs/advanced/unicode.md
<...>
```

Then, the execution of `byexample` is:

```shell
$ byexample -l shell --encoding ascii test/ds/ascii_with_unicode_example.md     # byexample: +diff=ndiff
<...>
File "test/ds/ascii_with_unicode_example.md", line 2
Failed example:
    cat docs/advanced/unicode.md
=> Execution of example 1 of 1 crashed.
- The output of the example could not be decoded as 'ascii'.
The current setting is '--encoding=ascii:strict'.
Try a different one with '--encoding' from the command line.
If the encoding is correct, try to use a more relaxed error handler
like 'replace' or 'ignore'.
If it helps, this is the decoding error we got:
<...>
[ABORT] Pass: 0 Fail: 0 Skip: 0
```

## Dry and glob expansion

`--dry` does not run any example, only parse them. And with a little of
verbosity, it lists the files and the count of examples per file.

The file names support *glob expansion* done by `byexample` itself.

```shell
$ byexample -l cpp,shell --dry -v --skip 'docs/languages/p*.md' -- 'docs/languages/*.md'
[i] File docs/languages/cpp.md, 34 examples.
[i] File docs/languages/elixir.md, 2 examples.
[i] File docs/languages/gdb.md, 7 examples.
[i] File docs/languages/go.md, 2 examples.
[i] File docs/languages/iasm.md, 7 examples.
[i] File docs/languages/java.md, 3 examples.
[i] File docs/languages/javascript.md, 2 examples.
[i] File docs/languages/ruby.md, 2 examples.
[i] File docs/languages/rust.md, 2 examples.
[i] File docs/languages/shell.md, 50 examples.
```

The glob expansion takes place also in the argument-file:

```shell
$ echo 'docs/languages/*.md' > test/ds/args

$ cat test/ds/args
docs/languages/*.md

$ byexample -l cpp,shell --dry -v @test/ds/args --skip 'docs/languages/p*.md'
[i] File docs/languages/cpp.md, 34 examples.
[i] File docs/languages/elixir.md, 2 examples.
[i] File docs/languages/gdb.md, 7 examples.
[i] File docs/languages/go.md, 2 examples.
[i] File docs/languages/iasm.md, 7 examples.
[i] File docs/languages/java.md, 3 examples.
[i] File docs/languages/javascript.md, 2 examples.
[i] File docs/languages/ruby.md, 2 examples.
[i] File docs/languages/rust.md, 2 examples.
[i] File docs/languages/shell.md, 50 examples.
```

<!--

$ rm -f test/ds/args    # byexample: -skip +pass

-->

## Subprocess within a module

The following print comes from a subprocess spawned by a module/plugin
proving that calling code in background is possible.

```shell
$ byexample -m test/ds/submod -l python -q test/ds/one.md
---> 42 bg
```
