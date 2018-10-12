"""
Example:
  (gdb) info files
  (gdb) print 1 + 2
  $1 = 3

"""

import re, pexpect, sys, time
from byexample.common import constant
from byexample.parser import ExampleParser
from byexample.finder import ExampleFinder
from byexample.runner import ExampleRunner, PexepctMixin, ShebangTemplate

stability = 'experimental'

class GDBPromptFinder(ExampleFinder):
    target = 'gdb-prompt'

    @constant
    def example_regex(self):
        return re.compile(r'''
            # Snippet consists of a single prompt line (gdb)
            (?P<snippet>
                (?:^(?P<indent> [ ]*) \(gdb\)[ ]     .*)
            )
            \n?
            # The expected output consists of any non-blank lines
            # that do not start with the prompt
            (?P<expected> (?:(?![ ]*$)     # Not a blank line
                          (?![ ]*\(gdb\))  # Not a line starting with the prompt
                         .+$\n?            # But any other line
                      )*)
            ''', re.MULTILINE | re.VERBOSE)

    def get_language_of(self, *args, **kargs):
        return 'gdb'

    def get_snippet_and_expected(self, match, where):
        snippet, expected = ExampleFinder.get_snippet_and_expected(self, match, where)

        snippet = self._remove_prompts(snippet)
        return snippet, expected

    def _remove_prompts(self, snippet):
        return snippet[6:]     # remove the (gdb) prompt

class GDBParser(ExampleParser):
    language = 'gdb'

    @constant
    def example_options_string_regex(self):
        # anything of the form:
        #   #  byexample:  +FOO -BAR +ZAZ=42
        return re.compile(r'#\s*byexample:\s*([^\n\'"]*)$',
                                                    re.MULTILINE)

    def process_snippet_and_expected(self, snippet, expected):
        snippet, expected = ExampleParser.process_snippet_and_expected(self,
                                            snippet, expected)
        # remove any option string, gdb does not support
        # comments. If we do not do this, gdb will complain
        snippet = self.example_options_string_regex().sub('', snippet)

        return snippet, expected


class GDBInterpreter(ExampleRunner, PexepctMixin):
    language = 'gdb'

    def __init__(self, verbosity, encoding, **unused):
        self.encoding = encoding

        # --nh     do not read ~/.gdbinit
        # --nx     do not read any .gdbinit
        # --quiet  do not print version number on startup
        PexepctMixin.__init__(self,
                                PS1_re = r'\(gdb\)[ ]',
                                any_PS_re = r'\(gdb\)[ ]')

    def get_default_cmd(self, *args, **kargs):
        return  "%e %p %a", {
                    'e': "/usr/bin/env",
                    'p': "gdb",
                    'a': [
                            "--nh",  # do not read ~/.gdbinit.
                            "--nx",  # do not read any .gdbinit files in any directory
                            "--quiet", # do not print version on startup
                        ]
                    }

    def run(self, example, flags):
        if not example.source:
            return ''

        # be extra carefully. if we add an extra newline, gdb
        # will rexecute the last command again.
        if example.source.endswith('\n'):
            source = example.source[:-1]

        return self._exec_and_wait(source, timeout=int(flags['timeout']))

    def interact(self, example, options):
        PexepctMixin.interact(self)

    def initialize(self, options):
        shebang, tokens = self.get_default_cmd()
        shebang = options['shebangs'].get(self.language, shebang)

        cmd = ShebangTemplate(shebang).quote_and_substitute(tokens)
        self._spawn_interpreter(cmd, delaybeforesend=options['delaybeforesend'],
                                     geometry=options['geometry'])

        # gdb will not print the address of a variable by default
        self._exec_and_wait('set print address off\n', timeout=1)

        # gdb will stop at the first null when printing an array
        self._exec_and_wait('set print null-stop on\n', timeout=1)

        # gdb will not ask for "yes or no" confirmation
        self._exec_and_wait('set confirm off\n', timeout=1)

    def shutdown(self):
        self._shutdown_interpreter()

