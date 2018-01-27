"""
Example:
  >>> def hello():
  ...     print("hello bla world")

  >>> hello()
  hello<...>world

  ```python
  
  j = 2
  for i in range(4):
      j += i
  
  j + 3
  
  out:
  11
  ```

"""

import re, pexpect, sys, time
from byexample.parser import ExampleParser
from byexample.finder import MatchFinder
from byexample.interpreter import Interpreter, PexepctMixin

class PythonPromptFinder(MatchFinder):
    target = 'python-prompt'

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

    def get_language_of(self, *args, **kargs):
        return 'python'

class PythonParser(ExampleParser):
    language = 'python'

    def example_options_string_regex(self):
        # anything of the form:
        #   #  byexample:  +FOO -BAR +ZAZ=42
        return re.compile(r'#\s*byexample:\s*([^\n\'"]*)$',
                                                    re.MULTILINE)


    def source_from_snippet(self, snippet):
        lines = snippet.split("\n")
        if lines and lines[0].startswith(">>> "):
            return '\n'.join(line[4:] for line in lines)

        return snippet

class PythonInterpreter(Interpreter, PexepctMixin):
    language = 'python'

    def __init__(self, verbosity, encoding, **unused):
        self.encoding = encoding

        PS1 = r'/byexample/py/ps1> '
        PS2 = r'/byexample/py/ps2> '

        change_prompts = r'''
import sys
import pprint as _byexample_pprint

# change the prompts
sys.ps1="%s"
sys.ps2="%s"

# patch the pprint _safe_repr function
def patch_pprint_safe_repr():
    import re
    ub_marker_re = re.compile(r"^[uUbB]([rR]?[" + "\\" + chr(39) + r"\"])", re.UNICODE)
    orig_repr = _byexample_pprint._safe_repr
    def patched_repr(object, *args, **kargs):
        orepr, readable, recursive = orig_repr(object, *args, **kargs)

        _repr = ub_marker_re.sub(r"\1", orepr)
        readable = False if _repr != orepr else readable

        return _repr, readable, recursive
    _byexample_pprint._safe_repr = patched_repr

patch_pprint_safe_repr() # patch!

# change the displayhook to use pprint instead of repr
sys.displayhook = lambda s: (
                    None if s is None
                    else _byexample_pprint.PrettyPrinter(indent=1, width=80, depth=None).pprint(s))

# remove introduced symbols
del sys
del patch_pprint_safe_repr
''' % (PS1, PS2)

        PexepctMixin.__init__(self,
                                cmd="/usr/bin/env python -i -c '%s'" % change_prompts,
                                PS1_re = PS1,
                                any_PS_re = r'/byexample/py/ps\d> ')


    def run(self, example, flags):
        return self._exec_and_wait(example.source,
                                    timeout=int(flags['TIMEOUT']))

    def interact(self, example, options):
        PexepctMixin.interact(self)

    def initialize(self, examples, options):
        self._spawn_interpreter()

    def shutdown(self):
        self._shutdown_interpreter()
