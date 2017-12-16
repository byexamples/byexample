How to extend
=============

``byexample`` uses three concepts to find, parse and execute the
examples of a file. The three concepts can be extended to find examples
in different files or to parse and run other languages.

Let's show them by example. Imagine that we want to write examples in
the mytical language ``ArnoldC``, a programming language which its
instruction set are phrases of the actor Arnold.

What do we need?

Finder
------

The first thing to teach ``byexample`` is how to find a ``ArnoldC``
example.

Just for fun, let's imagine that our examples are encloded by the ``~~~``
strings. Anything between two ``~~~`` will be considered a ``ArnoldC``
example.

To discriminate where the code ends and the expected result begins, let's say
that everything after the ``out:`` string is the expected result.

Here is what I mean

.. code::

    This is an example which begins here
    ~~~
    IT'S SHOWTIME   # byexample: +awesome
    TALK TO THE HAND "Hello World!"
    YOU HAVE BEEN TERMINATED
    out:
    Hello World!
    ~~~
    The code below should produce the famous 'Hello World!' output

Example regular expression
^^^^^^^^^^^^^^^^^^^^^^^^^^

To accomplish this we need to create a regular expression to find the
``~~~``, where the snippet of code is and where the expected output is.

.. code:: python

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

This capture groups ``snippet``, ``indent`` and ``expected`` are mandatory.
The capture may be empty but those three groups must be defined.
The first should match the executable code, while the last the expected output
if any that to compare.
The ``indent`` group is to count how many spaces are not part of the example
and they are just for indentation. Some languages like Python are sensible to
this.

Language of
^^^^^^^^^^^

Then, the finder will need to determinate in which language the example
was written.

A Finder can be a generic finder that can extract examples of any language
(like from a Markdown fenced-code block) or it can be specific and tight to
a single language (like a specific Finder to find an interactive Python
session).

For our purposes let's say that anything between ``~~~`` is always an
``ArnoldC`` example.

Finder class
^^^^^^^^^^^^

Now we ensample every pieces together.
We need to create a class, inheret from ``MatchFinder``,
define a ``target`` attribute and implement two methods:

.. code:: python

    >>> from byexample.finder import MatchFinder
    >>> class ArnoldCFinder(MatchFinder):
    ...     target = 'ArnoldC-session'
    ...     
    ...     def example_regex(self):
    ...         global example_re
    ...         return example_re
    ...     
    ...     def get_language_of(self, options, match, where):
    ...         return 'ArnoldC'

The ``target`` attribute may need a little explanation. All the
Finders must declare to which type of examples they are targeting.

If two Finders try to find the same target, one will cover the other.

This is useful if you want to use a different Finder in replacement for
an already created Finder. Just create a class with the same ``target``.

Let's see if our finder can find the ArnoldC snippet above.

.. code:: python

    >>> finder = ArnoldCFinder(0, 'utf-8')
    >>> matches = finder.get_matches(open('docs/how_to_extend.rst', 'r').read())
    >>> matches = list(matches)

    >>> len(matches)
    1

    >>> match = matches[0]
    >>> print(match.group('snippet'))
        IT'S SHOWTIME   # byexample: +awesome
        TALK TO THE HAND "Hello World!"
        YOU HAVE BEEN TERMINATED

    >>> print(match.group('expected'))
        Hello World!
    <blankline>

Nice...

Parser
------

Now that we have a raw snippet from the Finder we need to polish it and
extract the options the ``byexample`` uses to customize the example.

Option regular expressions
^^^^^^^^^^^^^^^^^^^^^^^^^^

An option or options can be of any form and be in any place.
Tipically we can write the options in the comments of the code which obviously
will depend of the language.

If the comments in ``ArnoldC`` starts with a ``#``, we can say that every comment
that starts with ``byexample`` is a comment to extract options.

This regular expression should capture that:

.. code:: python

    >>> opts_string_re = re.compile(r'#\s*byexample:\s*([^\n\'"]*)$',
    ...                                                re.MULTILINE)

The unnamed group should capture the option or options. How to extract
each individual option is a task for another regular expression.

This last one needs to support
 - if the 'add' group is present, add an option (aka set to it to True)
 - if the 'del' group is present, delete an option (aka set to it to False)
 - if the 'val' group is present, use it as the value of the option

