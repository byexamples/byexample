# Add New Languages

There are three different ways in which ``byexample`` can be extended:

 - define zones where to find examples
 - support new languages: how to find them and how to run them
 - perform arbitrary actions during the execution

``byexample`` uses the concept of modules: a python file with some extension
classes defined there. Modules can be loaded using ``--modules <dir>``
from the command line.

What extension classes will depend of what you want to extend or customize.

In this ``how-to`` we will see how to add a new language.

Check [how to define new zones where to find examples](/{{ site.uprefix }}/contrib/how-to-define-new-zones-where-to-find-examples)
and [how to hook to events with concerns](/{{ site.uprefix }}/contrib/how-to-hook-to-events-with-concerns)
for a ``how-to`` about the first and last items.

Imagine that we want to write examples in the mythical language ``ArnoldC``,
a programming language which its instruction set are phrases of a famous
actor.

What do we need?

## How to find examples: the Finder

The first thing to teach ``byexample`` is how to find a ``ArnoldC``
example.

Most of the languages supported by ``byexample`` use a *prompt* to mark
the begin of an example.

But just for fun, let's imagine that we want to do something different.
Let's say that our examples are enclosed by the ``~~~`` strings: anything
between two ``~~~`` will be considered a ``ArnoldC`` example.

Here is what I mean

```
This is an example which begins here
    ~~~
    IT'S SHOWTIME                       # byexample: +awesome
    TALK TO THE HAND "Hello World!"
    YOU HAVE BEEN TERMINATED

    out:
    Hello World!
    ~~~
The code below should produce the famous 'Hello World!' output
```

Notice how below the code there is a ``out:`` tag. We will use this to
separate the code from the expected output.

### Find the snippet of code

To accomplish this we need to create a regular expression to find the
``~~~``, where the snippet of code is and where the expected output is.

```python
>>> from byexample import regex as re

>>> example_re = re.compile(r'''
...     # begin with ~~~
...     ^[ ]*  ~~~  [ ]*\n
...
...     # grab everything until the 'out:' string
...     # this will be our snippet of code
...     (?P<snippet>
...         (?:^(?P<indent> [ ]*)[^ ] .*)   # first line: learn what is
...                                         # the level of indentation
...
...         (?:\n                           # grab everything else...
...                 (?![ ]*out:[ ]*\n)      # except if the line starts
...                                         # with out:
...                 (?![ ]*~~~)             # or with ~~~
...
...         .*)*)                           # anything else is welcome
...     \n?
...
...     # now, if we find 'out:', grab the expected output
...     # this part of the regex is optional because not all the examples
...     # output something to compare with.
...     (?: [ ]* out:[ ]*\n
...         (?P<expected> (?:
...                       (?![ ]*~~~)      # except a ~~~ line,
...                      .+$\n?            # grab everything!
...                   )*)
...     )?
...
...     # finally, the end marker
...     ^[ ]*  ~~~  [ ]*$
...
...     ''', re.MULTILINE | re.VERBOSE)
```

The capture's groups ``snippet``, ``indent`` and ``expected`` are mandatory.

The capture may be empty but those three groups must be defined.

The first should match the executable code, while the last the expected output
if any that to compare.

The ``indent`` group is to count how many spaces are not part of the example
and they are just for indentation: ``byexample`` will *drop* the first line that
has a lower level of indentation and any subsequent line.

> *Changed* in `byexample 10.0.0`. Before `10.0.0` you could return a
> Python regular expression but from `10.0.0` and on, you need to return
> the regular expressions created by `byexample.regex`. The module is
> almost identical to Python's `re` so the required changes are minimal.

### Detect the language

Then, the finder needs to determinate in which language the example
was written.

For our purposes let's say that anything between ``~~~`` is always an
``ArnoldC`` example but the same finder could find examples of
different languages.

### The Finder class

Now we assemble all the pieces.
We need to create a class, inherit from ``ExampleFinder``,
define a ``target`` attribute and implement a few methods:

