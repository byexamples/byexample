import re, pexpect, sys, time
from byexample.byexample import ExampleParser

class PythonInterpreter(ExampleParser):
    """
    Example:
      >>> def hello():
      ...     print("hello bla world")

      >>> hello()           # doctest: +ELLIPSIS
      'hello...world'

    """

    def example_regex(self):
        return re.compile(r'''
            # Source consists of a PS1 line >>>
            # followed by zero or more PS2 lines.
            (?P<source>
                (?:^(?P<indent> [ ]*) >>>[ ]     .*)    # PS1 line
                (?:\n           [ ]*  \.\.\.   .*)*)    # PS2 lines
            \n?
            # Want consists of any non-blank lines that do not start with PS1
            (?P<expected> (?:(?![ ]*$)     # Not a blank line
                          (?![ ]*>>>)      # Not a line starting with PS1
                         .+$\n?            # But any other line
                      )*)
            ''', re.MULTILINE | re.VERBOSE)

    def example_options_regex(self):
        optstring_re = re.compile(r'#\s*byexample:\s*([^\n\'"]*)$',
                                                    re.MULTILINE)

        opt_re = re.compile(r'(?:(?P<add>\+)|(?P<del>-))(?P<name>\w+)',
                                                    re.MULTILINE)

        return optstring_re, opt_re

    def remove_prompts(self, source):
        return '\n'.join(line[4:] for line in source.split("\n"))

    def __repr__(self):
        return self.INTERPRETER_NAME

    INTERPRETER_NAME = "Python (%s)" % "/usr/bin/python"


    def run(self, example, flags):
        # we need to add an extra newline to
        # finish a definition like
        #    >>> def f()
        #    ...   pass
        self.py.send(example.source + '\n')

        self._expect_prompt()
        return self._get_output()

    def _expect_prompt(self, timeout=2):
        # now we wait for a PS1 prompt
        # if we get a timeout that could mean:
        #   - the code executed is taking too long to finish
        #   - the code is malformed and the interpreter is waiting
        #     more data like this:
        #     >>> [ 1, 2,
        #     ...   3, 4,
        #     (the ] is missing)
        # if we don't get a timeout that could mean:
        #   - good, we got the *last* prompt line
        #   - good but we may didn't get the *last* prompt line
        #     and we should try to find the next prompt again
        expect = [self.PS1, pexpect.TIMEOUT]
        PS1_found, Timeout = range(len(expect))

        what = self.py.expect(expect, timeout=timeout)
        self.last_output.append(self.py.before)

        if what == PS1_found:
            while what != Timeout:
                what = self.py.expect(expect, timeout=0.05)
                self.last_output.append(self.py.before)

            # good, we found a prompt and we couldn't find another prompt after
            # the last one so we should be on the *last* prompt
        elif what == Timeout:
            raise Exception("Prompt not found: the code is taking too long to finish or there is a syntax error. Until now we got (last 1000 bytes):\n%s" % self.py.before[-1000:])


    def _get_output(self):
        out = "".join(self.last_output)
        self.drop_output()

        # remove any other 'prompt'
        out = re.sub(self.PS2, '', out)

        # uniform the new line endings (aka universal new lines)
        out = re.sub(r'\r\n', r'\n', out)

        # TODO: is this ok?
        if out and not out.endswith('\n'):
            out += '\n'

        return out

    def drop_output(self):
        self.last_output = []

    def initialize(self):
        self.PS1 = "/byexample/py/ps1> "
        self.PS2 = "/byexample/py/ps2> "

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
''' % (self.PS1, self.PS2)

        self.py = pexpect.spawn("/usr/bin/python -i -c '%s'" % change_prompts,
                                echo=False)
        self.py.delaybeforesend = 0.010
        self.last_output = []

        time.sleep(0.01)
        self._expect_prompt(timeout=10)
        self.drop_output() # discard banner and things like that

    def shutdown(self):
        self.py.sendeof()
        self.py.close()
        time.sleep(0.01)
        self.py.terminate(force=True)
