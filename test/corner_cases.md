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
$ byexample -l python  -vvvvvvvvvvvvvvvvvvvvv -- byexample/*.py > /dev/null  # byexample: +timeout=60
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
$ byexample -l shell --encoding ascii test/ds/ascii_with_unicode_example.md
<...>
File "test/ds/ascii_with_unicode_example.md", line 2
Failed example:
    cat docs/advanced/unicode.md
=> Execution of example 1 of 1 crashed.
- Incorrect encoding.
The output of the example is incompatible with the current encoding.
Try a different one with '--encoding' from the command line.
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

## Error on module load

Any error loading the module (at the import level) will be shown as any
other error:

```shell
$ byexample -m test/ds/badmod/ -l python --dry docs/languages/python.md
[!] From '/home/user/proj/byexample/test/ds/badmod' loading module 'bogus' failed. Skipping.
invalid syntax (bogus.py, line 1)
<...>
Rerun with -vvv to get a full stack trace.
```

With `-vvv`, the full stack is shown too:

```shell
$ byexample -m test/ds/badmod/ -l python --dry -vvv docs/languages/python.md
[!] From '/home/user/proj/byexample/test/ds/badmod' loading module 'bogus' failed. Skipping.
Traceback (most recent call last):
<...>
  File "<...>test/ds/badmod/bogus.py", line 1
<...>
SyntaxError: <...>
<...>
```

## Subprocess within a module

The following print comes from a subprocess spawned by a module/plugin
proving that calling code in background is possible.

```shell
$ byexample -m test/ds/submod -l python -q test/ds/one.md
---> 42 bg
```

## Shutdown

Ensure that if the program is slow and takes some reasonable time to
shutdown, don't raise a Timeout after stopping it

```shell
$ test/ds/sleepy/c.sh          # byexample: +timeout=10 +stop-on-silence +stop-signal=interrupt
Start
```

Run three very slow tests and send `byexample` to the background
as soon as possible.

```shell
$ byexample -l python test/ds/sleepy/{s1,s2,s3}.md  # byexample: +stop-on-silence 7
```

Now send a Ctrl-C (SIGINT) to abort the execution. It is expected that
the shutdown will take time to finish the current jobs (20 secs) but it
will not take the full time to run (60 secs) because it was aborted.

```shell
$ sleep 1 ; kill -2 %%    # byexample: +pass +timeout=3
$ fg            # byexample: +timeout 25 +rm=~
byexample --pretty none -l python test/ds/sleepy/{s1,s2,s3}.md
[i] User aborted. Waiting to finish the current active executions...
~
File test/ds/sleepy/s1.md, 2/2 test ran in <...> seconds
[PASS] Pass: 2 Fail: 0 Skip: 0
```

Forcing a shutdown doing a Ctrl-C (SIGINT) twice and more will
start breaking all the code but it will abort the execution faster.

Note how the timeouts sum up less than 20 secs proving that `byexample`
didn't complete any execution (it was aborted by hard) and finished.

```shell
$ byexample -l python test/ds/sleepy/{s1,s2,s3}.md  # byexample: +stop-on-silence 7

$ sleep 1 ; kill -2 %%    # byexample: +pass +timeout=3
$ fg            # byexample: +rm=~ +stop-on-silence 3
byexample --pretty none -l python test/ds/sleepy/{s1,s2,s3}.md
[i] User aborted. Waiting to finish the current active executions...

$ sleep 1 ; kill -2 %%    # byexample: +pass +timeout=3
$ fg            # byexample: +rm=~ +stop-on-silence 3
byexample --pretty none -l python test/ds/sleepy/{s1,s2,s3}.md
[w] Not waiting for the current active executions to finish...
Pressing more times Ctrl-C will force an immediate shutdown
but it will leave resources uncleaned (dangerous/unsafe).

$ sleep 1 ; kill -2 %%    # byexample: +pass +timeout=3
$ fg            # byexample: +timeout 3 +rm=~
<...>
KeyboardInterrupt<...>
```
