# Usage

Imagine that you are creating a 101 ``Python`` tutorial and you want to explain
the basics of the language writing a blog.

So you open your favorite editor (mine is ``cat``) and start to write the blog:

```
$ cat <<EOF > w/blog-101-python-tutorial.md
> This is a 101 Python tutorial
> The following is an example written in Python about arithmetics
>
>     >>> from __future__ import print_function
>     >>> 1 + 2
>     3
>
> The next example show you about complex numbers in Python
>
>     >>> 2j * 2
>     4
>
> And of course, this is the hello world written in Python
>
>     >>> print('hello world  ')    # byexample
>     hello world
> EOF

```

Now we want to be sure that the examples in the blog are correct.

Just run ``byexample`` selecting ``python`` as the language target
(for now, ignore the ``--pretty none``):

```
$ byexample --pretty none -l python w/blog-101-python-tutorial.md
<...>
Failed example:
    2j * 2
<...>
Expected:
4
Got:
4j
<...>
File w/blog-101-python-tutorial.md, 4/4 test ran in <...> seconds
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
example using ``--ff`` or ``--fail-fast``.

```
$ byexample --ff --pretty none -l python w/blog-101-python-tutorial.md
<...>
File w/blog-101-python-tutorial.md, 3/4 test ran in <...> seconds
[FAIL] Pass: 2 Fail: 1 Skip: 0

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
the test (I will use ``sed`` for this, but you can edit the file by hand):

```
$ sed -i 's/ 4$/ 4j/' w/blog-101-python-tutorial.md

$ byexample --pretty none -l python w/blog-101-python-tutorial.md
<...>
Failed example:
    print('hello world  ')    # byexample
<...>
Expected:
hello world
Got:
hello world$$
<...>
File w/blog-101-python-tutorial.md, 4/4 test ran in <...> seconds
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
$ byexample --pretty none --no-enhance-diff -l python w/blog-101-python-tutorial.md
<...>
Failed example:
    print('hello world  ')    # byexample
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
$ byexample --pretty none --diff ndiff -l python w/blog-101-python-tutorial.md
<...>
Failed example:
    print('hello world  ')    # byexample
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
$ sed -i 's/byexample/byexample: +norm-ws/' w/blog-101-python-tutorial.md

$ byexample --pretty none -l python w/blog-101-python-tutorial.md
<...>
File w/blog-101-python-tutorial.md, 4/4 test ran in <...> seconds
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

### Paste

As we mentioned before, you can use ``<name>`` to capture some output
and paste it in the next examples.

```python
>>> def gen_number():
...     n = 42
...     print("Generating: %i" % n)
...     return n

>>> a = gen_number()
Generating: <random-number>

>>> a == <random-number>     # byexample: +paste
True

```

You can even paste it in the expected of the next examples:

```python
>>> a                 # byexample: +paste
<random-number>

>>> a                 # byexample: +paste -tags
<random-number>

```

Disabling the capture you can be sure that the tags come from a previous example
and they are not captured from the current example but it is not mandatory.

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
$ byexample --pretty none -l python --timeout 0.0001 --ff w/blog-101-python-tutorial.md
<...>
Got:
**Execution timed out**
Prompt not found: the code is taking too long to finish or there is a syntax error.
<...>
[FAIL] Pass: 0 Fail: 1 Skip: 0

```

### More options

``byexample`` has more options that control the behavior of the examples.

If the option is set in the command line using ``-o <opt>``, it will affect all
the examples.

```
$ byexample --pretty none -l python --options "+norm-ws" w/blog-101-python-tutorial.md
<...>
File w/blog-101-python-tutorial.md, 4/4 test ran in <...> seconds
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
$ echo '--pretty=none'         > w/options_file
$ echo '--options="+norm-ws"' >> w/options_file

```

Then load it with ``@`` and the file; you can use multiple files
and combine them with more options from the command line:

