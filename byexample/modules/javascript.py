r"""
Example:
  > function hello() {
  .     console.log("hello bla world")
  . }

  > hello()               // byexample: +norm-ws
  hello   <...>   world

  > var j = 2;
  > for (var i = 0; i < 4; ++i) {
  .    j += i;
  . };
  8

  > j + 3
  11

  > console.log("this\n\
  . is a multiline\n\
  . string");
  this
  is a multiline
  string

  > /* this
  . is a multiline
  . comment */

  > 42
  42

  These requires to use +pass because the output from the interpreter
  gets mixed with the string typed in.
  *However* they never worked.
  > const readline = require('readline');
  > const rl = readline.createInterface({
  .   input: process.stdin,
  .   terminal: false
  . });

  > var num;
  > rl.question('num: ', (n) => {             // byexample: +input +pass +skip
  .   num = n;
  . });
  num: [42]

  > num // byexample: +skip
  42
"""

from __future__ import unicode_literals
import byexample.regex as re
from byexample.common import constant, abspath
from byexample.parser import ExampleParser
from byexample.finder import ExampleFinder
from byexample.runner import ExampleRunner, PexpectMixin, ShebangTemplate

stability = 'experimental'


class JavascriptPromptFinder(ExampleFinder):
    target = 'javascript-prompt'

    @constant
    def example_regex(self):
        return re.compile(
            r'''
            (?P<snippet>
                (?:^(?P<indent> [ ]*) (?:>)[ ]  .*)           # PS1 line
                (?:\n           [ ]*  \.[ ]             .*)*)    # PS2 lines
            \n?
            ## Want consists of any non-blank lines that do not start with PS1
            (?P<expected> (?:(?![ ]*$)        # Not a blank line
                          (?![ ]*(?:>))      # Not a line starting with PS1
                          .+$\n?              # But any other line
                      )*)
            ''', re.MULTILINE | re.VERBOSE
        )

    def get_language_of(self, *args, **kargs):
        return 'javascript'

    def get_snippet_and_expected(self, match, where):
        snippet, expected = ExampleFinder.get_snippet_and_expected(
            self, match, where
        )

        snippet = self._remove_prompts(snippet)
        return snippet, expected

    def _remove_prompts(self, snippet):
        lines = snippet.split("\n")
        return '\n'.join(line[2:] for line in lines)


class JavascriptParser(ExampleParser):
    language = 'javascript'

    @constant
    def example_options_string_regex(self):
        return re.compile(r'//\s*byexample:\s*([^\n\'"]*)$', re.MULTILINE)

    def extend_option_parser(self, parser):
        pass


class JavascriptInterpreter(ExampleRunner, PexpectMixin):
    language = 'javascript'

    def __init__(self, verbosity, encoding, **unused):
        PexpectMixin.__init__(
            self, PS1_re=r'node > ', any_PS_re=r'(?:node > )|(?:\.\.\. )'
        )

        self.encoding = encoding

    def run(self, example, options):
        return PexpectMixin._run(self, example, options)

    def _run_impl(self, example, options):
        return self._exec_and_wait(
            example.source, options, from_example=example
        )

    def interact(self, example, options):
        PexpectMixin.interact(self)

    def get_default_cmd(self, *args, **kargs):
        return "%e %p %a", {
            'e': '/usr/bin/env',
            'p': 'nodejs',
            'a': [abspath(__file__, 'gadgets', 'byexample-repl.js')]
        }

    def initialize(self, options):
        shebang, tokens = self.get_default_cmd()
        shebang = options['shebangs'].get(self.language, shebang)

        cmd = ShebangTemplate(shebang).quote_and_substitute(tokens)

        # run!
        self._spawn_interpreter(cmd, options)

        self._drop_output()  # discard banner and things like that

    def shutdown(self):
        self._shutdown_interpreter()

    def cancel(self, example, options):
        return False  # not supported by nodejs