```python
>>> from byexample.finder import ExampleFinder
>>> class ArnoldCFinder(ExampleFinder):
...     target = 'ArnoldC-session'
...
...     def example_regex(self):
...         global example_re
...         return example_re   # defined above
...
...     def get_language_of(self, options, match, where):
...         return 'ArnoldC'
...
...     def spurious_endings(self):
...         return spurious_endings(self) # defined above
```

The ``target`` attribute may need a little explanation. All the
Finders must declare which type of examples they are targeting.

If two finders try to find the same target, one will override the other.

This is useful if you want to use a different `Finder` in replacement for
an already created one: just create a class with the same ``target``.

Let's see if our finder can find the `ArnoldC` snippet above.

```python
>>> from byexample.cfg import Config
>>> finder = ArnoldCFinder(cfg=Config(verbosity=0, encoding='utf-8'))

>>> filepath = 'docs/contrib/how-to-support-new-finders-and-languages.md'
>>> where = (0,1,filepath,None)
>>> matches = finder.get_matches(open(filepath, 'r').read())
>>> matches = list(matches)

>>> len(matches)
1

>>> match = matches[0]

>>> indent = match.group('indent')
>>> len(indent)
4

>>> snippet, expected = finder.get_snippet_and_expected(match, where)
>>> print(snippet)
IT'S SHOWTIME                       # byexample: +awesome
TALK TO THE HAND "Hello World!"
YOU HAVE BEEN TERMINATED

>>> print(expected)
Hello World!
```

The ``get_snippet_and_expected`` by default gets the ``snippet`` and the
``expected`` groups from the match. But you can extend this to post-process
the strings.