```
$ byexample -l python @w/options_file w/blog-101-python-tutorial.md
<...>
File w/blog-101-python-tutorial.md, 4/4 test ran in <...> seconds
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

Those are find and extracted as well and typically the example spans only the
line that has the prompt and the expected output goes immediately below until
the first empty line.

Here is the same example than before but using prompts:

```python
>>> 1 + 1
2

```


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

## Changing the runner: Shebang

The examples are executed by a specific runner based on the language of
the examples.

In general, the runner is an interactive interpreter like ``irb`` for ``Ruby``
or ``python`` for ``Python``.

Sometimes is convenient to change how the interpreter is executed for:
 - using another one (but compatible)
 - adding or removing environment variables
 - redirecting the standard error
 - executing it remotely

Consider the following example that prints interesting things to standard output
and debug/uninterested things to standard error:

```
$ cat <<EOF > w/blog-database.md
>     >>> from __future__ import print_function
>     >>> import sys
>
>     >>> def load_database():
>     ...     print("Loading...")
>     ...     print("debug 314kb", file=sys.stderr)
>     ...     print("Done")
>
>     >>> load_database()
>     Loading...
>     Done
> EOF

```

Running this will fail because the debug print will be mixed with the normal
prints:

```
$ byexample --pretty none -l python w/blog-database.md
<...>
Expected:
Loading...
Done
Got:
Loading...
debug 314kb
Done
<...>

```

Yes, changing the example solves this but what happen if you cannot change it?

Then you can teach ``byexample`` to redirect the standard error.

For this we need to change how to spawn a ``python`` interpreter using
the ``shebang`` option:

```
$ byexample --pretty none -l python \
>   --shebang "python:/bin/sh -c '%e %p %a 2>/dev/null'"  \
>   w/blog-database.md
<...>
[PASS] Pass: 4 Fail: 0 Skip: 0

```

Don't be scared, the expression ``python:/bin/sh -c '%e %p %a 2>/dev/null'``
sets how to execute a runner for ``python``.

The ``%e``, ``%p``, ``%a`` tokens are replaced by ``byexample`` with the
environment, program name and arguments.

Each runner has its own set of values for those tokens.

To simplify let's assume that ``%e`` and ``%a`` are empty and ``%p``
is ``python``.

So the shebang after the substitutions is ``/bin/sh -c 'python 2>/dev/null'``

This one in turns means: spawn a ``/bin/sh`` shell with ``-c`` and
``'python 2>/dev/null'`` as arguments.

``-c`` means execute the next argument as a shell command, so this will
execute ``python 2>/dev/null`` and the ``2>/dev/null`` mean that the standard
error should be discarded.

If your shell-fu is a little rusty and the shebang is too magic, don't worry
I had the same problem; it's for very specific situation and you should be
away from this most of the time.

## Extending ``byexample``


Currently we support:

 - Python (compatible with ``doctest``). [docs](languages/python.md)
 - Ruby. [docs](languages/ruby.md)
 - Shell (``sh`` and ``bash``). [docs](languages/shell.md)
 - GDB (the [GNU Debugger](https://www.gnu.org/software/gdb/download/)). [docs](languages/gdb.md)
 - C++ (using [cling](https://github.com/root-project/cling) - *experimental*). [docs](languages/cpp.md)

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
            [--shebang runner:shebang] [-v | -q]
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
  --encoding ENCODING   select the encoding (supported in Python 3 only, use
                        the same encoding of stdout by default)
  --pretty {none,all}   control how to pretty print the output.
  --interact, --debug   interact with the runner/interpreter manually if an
                        example fails.
  --shebang runner:shebang
                        change the command line of the given <runner> by
                        <shebang>; the tokens %e %p %a are replaced by the
                        default values for environment, program name, and
                        arguments (however no all the runners will honor this
                        and some may break).
  -v                    verbosity level, add more flags to increase the level.
  -q, --quiet           quiet mode, do not print anything even if an example
                        fails; supress the progress output.

```
