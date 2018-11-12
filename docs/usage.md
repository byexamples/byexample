<!--
Check that we have byexample installed first
$ hash byexample                                    # byexample: +fail-fast

$ alias byexample=byexample\ --pretty\ none

--
-->

# Usage

Imagine that you are creating a 101 ``Python`` tutorial and you want to explain
the basics of the language writing a blog.

So you open your favorite editor, write some comments, you enhance them with
real ``Python`` examples and you get something like this:

```
$ cat test/ds/python-tutorial.v1.md               # byexample: +rm=~
This is a 101 Python tutorial
The following is an example written in Python about arithmetics
~
~    >>> from __future__ import print_function
~    >>> 1 + 2
~    3
~
The next example show you about complex numbers in Python
~
~    >>> 2j * 2
~    4
~
And of course, this is the hello world written in Python
~
~    >>> print('hello world  ')
~    hello world
~
```

Now we want to be sure that the examples in the blog are correct.

Just run ``byexample`` selecting ``python`` as the language target

```
$ byexample -l python test/ds/python-tutorial.v1.md
<...>
Failed example:
    2j * 2
<...>
Expected:
4
Got:
4j
<...>
File test/ds/python-tutorial.v1.md, 4/4 test ran in <...> seconds
[FAIL] Pass: 2 Fail: 2 Skip: 0
```

``byexample`` will show the differences for each failing test and at the end
will print a summary showing how many examples were executed, how many passed,
failed or where skipped.

A skipped example means that the example has a ``+skip`` option and it was not
executed.

In normal circumstances there are two possible status: ``PASS`` and ``FAIL``.

If something strange happen like the user pressed ``ctrl-c``, the underlying
runner crashed or an example couldn't get parsed, the status will be ``ABORT``.

For quick regression you may want to stop ``byexample`` at the first failing
example using ``--ff`` or ``--fail-fast`` to skip all the remaining examples.

```
$ byexample --ff -l python test/ds/python-tutorial.v1.md
<...>
File test/ds/python-tutorial.v1.md, 4/4 test ran in <...> seconds
[FAIL] Pass: 2 Fail: 1 Skip: 1
```

## Wildcards and Captures

You may noticed the use of ``<...>`` in the previous example. This tag matches
any string and can be used to ignore unwanted long or non-deterministic strings.

Like ``<...>``, the tags with a name like ``<name>`` matches anything but
the matched string is also captured and can be pasted into another example
later.


## Output differences

Each test is found, parsed and executed. For each test or example that failed
``byexample`` will print the example followed by the expected and the got
outputs.

In the previous example, the code executed was ``2j * 2`` and we expected
``4`` but instead we got ``4j`` as a result.

Obviously our blog has a bug!


We can fix ``2j * 2`` replacing the expected ``4`` by ``4j`` and re running
the test.

Here is our second try:

```
$ diff -U 1 test/ds/python-tutorial.v1.md test/ds/python-tutorial.v2.md  # byexample: +rm=~
<...>
~     >>> 2j * 2
~-    4
~+    4j
~ 

$ byexample -l python test/ds/python-tutorial.v2.md
<...>
Failed example:
    print('hello world  ')
<...>
Expected:
hello world
Got:
hello world$$
<...>
File test/ds/python-tutorial.v2.md, 4/4 test ran in <...> seconds
[FAIL] Pass: 3 Fail: 1 Skip: 0
```

We fixed one but the last example also fails. And this time the difference
is subtle.

### Whitespace differences

``byexample`` will highlight some whitespace characters both in the expected
and in the got outputs to make easier to see the differences like this.

In the last case, the example is printing 'hello world' followed by 2 trailing
spaces, marked with a ``$``

You can disable this enhancement if you are getting confuse for the extras ``$``s:

```
$ byexample --no-enhance-diff -l python test/ds/python-tutorial.v2.md
<...>
Failed example:
    print('hello world  ')
Expected:
hello world
Got:
hello world  
<...>
```

Without the enhancement, is harder to spot the difference, isn't?

That's the reason that the default in ``byexample`` is to highlight this kind
of hard-to-see characters

### Diff algorithms

``byexample`` supports diff algorithms.

Instead of printing the expected and the got outputs separately,
you can select one diff and print both outputs in the same context.

For large outputs this is an awesome tool

```
$ byexample --diff ndiff -l python test/ds/python-tutorial.v2.md
<...>
Failed example:
    print('hello world  ')
<...>
Differences:
- hello world
+ hello world$$
?            ++
<...>
```

Check out [docs/differences](differences.md) for more info about this.

## Normalize whitespace

