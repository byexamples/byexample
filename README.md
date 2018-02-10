# ``byexample``

``byexample`` is a literate programming engine where you mix
ordinary text and snippets of code in the same file and then you
execute them as regression tests.

It is primary intended for writing good and live tutorials and documentation
showing how a piece of software works or it can be used *by example*.

Currently we support:

 - C++
 - Python
 - Ruby
 - Shell (sh and bash)
 - GDB (the GNU Debugger)

The documentation of each one can be found in ``docs/languages/``.

More languages will be supported in the future. Stay tuned.

## Contribute

Go ahead, fork this project and start to hack it. Run ``make test`` to ensure that
everything is working as expected and then propose your Pull Request!

There are some interesting areas where you can contribute like:

 - add support to new languages (Javascript, Julia, just listen to you heart)
 - misspelling? I'm not an English native so any grammatical correction is welcome
 - add more examples. How do you use ``byexample``? Give us your feedback!
 - is ``byexample`` producing a hard-to-debug diff or you found a bug? Create an issue in github

## Usage

Install and run it against any source file(s), like this README.
All the snippets will be collected, executed and checked.

```shell
$ pip install --user byexample                # install it # byexample: +skip
$ byexample -l python,ruby,shell README.rst   # run it     # byexample: +skip
................
File README.rst, 20/20 test ran in <...> seconds
[PASS] Pass: 17 Fail: 0 Skip: 3

```

<img src="https://raw.githubusercontent.com/eldipa/byexample/master/media/demo.gif" alt="Sorry, it seems that you cannot see the demo. Another excuse to install byexample and test it by yourself ;)" width="75%" height="75%">

You can select which languages to run, over which files, how to display the
differences and much more.

The ``doc/usage.rst`` document goes through almost all the flags that the
``byexample`` program has.

### Snippets of code

Any snippet of code that it is detected by ``byexample`` will be executed
and its output compared with the text below.

This is a quite useful way to test and document by example.

Any code that is written inside of a Markdown fenced code block will be parsed
and executed depending of the language selected.

Here is an example in Python

```python
1 + 2

out:
3

```

The expression ``1 + 2`` is executed and the output compared with ``3`` to
see if the test passes or not.

For some languages, we support the interpreter-session like syntax.

For Python we use ``>>>`` and ``...`` as prompts to find this sessions

```python
>>> def add(a, b):
...   return a + b

```

```python
add(1, 2)

out:
3
```


There is not restriction in which snippets you can add. You can even mix
snippets of different languages in the same file!

Here is an example in Ruby

```ruby
def add(a, b)
  a + b
end;

add(2, 6)

out:
=> 8
```

The documentation of each language can be found in ``docs/languages/``.

### The 'match anything' wildcard

By default, if the expected text has the ``<...>`` marker, that
will match for any string.

Very useful to match long unwanted or uninteresting strings.

```python
print(list(range(20)))

out:
[0, 1, <...>, 18, 19]

```

### Capture

The ``<name>`` marker can be used to capture any string (like ``<...>``)
but also it assigns a name to the capture.

If a name is used in an example more than once, all the string captured under
that name must be the same string, otherwise the test will fail.

Given the value:

```python
X = 42

```

The following example will pass, as both ``random-number``s are the same (42).

```python
[1, X, 2, X]

out:
[1, <random-number>, 2, <random-number>]

```

But in the following, both numbers are different and the example will fail

```python
[1, X, 2, 4]                                    # byexample: +pass

out:
[1, <random-number>, 2, <random-number>]

```


### Option flags

``byexample`` supports a set of flags or options that can change some
parameters of the execution of the example.

Some flags are generic, others are interpreter-specific.

#### Normalize whitespace

Replace any sequence of whitespace by a single one. This makes the test
more robust against small differences (trailing spaces, space/tab mismatch)

```python
print(list(range(20)))				# byexample: +norm-ws

out:
[0,   1,  2,  3,  4,  5,  6,  7,  8,  9,
10,  11, 12, 13, 14, 15, 16, 17, 18, 19]

```

#### Skip and Pass

``skip`` will skip the example completely while ``pass`` will execute it
normally but it will not check the output.

```python
a = 1
a = 2       # this assignment will not be executed # byexample: +skip
a

out:
1
```

```python
def f():
    print("Choosing a random number...")
    return 42

a = f()     # execute the code but ignore the output # byexample: +pass
a

out:
42

```

#### Timeout

The execution of each example has a timeout which can be changed by
a flag

```python
import time
time.sleep(2.5) # simulates a slow operation # byexample: +timeout=3

```

## Extend ``byexample``

It is possible to extend ``byexample`` adding new ways to find examples in a
document and/or to parse and run/interpret a new language or adding hooks to be
called regardless of the language/interpreter.

The ``doc/how_to_extend.rst`` is a quick tutorial that shows exactly that.
