How to extend
=============

There are three different ways in which ``byexample`` can be extended:

 - how to find examples
 - how to support new languages
 - how to perform arbitrary actions during the execution

``byexample`` uses the concept of modules: a python file with some classes
defined there.
What classes will depend of what you want to extend or customize.

To load a set of modules you can use the ``--modules <dir>`` parameter:
all the python files will be loaded and the classes with the correct interface
will be added.

Let's show this by example. Imagine that we want to write examples in
the mythical language ``ArnoldC``, a programming language which its
instruction set are phrases of the actor Arnold.

What do we need?

How to find examples: the Finder
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The first thing to teach ``byexample`` is how to find a ``ArnoldC``
example.

``byexample`` already has a generic finder, the fenced code block finder.

But just for fun, let's imagine that we want to do something different.
Let's say that our examples are enclosed by the ``~~~`` strings: anything
between two ``~~~`` will be considered a ``ArnoldC`` example.

Here is what I mean

.. code::

    This is an example which begins here
    ~~~
    IT'S SHOWTIME                       # byexample: +awesome
    TALK TO THE HAND "Hello World!"
    YOU HAVE BEEN TERMINATED
    out:
    Hello World!
    ~~~
    The code below should produce the famous 'Hello World!' output

Notice how below the code there is a ``out:`` tag. We will use this to
separate the code from the expected output.

Example regular expression
--------------------------

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

The capture's groups ``snippet``, ``indent`` and ``expected`` are mandatory.

The capture may be empty but those three groups must be defined.

The first should match the executable code, while the last the expected output
if any that to compare.

The ``indent`` group is to count how many spaces are not part of the example
and they are just for indentation. Some languages like Python are sensible to
this.

Language of
-----------

Then, the finder needs to determinate in which language the example
was written.

A Finder can be a generic finder that can extract examples of any language
(like from a Markdown fenced-code block) or it can be specific and tight to
a single language (like a specific Finder to find an interactive Python
session).

For our purposes let's say that anything between ``~~~`` is always an
``ArnoldC`` example.

The Finder class
----------------

Now we ensemble all the pieces together.
We need to create a class, inherit from ``MatchFinder``,
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

If two Finders try to find the same target, one will override the other.

This is useful if you want to use a different Finder in replacement for
an already created one: just create a class with the same ``target``.

Let's see if our finder can find the ArnoldC snippet above.

.. code:: python

    >>> finder = ArnoldCFinder(0, 'utf-8')
    >>> matches = finder.get_matches(open('docs/how_to_extend.rst', 'r').read())
    >>> matches = list(matches)

    >>> len(matches)
    1

    >>> match = matches[0]
    >>> print(match.group('snippet'))
        IT'S SHOWTIME                       # byexample: +awesome
        TALK TO THE HAND "Hello World!"
        YOU HAVE BEEN TERMINATED

    >>> print(match.group('expected'))
        Hello World!

Nice...

How to support new languages: the Parser and the Interpreter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To support new languages we need to be able to parse the code in the first place
and then, to execute it later.

Now that we have a raw snippet from the Finder we need to polish it and
extract the options the ``byexample`` uses to customize the example.

Option regular expressions
--------------------------

An option or options can be of any form and be in any place.
Typically we can write the options in the comments of the code which obviously
will depend of the language.

If the comments in ``ArnoldC`` starts with a ``#``, we can say that every comment
that starts with ``byexample`` is a comment to extract options.

This regular expression should capture that:

.. code:: python

    >>> opts_string_re = re.compile(r'#\s*byexample:\s*([^\n\'"]*)$',
    ...                                                re.MULTILINE)

The unnamed group should capture the option or options. How to extract
each individual option is a task for parser more complex than a regex.

``byexample`` will create a parser for us to parse all the common options (the
ones that ``byexample`` supports by default).
It is our job to extend this parser adding more flags or arguments to parse our
specific options.


.. code:: python

    >>> def extend_option_parser(parser):
    ...     parser.add_flag("awesome")
    ...     parser.add_flag("norm-ws", default=False)
    ...     parser.add_flag("capture", default=True)

See the documentation of ``byexample.options.OptionParser`` for more
information.

The Parser class
----------------

Now we ensemble all the pieces together.
We need to create a class, inherit from ``ExampleParser``,
define a ``language`` attribute and implement the missing methods:

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
    ...     
    ...     def extend_option_parser(self, parser):
    ...         return extend_option_parser(parser)

The user can select which languages should be parsed and executed and which
should not: the ``language`` attribute is used for that purpose.

The ``source_from_snippet`` is the last chance to change the source code.

Let's peek how the parsing is used

.. code:: python

     >>> from byexample.options import Options, OptionParser
     >>> parser = ArnoldCParser(0, 'utf-8', OptionParser(add_help=False), Options())

     >>> example_str = match.group(0)
     >>> where = (0,1,'docs/how_to_extend.rst')
     >>> interpreter = None # not yet
     >>> example = parser.get_example_from_match(match, example_str,
     ...                                         interpreter, finder, where)

     >>> print(example.source)
     IT'S SHOWTIME                       # byexample: +awesome
     TALK TO THE HAND "Hello World!"
     YOU HAVE BEEN TERMINATED

     >>> print(example.expected.str)
     Hello World!

     >>> print(example.options)
     {'norm_ws': False, 'capture': True, 'awesome': True}


The Interpreter class
---------------------

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

Now we ensemble the Interpreter class

.. code:: python

    >>> from byexample.interpreter import Interpreter
    >>> class ArnoldCInterpreter(Interpreter):
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

The ``initialize`` and ``shutdown`` method are called before and after the
execution of all the tests. It can be used to set up the real interpreter
or to perform some off-line task (like compiling).
You may want to change how to setup the interpreter based on the examples that
it will execute or in the options passed from the command line.

It is in the ``run`` method where the magic happen. Its task is to execute
the given source and to return the output, if any.

The ``options`` parameter are the parsed options (a dictionary). What to do
with them is up to you.

.. code:: python

    >>> interpreter = ArnoldCInterpreter(0, 'utf-8')
    >>> found = interpreter.run(example, example.options)

    >>> found
    'Hello World!\n'

    >>> print("PASS" if found == example.expected.str else "FAIL")
    PASS


How to perform arbitrary actions during the execution: Concern
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

During the execution of the whole set of examples, ``byexample`` will execute
some callbacks or hooks at particular moments like before running an example or
after it failed.

The set of hooks are collected into the Concern interface (also known as
Cross-Cutting Concern).

You can create and add your own to concerns to extend the capabilities of
``byexample``:

 - show the progress of the execution
 - log / report generation for export
 - log execution time history for future execution time prediction (estimate)
 - turn on/off debugging, coverage and profile facilities
 - others...

Let's imagine that we want to print each example before its execution for
debugging purposes.

But logging everything all the time is annoying. What we also want is to control
this from the command line.


.. code:: python

    >>> from byexample.concern import Concern

    >>> class PrintExampleDebug(Concern):
    ...    target = 'print-debug'
    ...    
    ...    def start_example(self, example, options):
    ...        print(example.source)
    ...


See the documentation of the class ``Concern`` in ``byexample/concern.py`` to get
a description of all the possible hooks and when they are called.

See the implementation of the progress bar in ``byexample/modules/progress.py``
as a practical example.


