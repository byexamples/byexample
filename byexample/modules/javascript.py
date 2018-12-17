'''
Javascript code (using nodejs).

> 1 + 2;
3

The "out:" label marks the begin of the expected output to compare.

The semicolons are optional (as long as they are syntactically correct):

> 'hello' + ' ' + 'world'
'hello world'

Prompt based is allowed too using '>' as the first prompt
and '.' as the second prompt:

> function mul(a, b) {
.   return a * b;
. }

> mul(4, 2)
8

'''

from __future__ import unicode_literals
import re
from byexample.common import constant, abspath
from byexample.parser import ExampleParser
from byexample.finder import ExampleFinder, ZoneDelimiter
from byexample.runner import ExampleRunner, PexepctMixin, ShebangTemplate

stability = 'experimental'

class JavascriptCommentDelimiter(ZoneDelimiter):
    target = {'.js'}

    @constant
    def zone_regex(self):
        return re.compile(r'''
            # Begin with a /* marker
            ^[ ]*
             /\*

             # then, grab everything
             (?P<zone>.*?)

             # and the close marker
             \*/
            ''', re.DOTALL | re.MULTILINE | re.VERBOSE)

    @constant
    def leading_asterisk(self):
        return re.compile(r'^[ \*]+(?=[^ \*]|$)', re.MULTILINE)

    def get_zone(self, match, where):
        zone = ZoneDelimiter.get_zone(self, match, where)
        return self.leading_asterisk().sub(' ', zone)

class JavascriptPromptFinder(ExampleFinder):
    target = 'javascript-prompt'

    @constant
    def example_regex(self):
        return re.compile(r'''
            (?P<snippet>
                (?:^(?P<indent> [ ]*) (?:>)[ ]  .*)           # PS1 line
                (?:\n           [ ]*  \.[ ]             .*)*)    # PS2 lines
            \n?
            ## Want consists of any non-blank lines that do not start with PS1
            (?P<expected> (?:(?![ ]*$)        # Not a blank line
                          (?![ ]*(?:>))      # Not a line starting with PS1
                          .+$\n?              # But any other line
                      )*)
            ''', re.MULTILINE | re.VERBOSE)

    def get_language_of(self, *args, **kargs):
        return 'javascript'

    def get_snippet_and_expected(self, match, where):
        snippet, expected = ExampleFinder.get_snippet_and_expected(self, match, where)

        snippet = self._remove_prompts(snippet)
        return snippet, expected

    def _remove_prompts(self, snippet):
        lines = snippet.split("\n")
        return '\n'.join(line[2:] for line in lines)

class JavascriptParser(ExampleParser):
    language = 'javascript'

    @constant
    def example_options_string_regex(self):
        return re.compile(r'//\s*byexample:\s*([^\n\'"]*)$',
                                                    re.MULTILINE)

    def extend_option_parser(self, parser):
        pass

class JavascriptInterpreter(ExampleRunner, PexepctMixin):
    language = 'javascript'

    def __init__(self, verbosity, encoding, **unused):
        PexepctMixin.__init__(self,
                                PS1_re = r'node > ',
                                any_PS_re = r'(?:node > )|(?:\.\.\. )')

        self.encoding = encoding

    def run(self, example, options):
        return PexepctMixin._run(self, example, options)

    def _run_impl(self, example, options):
        return self._exec_and_wait(example.source, options)

    def interact(self, example, options):
        PexepctMixin.interact(self)

    def get_default_cmd(self, *args, **kargs):
        return  "%e %p %a", {
                    'e': '/usr/bin/env',
                    'p': 'nodejs',
                    'a': [abspath(__file__, 'byexample-repl.js')]
                    }

    def initialize(self, options):
        shebang, tokens = self.get_default_cmd()
        shebang = options['shebangs'].get(self.language, shebang)

        cmd = ShebangTemplate(shebang).quote_and_substitute(tokens)

        # run!
        self._spawn_interpreter(cmd, options)

        self._drop_output() # discard banner and things like that

    def shutdown(self):
        self._shutdown_interpreter()
