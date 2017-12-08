import re, pexpect, sys, time
from byexample.parser import ExampleParser
from byexample.finder import ExampleMatchFinder
from byexample.interpreter import Interpreter, PexepctMixin

class RubyPromptFinder(ExampleMatchFinder):
    target = 'ruby-prompt'

    def example_regex(self):
        return re.compile(r'''
            # Snippet consists of one or more PS1 lines >>
            (?P<snippet>
                (?:^(?P<indent> [ ]*) >>[ ]     .*)    # PS1 line
                (?:\n           [ ]*  >>      .*)*)    # and more PS1 lines
            \n?
            # Want consists of any non-blank lines that do not start with PS1
            # The '=>' indicator is included (implicitly)
            (?P<expected> (?:(?![ ]*$)     # Not a blank line
                          (?![ ]*>>)       # Not a line starting with PS1
                         .+$\n?            # But any other line
                      )*)
            ''', re.MULTILINE | re.VERBOSE)

    def get_language_of(self, *args, **kargs):
        return 'ruby'

class RubyParser(ExampleParser):
    language = 'ruby'

    def example_options_regex(self):
        optstring_re = re.compile(r'#\s*byexample:\s*([^\n\'"]*)$',
                                                    re.MULTILINE)

        opt_re = re.compile(r'''
                (?:(?P<add>\+) | (?P<del>-))   #  + or - followed by
                (?P<name>\w+)                  # the name of the option and
                (?:=(?P<val>\w+))?             # optionally, = and its value

                ''', re.MULTILINE | re.VERBOSE)

        return optstring_re, opt_re

    def source_from_snippet(self, snippet):
        lines = snippet.split("\n")
        if lines and lines[0].startswith(">> "):
            return '\n'.join(line[3:] for line in lines)

        return snippet

class RubyInterpreter(Interpreter, PexepctMixin):
    ''' An interpreter for Ruby using irb.
        Example:
            >> def hello
            >>     'hello bla world'
            >> end;

            >> hello
            => "hello<...>world"

    '''
    language = 'ruby'

    def __init__(self, verbosity, encoding):
        PexepctMixin.__init__(self,
                                cmd='/usr/bin/irb',
                                PS1_re = r'irb[^:]*:\d+:0(>|\*) ',
                                any_PS_re = r'irb[^:]*:\d+:\d+(>|\*) ')

        self.encoding = encoding

    def run(self, example, flags):
        return self._exec_and_wait(example.source + '\n',
                                    timeout=int(flags['TIMEOUT']))

    def initialize(self):
        self._spawn_interpreter()

    def shutdown(self):
        self._shutdown_interpreter()
