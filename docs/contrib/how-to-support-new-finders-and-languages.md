# Add New Languages

There are three different ways in which ``byexample`` can be extended:

 - how to find examples
 - how to support new languages
 - how to perform arbitrary actions during the execution

``byexample`` uses the concept of modules: a python file with some classes
defined there and it can be loaded using ``--modules <dir>`` from the command
line.

What classes will depend of what you want to extend or customize.

In this ``how-to`` we will go through the first two items: how to support
new finders and languages. Check
[how to hook to events with concerns](/{{ site.uprefix }}/contrib/how-to-hook-to-events-with-concerns)
for a ``how-to`` about the last one.

Let's show this by example.

Imagine that we want to write examples in the mythical language ``ArnoldC``,
a programming language which its instruction set are phrases of a famous
actor.

What do we need?

## How to find examples: the Finder

The first thing to teach ``byexample`` is how to find a ``ArnoldC``
example.

``byexample`` already has a generic finder, the
[fenced code block finder](/{{ site.uprefix }}/overview/where-should-I-write-the-examples).

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

### Find by snippet

To accomplish this we need to create a regular expression to find the
``~~~``, where the snippet of code is and where the expected output is.

```python
>>> import re

>>> example_re = re.compile(r'''
...     # begin with ~~~
...     ^[ ]*  ~~~  [ ]*\n
...
...     # the, grab everything until the 'out:' string
...     # this will be out snippet of code
...     (?P<snippet>
...         (?:^(?P<indent> [ ]*)[^ ] .*)   # first line: learn what is the
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
...     # this part of the regex is optional because no all the examples
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

### Spurious ends

It is likely that you may want to write your examples in a file and mark it
with some *mark-up* to render the code with syntax highlight.

For a Markdown you may wrap your example with ````` ``` ````` or ``~~~`` so
it can be highlighted.

If that's the case, you may write something like this:

`````
 ```python
 >>> print("My first example!")
 My first example!
 ```
`````

Notice how there is *not* a newline that separates the example from
the mark-up.

``byexample`` is *agnostic* of the format of the file but it will try to
remove those mark-ups if they are found at *the end* of an examples as it will
assume that they are not part of the example but they are just
part of the decoration.

``byexample`` tries to be *user friendly*.

But this has its limits; if this interfers with your finder,
you can tweak it and redefine these *spurious endings*.

In our ``ArnoldC`` example, we don't want to remove ``~~~`` because it *is*
part of the example:

```python
>>> def spurious_endings(self):
...     endings = ExampleFinder.spurious_endings(self)
...     return endings - {'~~~'}
```

Check also how this is
[seen and used](/{{ site.uprefix }}/overview/where-should-I-write-the-examples)
by the user of your new language.

### Detect the language

Then, the finder needs to determinate in which language the example
was written.

A Finder can be a generic finder that can extract examples of any language
(like from a Markdown fenced-code block) or it can be specific and tight to
a single language (like a specific Finder to find an interactive Python
session).

For our purposes let's say that anything between ``~~~`` is always an
``ArnoldC`` example.

### The Finder class

Now we ensemble all the pieces together.
We need to create a class, inherit from ``ExampleFinder``,
define a ``target`` attribute and implement few methods:

```python
>>> from byexample.finder import ExampleFinder
>>> class ArnoldCFinder(ExampleFinder):
...     target = 'ArnoldC-session'
...     specific = True
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
Finders must declare to which type of examples they are targeting.

If two Finders try to find the same target, one will override the other.

This is useful if you want to use a different Finder in replacement for
an already created one: just create a class with the same ``target``.

The other special attribute is ``specific``. If it is True, the finder is
specific to a language, like in this case.
If not, it is a generic Finder.

If two finders find the same example, the example found by the more specific
finder will be used.

If there is not a winner, ``byexample`` will use some heuristics to find a
single one and if it is still too unclear, ``byexample`` will print
an error. (check [byexample/finder.py](https://github.com/byexamples/byexample/tree/master/byexample/finder.py))

Let's see if our finder can find the ArnoldC snippet above.


```python
>>> finder = ArnoldCFinder(0, 'utf-8')

>>> filepath = 'docs/contrib/how-to-support-new-finders-and-languages.md'
>>> where = (0,1,filepath)
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
the prompts from the snippet to return a valid ``Python`` code.

## How to support new languages: the Parser and the Runner

To support new languages we need to be able to parse the code in the first place
and to execute it later.

Now that we have a raw snippet from the Finder we need to polish it and
extract the options that ``byexample`` uses to customize the example.

### Get the options

The [options](/{{ site.uprefix }}/basic/options) can be of any form and be in any place.

Typically we can write the options in the comments of the code which obviously
will depend of the language.

If the comments in ``ArnoldC`` starts with a ``#``, we can say that every comment
that starts with ``byexample`` is a comment that will contain options.

This regular expression should capture that:

```python
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
...     parser.add_flag("norm-ws", default=False)
...     parser.add_flag("tags", default=True)
...     parser.add_argument("+rm", action='append', default=[])
```

See the documentation of the class [OptionParser](https://github.com/byexamples/byexample/tree/master/byexample/options.py)
for more information.

> *Note:* the ``extend_option_parser`` in theory is called once for each
> example. However ``byexample`` calls it just once for the entire execution
> and caches the result for performance reasons.
>
> It is possible to tweak this or even to disable the cache entirely if you
> have to.
>
> See ``PythonParser`` in [byexample/modules/python.py](https://github.com/byexamples/byexample/tree/master/byexample/modules/python.py)
> for an example of this.
>
> In the same line, the extraction and parsing of the options are also cached.
> If two examples have the same options, they are parsed once.
>
> If you need to tweak or disable this you could override
> the class [ExampleParser](https://github.com/byexamples/byexample/tree/master/byexample/parser.py)

### The Parser class

Now we ensemble all the pieces together.

We need to create a class, inherit from ``ExampleParser``,
define a ``language`` attribute and implement the missing methods:

```python
>>> from byexample.parser import ExampleParser
>>> class ArnoldCParser(ExampleParser):
...     language = 'python'
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

Let's create the example:

```python
>>> from byexample.options import Options, OptionParser
>>> parser = ArnoldCParser(0, 'utf-8', Options(optparser=OptionParser(add_help=False)))

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

These attributes are completed using the parser. It is the parse who only
knows how to extract these from a *raw* example because is a language
specific task.

```python
>>> example = example.parse_yourself()

>>> print(example.source)
IT'S SHOWTIME                       # byexample: +awesome
TALK TO THE HAND "Hello World!"
YOU HAVE BEEN TERMINATED

>>> print(example.expected.str)
Hello World!

>>> print(example.options)
{'awesome': True, 'norm_ws': False, 'rm': [], 'tags': True}
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
...     language = 'python'
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

You may want to change how to setup the interpreter or the compiler based on
the examples that it will execute or in the options passed from the command
line.

The ``options`` parameter are the parsed options (plus the
[options](/{{ site.uprefix }}/basic/options) that come from the command line).

It is in the ``run`` method where the magic happen.

Its task is to execute the given source and to return the output, if any.

What to do with them is up to you.

```python
>>> runner = ArnoldCRunner(0, 'utf-8')
>>> found = runner.run(example, example.options)

>>> found
'Hello World!\n'

>>> print("PASS" if found == example.expected.str else "FAIL")
PASS
```

## That's all. Congrats!