We can tell ``byexample`` to relax the checks and replace all the sequences
of spaces, tabs and new lines as a single space.

We could use this to fix our failing example adding ``# byexample: +norm-ws``
to the example:

```
$ diff -U 1 test/ds/python-tutorial.v2.md test/ds/python-tutorial.v3.md      # byexample: +rm=~
<...>
~-    >>> print('hello world  ')
~+    >>> print('hello world  ')      # byexample: +norm-ws
~     hello world
~

$ byexample -l python test/ds/python-tutorial.v3.md
<...>
File test/ds/python-tutorial.v3.md, 4/4 test ran in <...> seconds
[PASS] Pass: 4 Fail: 0 Skip: 0
```


## Option flags

``byexample`` supports a set of flags or options that can change some
parameters of the execution of the example.

Some flags are generic, others are language-specific.

### Normalize whitespace

We already saw this one, replace any sequence of whitespace by a single one.

This makes the test more robust against small differences
(trailing spaces, space/tab mismatch)

Here is another example, this time written in ``Ruby``:

```ruby
Array(0...20)				# byexample: +norm-ws

out:
=> [0,   1,  2,  3,  4,  5,  6,  7,  8,  9,
   10,  11, 12, 13, 14, 15, 16, 17, 18, 19]
```

### Skip and Pass

``skip`` will skip the example completely while ``pass`` will execute it
normally but it will not check the output.

See the difference between those two in these ``Python`` examples:

```python
>>> def f():
...    print("Choosing a random number...")
...    return 42

>>> a = 1
>>> a = f() # this assignment will not be executed # byexample: +skip

>>> a
1

>>> a = f() # execute the code but ignore the output # byexample: +pass

>>> a
42

>>> a = f() # the output is not ignored so we must check for it
Choosing a random number...
```

### Timeout

The execution of each example has a timeout which can be changed by a flag

```python
import time
time.sleep(2.5) # simulates a slow operation # byexample: +timeout=3
```

See what happen when an example timeout:

```
$ byexample -l python --timeout 0.0001 --ff test/ds/python-tutorial.v3.md
<...>
File "test/ds/python-tutorial.v3.md", line 4
Failed example:
    from __future__ import print_function
=> Execution timedout at example 1 of 4.
This could be because the example just ran too slow (try add more time
with +timeout=<n>) or the example is "syntactically incorrect" and
the interpreter hang (may be you forgot a parenthesis or something like that?).
<...>
[ABORT] Pass: 0 Fail: 0 Skip: 0
```

### More options

``byexample`` has more options that control the behavior of the examples.

If the option is set in the command line using ``-o <opt>``, it will affect all
the examples.

```
$ byexample -l python --options "+norm-ws" test/ds/python-tutorial.v2.md
<...>
File test/ds/python-tutorial.v2.md, 4/4 test ran in <...> seconds
[PASS] Pass: 4 Fail: 0 Skip: 0
```

If the option is set per example using ``byexample: <opt>``, it will affect only
the specific example.

You can know what options are available for a given language running the help
integrated in ``byexample``.

For ``Python`` you could do:

```
$ byexample -l python --show-options
byexample's options
-------------------
optional arguments:
  +fail-fast            if an example fails, fail and stop all the execution.
  +norm-ws              ignore the amount of whitespaces.
  <...>
python's specific options
-------------------------
optional arguments:
  +py-doctest           enable the compatibility with doctest.
  +py-pretty-print      enable the pretty print enhancement.
  <...>
```

### Loading options from a file

If the amount of options is a little overhelming for you, you can
write them down to a file and let ``byexample`` load them for you.

The only convention that you need to follow is to write one option
per line and use ``=`` for the arguments.

```
$ echo '-l=python'               > w/options_file
$ echo '--options="+norm-ws"'   >> w/options_file
```

Then load it with ``@`` and the file; you can use multiple files
and combine them with more options from the command line:

```
$ byexample @w/options_file test/ds/python-tutorial.v2.md
<...>
File test/ds/python-tutorial.v2.md, 4/4 test ran in <...> seconds
[PASS] Pass: 4 Fail: 0 Skip: 0
```


## What is considered an example?

``byexample`` uses the concept of finders to find and extract examples from
a given file.

Currently ``byexample`` supports one generic finder based on the
Markdown fenced block syntax.

Anything that it is between ````` ```<language> ````` and ````` ``` ````` is
considered an example and the language of syntax set.

The fenced block contains the code to execute and the expected output separated
by the ``out:`` label.

`````
 ```python
 1 + 1

 out:
 2
 ```
`````