Take a look of the implementation of ``PythonFinder``
(in [byexample/modules/python.py](https://github.com/byexamples/byexample/tree/master/byexample/modules/python.py))

The ``PythonFinder`` will find and match ``Python`` examples that starts with
the prompt ``>>>``; later, it extends ``get_snippet_and_expected`` to remove
the prompts from the snippet to return valid ``Python`` code.

## How to support new languages: the Parser and the Runner

To support new languages we need to be able to parse the code in the first place
and to execute it later.

Now that we have a raw snippet from the Finder we need to polish it and
extract the options that ``byexample`` uses to customize the example.

### Get the options

The [options](/{{ site.uprefix }}/basic/options) can be of any form and be in any place.

Typically we can write the options in the comments of the code which obviously
will depend on the language.

If the comments in ``ArnoldC`` starts with a ``#``, we can say that every comment
that starts with ``byexample`` is a comment that will contain options.

This regular expression should capture that:

```python
>>> from byexample import regex as re
>>> opts_string_re = re.compile(r'#\s*byexample:\s*([^\n\'"]*)$',
...                                                re.MULTILINE)
```

The unnamed group should capture the option or options; how to extract
each individual option is a task for more complex parser than a simple regex.

``byexample`` will create a parser for us to parse all the common options (the
ones that ``byexample`` supports by default).

It is our job to extend this parser adding more flags or arguments to parse our
own specific options (``ArnoldC``'s specific).

```python
>>> def extend_option_parser(parser):
...     parser.add_flag("awesome")
```

See the documentation of the class [OptionParser](https://github.com/byexamples/byexample/tree/master/byexample/options.py)
for more information.

> *Note:* the ``extend_option_parser`` in theory is called once for each
> example. However ``byexample`` calls it as few times as possible
> for performance reasons.
>
> The extraction and parsing of the options are cached: if two examples
> have the same options, they are parsed once and therefor
> the parser itself is extended just once.
>
> If you need to tweak or disable this you could override methods of
> the class [ExampleParser](https://github.com/byexamples/byexample/tree/master/byexample/parser.py)

### The Parser class

Now we assemble all the pieces.

We need to create a class, inherit from ``ExampleParser``,
define a ``language`` attribute and implement the missing methods:

```python
>>> from byexample.parser import ExampleParser
>>> class ArnoldCParser(ExampleParser):
...     language = 'arnold'
...
...     def example_options_string_regex(self):
...         global opts_string_re
...         return opts_string_re
...
...     def extend_option_parser(self, parser):
...         return extend_option_parser(parser)
```

The user can select which languages should be parsed and executed and which
should not from the command line with the flag ``-l``.

So we need to declare what language is our Parser for: that's the reason
behind the ``language`` attribute.

Optionally you can add define the ``flavors`` attribute: a set of
different flavors for your language that you have support that the user
can select with ``-l`` (parse the example in a different way perhaps?).

Let's create the example (in the practice this is done by ``byexample`` behind
the scenes so you do not to be worry about the details):

```python
>>> from byexample.options import Options, OptionParser
>>> parser = ArnoldCParser(cfg=Config(verbosity=0, encoding='utf-8', options=Options(rm=[], norm_ws=False, tags=True, capture=True, type=False, input_prefix_range=(6,12), optparser=OptionParser(add_help=False))))

>>> from byexample.finder import Example
>>> runner = None # not yet
>>> example = Example(finder, runner, parser,
...                   snippet, expected, indent, where)
```

At this point, the example created is incomplete as its source code wasn't
extracted from the snippet nor its options.

```python
>>> example.source
<...>
AttributeError: 'Example' object has no attribute 'source'

>>> example.options
<...>
AttributeError: 'Example' object has no attribute 'options'
```

These attributes are completed using the parser who is the only one that
knows how to extract these options from a *raw* example because is a language
specific task.

```python
>>> from byexample.log import init_log_system
>>> init_log_system()   # needed becuase parse_yourself requires the log system

>>> example = example.parse_yourself()

>>> print(example.source)
IT'S SHOWTIME                       # byexample: +awesome
TALK TO THE HAND "Hello World!"
YOU HAVE BEEN TERMINATED

>>> print(example.expected.str)
Hello World!

>>> print(example.options)
{'awesome': True}
```

The ``process_snippet_and_expected`` method can be extended to perform the last
minute changed to the snippet and the expected strings, after the parsing of the
options.

```python
>>> hasattr(ExampleParser, 'process_snippet_and_expected')
True
```

See ``GDBParser`` in [byexample/modules/gdb.py](https://github.com/byexamples/byexample/tree/master/byexample/modules/gdb.py).

The implementation extends this method to remove any comment on the snippet
because ``GDB`` doesn't support them.

Other useful example is ``PythonParser`` [byexample/modules/python.py](https://github.com/byexamples/byexample/tree/master/byexample/modules/python.py)
It modifies heavily the expected string to support a compatibility mode with ``doctest``.

#### TL;DR - Options from the command line and from the examples

`byexample` allow the user to pass options from the command line via
`-o`. These options are the same that you can set on each example but
they affect to the whole execution.

Following our `+awesome` example we could call `byexample` like:

```shell
$ byexample -l arnold -o=+awesome somefile.md       # byexample: +skip
```

Parsing the options from the command line is done by
`ExampleParser.extract_cmdline_options` while the parsing from each
example is done by `ExampleParser.extract_options`.

In general you don't need to worry about those two: `byexample`
uses the your option parser provided by `extend_option_parser`
in a reasonable manner.

Only if you want to do something more sophisticated you may want to
override those two methods. Just remember to call the parent method
and keep in mind that while the parsing of the options from the command
line happens in the `main` thread, the rest of the parsing happens on
each `worker` (this is relevant only if you need to *share* information between
them, in which case you need to [share data safety](/{{ site.uprefix }}/contrib/concurrency-model).)

### The Runner class

The Runner is who will execute the code.

Most of the times it is a proxy to a real interpreter but it can be a mix
of compiler/runner depending of the underlying language.

To see how this 'proxy' class can interact with another program, check the
implementation of the Python and Ruby Interpreters of ``byexample`` in
[byexample/modules/python.py](https://github.com/byexamples/byexample/tree/master/byexample/modules/python.py) and
[byexample/modules/ruby.py](https://github.com/byexamples/byexample/tree/master/byexample/modules/ruby.py)

For our case, we will implement a small toy-interpreter in ``Python`` itself so
you do not need to install a real ``ArnoldC`` compiler.


```python
>>> from byexample import regex as re
>>> def toy_arnoldc_interpreter(source_code):
...     output = []
...     for line in source_code.split('\n'):
...         if line.startswith("TALK TO THE HAND"):
...             to_print = re.search(r'"([^"]*)"', line).group(1)
...             output.append(to_print + '\n')
...
...     return '\n'.join(output)
```

Now we ensemble the ``ExampleRunner`` subclass

```python
>>> from byexample.runner import ExampleRunner
>>> class ArnoldCRunner(ExampleRunner):
...     language = 'arnold'
...
...     def run(self, example, options):
...         return toy_arnoldc_interpreter(example.source)
...
...     def initialize(self, examples, options):
...         pass
...
...     def shutdown(self):
...         pass
```

The ``initialize`` and ``shutdown`` methods are called before and after the
execution of all the tests. It can be used to set up the real interpreter
or to perform some off-line task (like compiling).

If possible, try to implement the ``cancel`` method to cancel an ongoing
example and support the recovery after a [timeout](/{{ site.uprefix }}/basic/timeout).

You may want to change how to setup the interpreter or the compiler based on
the examples that it will execute or in the options passed from the command
line.

The ``options`` parameter are the parsed options (plus the
[options](/{{ site.uprefix }}/basic/options) that come from the command line).

It is in the ``run`` method where the magic happen.

Its task is to execute the given source and to return the output, if any.

What to do with them is up to you.

```python
>>> runner = ArnoldCRunner(cfg=Config(verbosity=0, encoding='utf-8'))
>>> found = runner.run(example, example.options)

>>> found
'Hello World!\n'

>>> print("PASS" if found == example.expected.str else "FAIL")
PASS
```

Like in the `Parser`, you can define the optional ``flavors`` attribute
to accept different flavors of the same language. The constructor of you
`Runner` will receive the `language_flavors` argument with the list
selected by the user so you can do something different on each case.

## Concurrency model

Each `ExampleFinder`, `ExampleParser` and `ExampleRunner` instances
will be created *once* during the setup of
`byexample` and then it will be created *once per job* thread.

By default there is only one job thread but more threads can be added
with the `--jobs` option.

If you want to *share* data among them you will have to use a
thread-safe structures created by a `sharer` and store them
in a `namespace`.

In the [concurrency model](/{{ site.uprefix }}/contrib/concurrency-model)
documentation it is explained and in
[byexample/modules/progress.py](https://github.com/byexamples/byexample/tree/master/byexample/modules/progress.py)
you can see a concrete example.

> *Changed* in `byexample 10.0.0`. Before `10.0.0` you were forced to
> use `multiprocessing` by hand but in `10.0.0` the concurrency model
> is hidden so you cannot relay on `multiprocessing` because `byexample`
> may not use processes at all!
> `sharer` and `namespace` are objects that hide the details while
> allowing you to have the same power.

## `ExampleFinder`, `ExampleParser` and `ExampleRunner` initialization

If you decide to implement your own `__init__`,
you must ensure that you call parent class' `__init__` method
passing to it all the keyword-only arguments that you received.

Once done that, you can use the `self.cfg` property to access any
configuration set in `byexample` including the flags/options set
(`self.cfg.options`).

In the `__init__` you can also change the value of `target` (for the
`ExampleFinder`) and the value of language (for `ExampleParser` and
`ExampleRunner`) based on the configuration.

You can use it for example to disable the finder/parser/runner setting
`target` / `language` to `None` dynamically.

See
[Extension initialization](/{{ site.uprefix }}/contrib/extension-initialization)
for more about this and some troubleshooting.

> *New* in ``byexample 11.0.0``: `self.cfg` was introduced.
