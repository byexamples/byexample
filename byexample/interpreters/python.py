import re, pexpect, sys, time
from byexample.parser import ExampleParser
from byexample.interpreter import PexepctMixin

class PythonInterpreter(ExampleParser, PexepctMixin):
    """
    Example:
      >>> def hello():
      ...     print("hello bla world")

      >>> hello()
      hello<...>world

    """

    def __init__(self, *args, **kargs):
        PS1 = r'/byexample/py/ps1> '
        PS2 = r'/byexample/py/ps2> '

        change_prompts = r'''
import sys, pprint

# change the prompts
sys.ps1="%s"
sys.ps2="%s"

class __Printer(pprint.PrettyPrinter):
    def __init__(self, *args, **kargs):
        import pprint, re
        pprint.PrettyPrinter.__init__(self, *args, **kargs)
        r = r"(\W|^)[uUbB]([rR]?[" + "\\" + chr(39) + r"\"])"
        self.ub_marker_re = re.compile(r, re.UNICODE)

    def format(self, object, context, maxlevels, level):
        import pprint, re
        parent_format = pprint.PrettyPrinter.format
        orepr, readable, recursive = parent_format(self, object, context,
                                                  maxlevels, level)

        repr = re.sub(self.ub_marker_re, r"\1\2", orepr)
        readable = False if repr != orepr else readable

        return repr, readable, recursive

# change the displayhook to use pprint instead of repr
sys.displayhook = lambda s: (
                    None if s is None
                    else __Printer(indent=1, width=80, depth=None).pprint(s))

# remove the introduced names
del sys
del pprint
''' % (PS1, PS2)

        PexepctMixin.__init__(self,
                                cmd="/usr/bin/python -i -c '%s'" % change_prompts,
                                PS1_re = PS1,
                                any_PS_re = r'/byexample/py/ps\d> ')

        ExampleParser.__init__(self, *args, **kargs)

    def example_regex(self):
        return re.compile(r'''
            # Snippet consists of a PS1 line >>>
            # followed by zero or more PS2 lines.
            (?P<snippet>
                (?:^(?P<indent> [ ]*) >>>[ ]     .*)    # PS1 line
                (?:\n           [ ]*  \.\.\.   .*)*)    # PS2 lines
            \n?
            # The expected output consists of any non-blank lines
            # that do not start with PS1
            (?P<expected> (?:(?![ ]*$)     # Not a blank line
                          (?![ ]*>>>)      # Not a line starting with PS1
                         .+$\n?            # But any other line
                      )*)
            ''', re.MULTILINE | re.VERBOSE)

    def example_options_regex(self):
        # anything of the form:
        #   #  byexample:  +FOO -BAR +ZAZ=42
        optstring_re = re.compile(r'#\s*byexample:\s*([^\n\'"]*)$',
                                                    re.MULTILINE)

        opt_re = re.compile(r'''
                (?:(?P<add>\+) | (?P<del>-))   #  + or - followed by
                (?P<name>\w+)                  # the name of the option and
                (?:=(?P<val>\w+))?             # optionally, = and its value

                ''', re.MULTILINE | re.VERBOSE)

        return optstring_re, opt_re

    def source_from_snippet(self, snippet):
        return '\n'.join(line[4:] for line in snippet.split("\n"))

    def __repr__(self):
        return self.INTERPRETER_NAME

    INTERPRETER_NAME = "Python (%s)" % "/usr/bin/python"


    def run(self, example, flags):
        # we need to add an extra newline to
        # finish a definition like
        #    >>> def f()
        #    ...   pass
        return self._exec_and_wait(example.source + '\n',
                                    timeout=int(flags['TIMEOUT']))

    def initialize(self):
        self._spawn_interpreter()

    def shutdown(self):
        self._shutdown_interpreter()
