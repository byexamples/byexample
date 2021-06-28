r"""
Example:

  PS> 1 + 2
  3

  PS> $ComputerName = 'DC01', 'WEB01'
  PS> foreach ($Computer in $ComputerName) {
  -->    echo $Computer
  --> }
  DC01
  WEB01

  PS> echo @"this
  ParserError:
  Line |
     1 |  echo @"this
       |         ~
       | No characters are allowed after a here-string header but
       | before the end of the line.

  PS> echo @"
  --> this
  --> is a multiline
  --> string
  --> "@
  this
  is a multiline
  string

  PS> echo "foo         bar"    # byexample: +norm-ws
  foo bar

  These requires to use +pass because the output from the interpreter
  gets mixed with the string typed in.
  PS> $num = Read-Host num    # byexample: +input +pass
  num: [42]
  PS> echo $num
  42

  PS> $what = Read-Host    # byexample: +input +pass
  [it works!]
  PS> echo $what
  it works!
'''

"""

from __future__ import unicode_literals
import sys, time
import byexample.regex as re
from byexample.log import clog
from byexample.common import constant
from byexample.parser import ExampleParser
from byexample.runner import ExampleRunner, PexpectMixin, ShebangTemplate
from byexample.finder import ExampleFinder

stability = 'experimental'


class PowerShellPromptFinder(ExampleFinder):
    target = 'pwsh-prompt'

    @constant
    def example_regex(self):
        return re.compile(
            r'''
            (?P<snippet>
                (?:^(?P<indent> [ ]*) (?:PS>)[ ]  .*)         # PS1 line
                (?:\n           [ ]*  -->             .*)*)    # PS2 lines
            \n?
            ## Want consists of any non-blank lines that do not start with PS1
            (?P<expected> (?:(?![ ]*$)        # Not a blank line
                          (?![ ]*(?:PS>))     # Not a line starting with PS1
                          .+$\n?              # But any other line
                      )*)
            ''', re.MULTILINE | re.VERBOSE
        )

    def get_language_of(self, *args, **kargs):
        return 'pwsh'

    def get_snippet_and_expected(self, match, where):
        snippet, expected = ExampleFinder.get_snippet_and_expected(
            self, match, where
        )

        snippet = self._remove_prompts(snippet)
        return snippet, expected

    def _remove_prompts(self, snippet):
        lines = snippet.split("\n")
        return '\n'.join(line[4:] for line in lines)


class PowerShellParser(ExampleParser):
    language = 'pwsh'

    @constant
    def example_options_string_regex(self):
        # anything of the form:
        #   # byexample:  +FOO -BAR +ZAZ=42
        return re.compile(r'#\s*byexample:\s*([^\n\'"]*)$', re.MULTILINE)

    def process_snippet_and_expected(self, snippet, expected):
        snippet, expected = ExampleParser.process_snippet_and_expected(
            self, snippet, expected
        )

        # Don't allow to pass any trailing newline that could confuse
        # PowerShell and/or Byexample
        snippet = snippet.rstrip('\n')

        # Multiline examples always require and extra line to be injected
        # We are assuming that the example will make PowerShell to prompt
        # the secondary prompt and this one is closed only after a new empty
        # line (similar to what Python requires to close a func definition)
        if len(snippet.split('\n')) > 1:
            snippet += '\n'

        return snippet, expected


class PowerShellInterpreter(ExampleRunner, PexpectMixin):
    language = 'pwsh'

    def __init__(self, verbosity, encoding, **unused):
        self.encoding = encoding

        PexpectMixin.__init__(
            self, PS1_re=r'byexample-ps1>', any_PS_re=r'(byexample-ps1>)|(>>)'
        )

    def get_default_cmd(self, *args, **kargs):
        return "%e %p %a", {
            'e':
            "/usr/bin/env",
            'p':
            "pwsh",
            'a': [
                '-NoLogo',
                '-NoProfile',
                '-NoExit',
                '-Command',
                "function prompt { \"byexample-ps1>byexample-ps1-mark\" }",
            ]
        }

    def run(self, example, options):
        options['geometry'] = self._terminal_default_geometry
        options['term'] = 'ansi'

        if options['type'] and not options['pass']:
            clog().warn(
                "Typing is supported but the example's output will be unpredictable: add +pass to skip its check."
            )
        return PexpectMixin._run(self, example, options)

    def _run_impl(self, example, options):
        return self._exec_and_wait(
            example.source, options, from_example=example
        )

    def interact(self, example, options):
        PexpectMixin.interact(self)

    def initialize(self, options):
        shebang, tokens = self.get_default_cmd()
        shebang = options['shebangs'].get(self.language, shebang)

        # documented by PowerShell but completely ignored
        # https://no-color.org/
        # https://docs.microsoft.com/en-us/powershell/scripting/learn/experimental-features?view=powershell-7.1
        env_update = {'NO_COLOR': '1'}
        cmd = ShebangTemplate(shebang).quote_and_substitute(tokens)
        self._spawn_interpreter(
            cmd, options, subprocess=True, env_update=env_update
        )

    def shutdown(self):
        self._shutdown_interpreter()

    def _get_output(self, options):
        # Insert a cookie marker where the prompts were
        # except at the end
        #
        # For example, this was the original _output_between_prompts:
        #   ['foo 1\nA1\nA2\n', 'B1\n']  (two chunks)
        # We will have:
        #   ['foo 1\nA1\nA2\n', cookie, 'B1\n']  (three chunks)
        cookie = '[byexamplecookie]$'
        chunks = []
        before = len(self._output_between_prompts)
        for c in self._output_between_prompts:
            chunks.append(c)
            chunks.append(cookie)
        del chunks[-1]

        # Get the raw output obtained joining the chunks
        # of _output_between_prompts (which are *not* necessary
        # complete lines)
        #
        # We should get:
        #   'foo 1\nA1\nA2\ncookieB1\n'
        #
        raw_output = self._emulate_as_is_terminal(chunks)

        # ANSI Terminal emulator (pyte) requires \r to trigger
        # a carriage-return (\n are not enough)
        # This is required because _emulate_as_is_terminal replaced
        # all the newlines (\r, \r\n) by \n
        if options['term'] == 'ansi':
            raw_output = raw_output.replace('\n', '\r\n')

        # Get the lines read preserving the \n at the end of them.
        #
        # We should get:
        #   ['foo 1\n', 'A1\n', 'A2\n', 'cookieB1\n']  (four lines)
        lines = raw_output.splitlines(keepends=True)

        # PowerShell echoes back each line that we sent to it so we
        # count them and we remove them from the output obtained
        # before continuing with the _get_output() pipeline
        #
        # Assuming last_num_lines_sent == 1  we should get:
        #   ['A1\n', 'A2\n', 'cookieB1\n']  (three lines)
        lines = lines[self.last_num_lines_sent:]

        # Now we reconstruct the _output_between_prompts joining
        # the lines and splitting them by cookie
        #
        # We should get:
        #   ['A1\nA2\n', 'B1\n']  (two chunks)
        self._output_between_prompts = ''.join(lines).split(cookie)
        assert len(self._output_between_prompts) <= before

        # Let the rest of the _get_output() pipeline proceed
        return super()._get_output(options)

    def cancel(self, example, options):
        return False
