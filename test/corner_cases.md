<!--
Check that we have byexample installed first
$ hash byexample                                    # byexample: +fail-fast

$ alias byexample=byexample\ --pretty\ none

--
-->


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
