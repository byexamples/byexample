# huff usage

``huff`` (human diff) is a simple yet complete diff program with a
more human-understandable output;
it is a spin-off project from ``byexample``.


```shell
$ # ignore this
$ alias huff=python\ q.py

$ huff -h                      # byexample: +norm-ws
usage: q.py [-h] [-V] [-d {none,unified,ndiff,context}] [--no-enhance-diff]
            [--encoding ENCODING] [--pretty {none,all}] [-q]
            [--from-file FROM_FILE | --to-file TO_FILE]
            file [file ...]
positional arguments:
  file                  files to compare of the form: 'file1 file2'. If --to-
                        file or --from-file is given, there is no restriction
                        on the argument.
optional arguments:
  -h, --help            show this help message and exit
  -V, --version         show q.py's version and license, then exit
  -d {none,unified,ndiff,context}, --diff {none,unified,ndiff,context}
                        select diff algorithm.
  --no-enhance-diff     by default, improves are made so the diff are easier
                        to to understand: non-printable characters are
                        visible; this flag disables all of that.
  --encoding ENCODING   select the encoding (supported in Python 3 only, use
                        the same encoding of stdout by default)
  --pretty {none,all}   control how to pretty print the output.
  -q, --quiet           quiet mode, do not print anything even if there are
                        differences.
  --from-file FROM_FILE
                        compare this file against the rest of the files.
  --to-file TO_FILE     compare all the files against this one.

```

It is quite simple to use, just pass 2 files to compare:

```shell
$ echo "Fooo" > w/file1
$ echo "Foao" > w/file2

$ huff --pretty none w/file1 w/file2                      # byexample: +norm-ws
Differences found between files 'w/file1' and 'w/file2':
<...>
Differences:
- Fooo
?    -
+ Foao
?   +

```

It gets better if the differences are subtle: ``huff`` (and ``byexample``) will
try to spot them enhancing the differences.

```shell
$ echo "Foo  " > w/file3

$ huff --pretty none w/file1 w/file3                      # byexample: +norm-ws
Differences found between files 'w/file1' and 'w/file3':
<...>
Differences:
- Fooo
+ Foo$$

```

You can disable this if you want with ``--no-enhance-diff``

More comparisions
-----------------

You can compare one file against several others (or others against one) with
``--from-file`` and ``--to-file``

```shell
$ huff --pretty none --from-file w/file1 w/file2 w/file3   # byexample: +norm-ws
Differences found between files 'w/file1' and 'w/file2':
<...>
Differences:
- Fooo
?    -
+ Foao
?   +
Differences found between files 'w/file1' and 'w/file3':
<...>
Differences:
- Fooo
+ Foo$$

```


```shell
$ huff --pretty none --to-file w/file1 w/file2 w/file3      # byexample: +norm-ws
Differences found between files 'w/file2' and 'w/file1':
<...>
Differences:
- Foao
?   -
+ Fooo
?    +
Differences found between files 'w/file3' and 'w/file1':
<...>
Differences:
- Foo$$
+ Fooo

```

Diff algorithms
---------------

``huff`` support several kinds of diff algorithms (``ndiff`` by default)

```shell
$ huff --pretty none --diff context w/file1 w/file2        # byexample: +norm-ws
Differences found between files 'w/file1' and 'w/file2':
<...>
Differences:
*** 1 ****
! Fooo
--- 1 ----
! Foao

$ huff --pretty none --diff unified w/file1 w/file2        # byexample: +norm-ws
Differences found between files 'w/file1' and 'w/file2':
<...>
Differences:
@@ -1<...> +1<...> @@
-Fooo
+Foao

```

or even none:

```shell
$ huff --pretty none --diff none w/file1 w/file2           # byexample: +norm-ws
Differences found between files 'w/file1' and 'w/file2':
<...>
Expected:
Fooo
Got:
Foao

```

