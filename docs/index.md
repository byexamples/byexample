<!--
Check that we have byexample installed first
$ hash byexample                                    # byexample: +fail-fast
-->

<img src="https://api.travis-ci.org/byexamples/byexample.svg?branch=master" alt="Travis CI is not available">

``byexample`` is a literate programming engine where you mix
ordinary text and snippets of code in the same file and then you
execute them as regression tests.

It lets you to execute the examples written in ``Python``, ``Ruby`` or whatever
in your documentation and validate them.

You can always be sure that the examples are correct and your documentation
is up to date!

Currently ``byexample`` supports:

 - [Python](https://byexamples.github.io/byexample/languages/python) (compatible with ``doctest``)
 - [Ruby](https://byexamples.github.io/byexample/languages/ruby)
 - [Javascript](https://byexamples.github.io/byexample/languages/javascript)
 - [Shell](https://byexamples.github.io/byexample/languages/shell) (``sh`` and ``bash``)
 - [GDB](https://byexamples.github.io/byexample/languages/gdb)
 - [C/C++](https://byexamples.github.io/byexample/languages/cpp) (using [cling](https://github.com/root-project/cling))

## Usage

<img src="https://raw.githubusercontent.com/byexamples/byexample/master/media/demo.gif" alt="Sorry, it seems that you cannot see the demo. Another excuse to install byexample and test it by yourself ;)" width="75%" height="75%">

## How do I get started?

First, you need to install it:

```
$ pip install byexample                # install it # byexample: +skip
```

Or if you prefer, you can install it inside a
[virtual env](https://docs.python.org/3/library/venv.html).

If you don't have ``pip`` or ``python`` installed, check the
[download page](https://www.python.org/downloads/).

That's it! Now, write a tutorial, a blog or a how-to and put some examples
in between (like this ``README.md`` that you are reading);
All the snippets and examples will be collected, executed and checked.

```
$ byexample -l python,ruby,shell README.md      # run it    # byexample: +skip
[PASS] Pass: <...> Fail: <...> Skip: <...>
```

You can select which languages to run, over which files, how to display the
[differences](https://byexamples.github.io/byexample/differences) and much more.

The [usage](https://byexamples.github.io/byexample/usage)
document goes through almost all the flags that
``byexample`` program has, full of examples of course.

## What an example looks like?

It is just a snippet of code followed by the expected result:

```python
>>> 1 + 2
3
```

or

```python
1 + 2

out:
3
```

The expression ``1 + 2`` is executed and the output compared with ``3`` to
see if the test passes or not.

## Where should I write the examples?

``byexample`` really doesn't care where you write the examples: you can write
them in a Markdown, HTML, Latex, or plain text file.

Even you can write them in your own source code to document and test it.

Anything that it is between ````` ```<language> ````` and ````` ``` ````` is considered
an example: this the Markdown fenced block syntax.

But ``byexample`` detects examples in other contexts as well.

For example in ``Python`` you can use the prompts ``>>>`` and ``...`` to write
an interpreter session like example.

```python
>>> def add(a, b):
...   return a + b

>>> add(1, 2)
3
```

Take a look to the documentation of each language [docs/languages](https://github.com/byexamples/byexample/tree/master/docs/languages/).

Check out [where should I write the examples](https://byexamples.github.io/byexample/where-should-I-write-the-examples)
section, it has a more in deep description.

And also check the [usage](https://byexamples.github.io/byexample/usage) page
for more examples.

## Languages supported

Currently we support:

 - [Python](https://byexamples.github.io/byexample/languages/python) (compatible with ``doctest``) -> *stable*
 - [Ruby](https://byexamples.github.io/byexample/languages/ruby) -> *experimental*
 - [Javascript](https://byexamples.github.io/byexample/languages/javascript) -> *experimental*
 - [Shell](https://byexamples.github.io/byexample/languages/shell) (``sh`` and ``bash``) -> *stable*
 - [GDB](https://byexamples.github.io/byexample/languages/gdb) -> *experimental*
 - [C/C++](https://byexamples.github.io/byexample/languages/cpp) (using ``cling``) -> *experimental*

More languages will be supported in the future. Stay tuned.

## Contributing

First off, thanks for using and considering contributing to ``byexample``.

We love to receive contributions from our community. There are tons of ways you
can contribute

 - add support to new languages (Javascript, Julia, just listen to you heart). Check this [how to](https://byexamples.github.io/byexample/how-to-support-new-finders-and-languages).
 - misspelling? Improve to the documentation is more than welcome.
 - add more examples. How do you use ``byexample``? Give us your feedback!
 - is ``byexample`` producing a hard-to-debug diff or you found a bug? Create an issue in github.

But don't be limited to those options. We keep our mind open to other useful
contributions: write a tutorial or a blog, feature requests, social media...

Check out our [CONTRIBUTING](https://github.com/byexamples/byexample/tree/master/CONTRIBUTING.md) guidelines and welcome!

### Extend ``byexample``

It is possible to extend ``byexample`` adding new ways to find examples in a
document and/or to parse and run/interpret a new language or adding hooks to be
called regardless of the language/interpreter.

Check out [how to support new finders and languages](https://byexamples.github.io/byexample/how-to-support-new-finders-and-languages)
and [how to hook to events with concerns](https://byexamples.github.io/byexample/how-to-hook-to-events-with-concerns) for
a quick tutorials that shows exactly how to do that.

You could also share your work and [contribute](https://github.com/byexamples/byexample/tree/master/CONTRIBUTING.md) to
``byexample`` with your extensions.

## Versioning

We use [semantic version](https://semver.org/) for the core or engine.

For each module we have the following categorization:

 - ``experimental``: non backward compatibility changes are possible or even
removal between versions (even patch versions).
 - ``unstable``: low impact non backward compatibility changes may occur
between versions; but in general a change like that will happen only between
major versions.
 - ``stable``: non backward compatibility changes, if happen, they will
between major versions.
 - ``deprecated``: it will disappear in a future version.

See the latest [releases and tags](https://github.com/byexamples/byexample/tags)

Current version:

```shell
$ byexample -V
byexample 7.4.3 (Python <...>) - GNU GPLv3
<...>
Copyright (C) Di Paola Martin - https://github.com/byexamples/byexample
<...>
```

## License

This project is licensed under GPLv3

```shell
$ head -n 2 LICENSE     # byexample: +norm-ws
          GNU GENERAL PUBLIC LICENSE
           Version 3, 29 June 2007
```

See [LICENSE](https://github.com/byexamples/byexample/tree/master/LICENSE.md) for more details.

