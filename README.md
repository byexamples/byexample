<!--
Check that we have byexample installed first
$ hash byexample                                    # byexample: +fail-fast
-->

# ``byexample``

``byexample`` is a literate programming engine where you mix
ordinary text and snippets of code in the same file and then you
execute them as regression tests.

It lets you to execute the examples written in ``Python``, ``Ruby`` or whatever
in your documentation and validate them.

You can always be sure that the examples are correct and your documentation
is up to date!

## Usage

<img src="https://raw.githubusercontent.com/byexamples/byexample/master/media/demo.gif" alt="Sorry, it seems that you cannot see the demo. Another excuse to install byexample and test it by yourself ;)" width="75%" height="75%">

You [write your documentation with examples](https://byexamples.github.io/byexample/overview/where-should-I-write-the-examples)
in a Markdown or other text file.

Then, you run `byexample` from the command line selecting which
language or languages you want to run:
[Python](https://byexamples.github.io/byexample/languages/python),
[Ruby](https://byexamples.github.io/byexample/languages/ruby),
[Shell](https://byexamples.github.io/byexample/languages/shell) and
[C/C++](https://byexamples.github.io/byexample/languages/cpp) to
mention a few.

And yes, you can write examples in different languages in the same
file. [Combine them to combine their
strengths](https://byexamples.github.io/byexample/recipes/advanced-checks)
and make your life easier.

That's all. `byexample` will compare the output of the examples with the
expected ones and it will [show any
difference](https://byexamples.github.io/byexample/overview/differences).

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

Several languages are supported like ``Python``, ``Ruby`` and ``C++``
along with others.

Take at look at the official web page:
[https://byexamples.github.io](https://byexamples.github.io)

Some quick links:

- [Quick usage](https://byexamples.github.io/byexample/overview/usage)
- [Where should I write the examples?](https://byexamples.github.io/byexample/overview/where-should-I-write-the-examples)

## Languages supported

Currently we support:

 - [Python](https://byexamples.github.io/byexample/languages/python)
 - [Ruby](https://byexamples.github.io/byexample/languages/ruby)
 - [Javascript](https://byexamples.github.io/byexample/languages/javascript)
 - [Shell](https://byexamples.github.io/byexample/languages/shell)
 - [GDB](https://byexamples.github.io/byexample/languages/gdb)
 - [C/C++](https://byexamples.github.io/byexample/languages/cpp)
 - [Elixir](https://byexamples.github.io/byexample/languages/elixir)
 - [PHP](https://byexamples.github.io/byexample/languages/php)

More languages will be supported in the future. Stay tuned.

## Platforms supported

Linux is the preferable choice as it is very well tested.

Since `9.2.1` macOS is also supported for the testing is more limited
and it is expected to have little variations from Linux.

You can even run `byexample` in Windows`**` using
[Windows Subsystem for Linux](https://docs.microsoft.com/en-us/windows/wsl/install-win10)
but keep in mind that the testing is even more limited;
a native execution in Windows (outside of WSL) is currently not
supported.

## Contributing

First off, thanks for using and considering contributing to ``byexample``.

We love to receive contributions from our community. There are tons of ways you
can contribute

 - add support to new languages (Javascript, Julia, just listen to you heart). Check this [how to](https://byexamples.github.io/byexample/contrib/how-to-support-new-finders-and-languages).
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

Check out [how to support new finders and languages](https://byexamples.github.io/byexample/contrib/how-to-support-new-finders-and-languages)
and [how to hook to events with concerns](https://byexamples.github.io/byexample/contrib/how-to-hook-to-events-with-concerns) for
a quick tutorials that shows exactly how to do that.

You could also share your work and [contribute](https://github.com/byexamples/byexample/tree/master/CONTRIBUTING.md) to
``byexample`` with your extensions.

## Versioning

We use [semantic version](https://semver.org/) for the core or engine.

For each module we have the following categorization:

 - ``experimental``: non backward compatibility changes are possible or even
removal between versions (even patch versions).
 - ``provisional``: low impact non backward compatibility changes may occur
between versions; but in general a change like that will happen only between
major versions.
 - ``stable``: non backward compatibility changes, if happen, they will
between major versions.
 - ``deprecated``: it will disappear in a future version.

See the latest [releases and tags](https://github.com/byexamples/byexample/tags)
and the
[changelog](https://github.com/byexamples/byexample/releases)

Current version:

```shell
$ byexample -V
byexample 10.0.3 (Python <...>) - GNU GPLv3
<...>
Copyright (C) Di Paola Martin - https://byexamples.github.io
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

