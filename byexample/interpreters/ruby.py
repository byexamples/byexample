import re, pexpect, sys, time
from byexample.parser import ExampleParser
from byexample.interpreter import PexepctMixin

class RubyInterpreter(ExampleParser, PexepctMixin):
    ''' An interpreter for Ruby using irb.
        Example:
            rb> def hello
            ...     'hello bla world'
            ... end;

            rb> hello
            => "hello<...>world"

    '''
    def __init__(self, *args, **kargs):
        PexepctMixin.__init__(self,
                                cmd='/usr/bin/irb',
                                PS1_re = r'irb[^:]*:\d+:0(>|\*) ',
                                any_PS_re = r'irb[^:]*:\d+:\d+(>|\*) ')

        ExampleParser.__init__(self, *args, **kargs)

    def example_regex(self):
        return re.compile(r'''
            # Snippet consists of a PS1 line rb>
            # followed by zero or more PS2 lines.
            (?P<snippet>
                (?:^(?P<indent> [ ]*) rb>[ ]     .*)    # PS1 line
                (?:\n           [ ]*  \.\.\.   .*)*)    # PS2 lines
            \n?
            # Want consists of any non-blank lines that do not start with PS1
            # The '=>' indicator is included (implicitly)
            (?P<expected> (?:(?![ ]*$)     # Not a blank line
                         (?![ ]*rb>)       # Not a line starting with PS1
                         .+$\n?            # But any other line
                      )*)
            ''', re.MULTILINE | re.VERBOSE)

    def example_options_regex(self):
        optstring_re = re.compile(r'#\s*byexample:\s*([^\n\'"]*)$',
                                                    re.MULTILINE)

        opt_re = re.compile(r'(?:(?P<add>\+)|(?P<del>-))(?P<name>\w+)',
                                                    re.MULTILINE)

        return optstring_re, opt_re

    def source_from_snippet(self, snippet):
        return '\n'.join(line[4:] for line in snippet.split("\n"))

    def __repr__(self):
        return self.INTERPRETER_NAME

    INTERPRETER_NAME = "Ruby (%s)" % "/usr/bin/irb"

    def run(self, example, flags):
        return self._exec_and_wait(example.source + '\n', timeout=2)

    def initialize(self):
        self._spawn_interpreter()

    def shutdown(self):
        self._shutdown_interpreter()