In addition to those three named group, the regular expression needs to
define an another one: the 'name' group to capture the name of the option.

.. code:: python

    >>> opt_re = re.compile(r'''
    ...     (?:(?P<add>\+) | (?P<del>-))   #  + or - followed by
    ...     (?P<name>\w+)                  # the name of the option and
    ...     (?:=(?P<val>\w+))?             # optionally, = and its value
    ...
    ...     ''', re.MULTILINE | re.VERBOSE)

Parser class
^^^^^^^^^^^^

Now we ensample every pieces together.
We need to create a class, inheret from ``ExampleParser``,
define a ``language`` attribute and implement the missing  methods:

.. code:: python

    >>> from byexample.parser import ExampleParser
    >>> class ArnoldCParser(ExampleParser):
    ...     language = 'python'
    ...     
    ...     def example_options_string_regex(self):
    ...         global opts_string_re
    ...         return opts_string_re
    ...     
    ...     def example_option_regex(self):
    ...         global opt_re
    ...         return opt_re
    ...     
    ...     def source_from_snippet(self, snippet):
    ...         return snippet

The user can select which languages should be parsed and executed and which
should not: the ``language`` attribute is used for that purpose.

The ``source_from_snippet`` is the last change to change the source code.

Let's peek how the parsing is used

.. code:: python

     >>> from byexample.options import Options
     >>> parser = ArnoldCParser(0, 'utf-8')

     >>> example_str = match.group(0)
     >>> where = (0,1,'docs/how_to_extend.rst')
     >>> interpreter = None # not yet
     >>> example = parser.get_example_from_match(Options(), match, example_str,
     ...                                         interpreter, where)

     >>> print(example.source)
     IT'S SHOWTIME   # byexample: +awesome
     TALK TO THE HAND "Hello World!"
     YOU HAVE BEEN TERMINATED
     <blankline>

     >>> print(example.expected)
     Hello World!
     <blankline>

     >>> print(example.options)
     {'awesome': True}


Interpreter
-----------

The Interpreter is who will execute the code. It is not necessary a real
interpreter, for almost all the languages you want to use a real official
interpreter: your Interpreter class will be just a proxy.

To see how this 'proxy' class can interact with another program, check the
implementation of the Python and Ruby Interpreters of ``byexample``

For our case, we will implement a small toy-interpreter in Python itself so
you do not need to install a real ``ArnoldC`` compiler.

.. code:: python

    >>> def toy_arnoldc_interpreter(source_code):
    ...     output = []
    ...     for line in source_code.split('\n'):
    ...         if line.startswith("TALK TO THE HAND"):
    ...             to_print = re.search(r'"([^"]*)"', line).group(1)
    ...             output.append(to_print + '\n')
    ...     
    ...     return '\n'.join(output)

Now we ensample the Interpreter class

.. code:: python

    >>> from byexample.interpreter import Interpreter
    >>> class ArnoldCInterpreter(Interpreter):
    ...     language = 'python'
    ...     
    ...     def run(self, example, options):
    ...         return toy_arnoldc_interpreter(example.source)
    ...     
    ...     def initialize(self):
    ...         pass
    ...     
    ...     def shutdown(self):
    ...         pass

The ``initialize`` and ``shutdown`` method are called before and after the
execution of all the tests. It can be used to set up the real interpreter
or to perform some off-line task (like compiling)

It is in the ``run`` method where the magic happen. Its task is to execute
the given source and to return the output, if any.
The ``options`` parameter are the parsed options (a dictionary). What to do
with them is up to you.

.. code:: python

    >>> interpreter = ArnoldCInterpreter(0, 'utf-8')
    >>> found = interpreter.run(example, example.options)

    >>> found
    'Hello World!\n'

    >>> print("PASS" if found == example.expected else "FAIL")
    PASS


Extending ``byexample``
-----------------------

You can create a new Finder to extend how to extract examples (not necessary
you need to support new languages).
You can create a new Parser and/or a new Interpreter to support a new languages
(not necessary you need to define new ways to find those examples)

Now that we created three new classes, what do we need to do to integrate them
into ``byexample``.

``byexample`` will load any python module in some predefined directories.
You can put your classes there or you can instruct ``byexample`` to search
more modules in a directory of your choice from the command line.