In addition to that, most of the languages supported in ``byexample`` has their
own additional finder.

For example in ``Python`` you can use the prompts ``>>>`` and ``...`` to write
an interpreter session like example.

```python
>>> 1 + 1
2
```

Check out [where should I write the examples](where_should_I_write_the_examples.md)
section, it has a more in deep description.

### New lines at the end are ignored

``byexample`` will ignore any empty line(s) at the end of the expected string
and from the got string from the executed examples.

Look at this successful example even if the example prints several empty lines
at the end which are not expected:

```python
>>> print("bar\n\n")
bar
```

This is because most of the time an empty new line is added for aesthetics
purposes in the example or produced by the runner/interpreter as an artifact.

### New lines in the middle of the expected string

Most, if not all the examples use an empty line as delimiter to mark the end
of the expected string.

But what if you want to test a multiline text that has empty lines?

You can use a special character like ``~`` and instruct ``byexample`` to
ignore it with the ``rm`` option.

```python
>>> print("hello\n\nworld!")    # byexample: +rm=~
hello
~
world!
```



## Extending ``byexample``

Currently we support:

 - Python (compatible with ``doctest``) -> [docs](https://byexamples.github.io/byexample/languages/python)
 - Ruby -> [docs](https://byexamples.github.io/byexample/languages/ruby)
 - Javascript -> [docs](https://byexamples.github.io/byexample/languages/javascript)
 - Shell (``sh`` and ``bash``) -> [docs](https://byexamples.github.io/byexample/languages/shell)
 - GDB (the [GNU Debugger](https://www.gnu.org/software/gdb/download/)) -> [docs](https://byexamples.github.io/byexample/languages/gdb)
 - C++ (using [cling](https://github.com/root-project/cling) - *experimental*) -> [docs](https://byexamples.github.io/byexample/languages/cpp)

But don't get limited to those.

You can extend ``byexample`` adding:
 - new ways to find examples
 - support new languages and interpreters
 - new reports and other things

Check out [how to support new finders and languages](how_to_support_new_finders_and_languages.md)
and [how to hook to events with concerns](how_to_hook_to_events_with_concerns.md) for more info.

It is easier than you think!

## Help included

The help included in ``byexample`` should give you a quick overview of its
capabilities

```
$ byexample -h                                          # byexample: +norm-ws
usage: <byexample> [-h] [-V] [--ff] [--dry] [--skip file [file ...]] [-m dir]
            [-d {none,unified,ndiff,context}] [--no-enhance-diff] -l language
            [--timeout TIMEOUT] [-o OPTIONS_STR] [--show-options]
            [--encoding ENCODING] [--pretty {none,all}] [--interact]
            [--shebang runner:shebang] [-j JOBS] [-v | -q]
            [file [file ...]]
positional arguments:
  file                  file that have the examples to run.
optional arguments:
  -h, --help            show this help message and exit
  -V, --version         show <...> version and license, then exit
  --ff, --fail-fast     if an example fails, fail and stop all the execution.
  --dry                 do not run any example, only parse them.
  --skip file [file ...]
                        skip these files
  -m dir, --modules dir
                        append a directory for searching modules there.
  -d {none,unified,ndiff,context}, --diff {none,unified,ndiff,context}
                        select diff algorithm.
  --no-enhance-diff     by default, improves are made so the diff are easier
                        to to understand: non-printable characters are
                        visible; captured string shown, and more; this flag
                        disables all of that.
  -l language, --language language
                        select which languages to parse and run. Comma
                        separated syntax is also accepted.
  --timeout TIMEOUT     timeout in seconds to complete each example (2 by
                        default); this can be changed per example with this
                        option.
  -o OPTIONS_STR, --options OPTIONS_STR
                        add additional options; see --show-options to list
                        them.
  --show-options        show the available options for the selected languages
                        (with -l)
  --encoding ENCODING   select the encoding; use the same encoding of stdout
                        by default)
  --pretty {none,all}   control how to pretty print the output.
  --interact, --debug   interact with the runner/interpreter manually if an
                        example fails.
  --shebang runner:shebang
                        change the command line of the given <runner> by
                        <shebang>; the tokens %e %p %a are replaced by the
                        default values for environment, program name, and
                        arguments (however no all the runners will honor this
                        and some may break).
  -j JOBS, --jobs JOBS  run <jobs> in parallel (1 default); "cpu" means use
                        all the cpus available; "cpu<...>" multiply it by <n>
                        the cpus available.
  -v                    verbosity level, add more flags to increase the level.
  -q, --quiet           quiet mode, do not print anything even if an example
                        fails; supress the progress output.
```
