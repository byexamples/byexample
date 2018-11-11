"""
Example:
  $ hello() {
  >     echo "hello bla world"
  > }

  $ hello
  hello<...>world

  ```shell
  for i in 0 1 2 3; do
      echo $i
  done

  out:
  0
  1
  2
  3
  ```
"""

import re, pexpect, sys, time
from byexample.common import constant
from byexample.parser import ExampleParser
from byexample.finder import ExampleFinder
from byexample.runner import ExampleRunner, PexepctMixin, ShebangTemplate
from byexample.executor import TimeoutException

stability = 'provisional'

class ShellPromptFinder(ExampleFinder):
    target = 'shell-prompt'

    @constant
    def example_regex(self):
        return re.compile(r'''
            (?P<snippet>
                (?:^(?P<indent> [ ]*) (?:\$)[ ]  .*)      # PS1 line
                (?:\n           [ ]*  >             .*)*)    # PS2 lines
            \n?
            ## Want consists of any non-blank lines that do not start with PS1
            (?P<expected> (?:(?![ ]*$)        # Not a blank line
                          (?![ ]*(?:\$))      # Not a line starting with PS1
                          .+$\n?              # But any other line
                      )*)
            ''', re.MULTILINE | re.VERBOSE)

    def get_language_of(self, *args, **kargs):
        return 'shell'

    def get_snippet_and_expected(self, match, where):
        snippet, expected = ExampleFinder.get_snippet_and_expected(self, match, where)

        snippet = self._remove_prompts(snippet)
        return snippet, expected

    def _remove_prompts(self, snippet):
        lines = snippet.split("\n")
        return '\n'.join(line[2:] for line in lines)

class ShellParser(ExampleParser):
    language = 'shell'

    @constant
    def example_options_string_regex(self):
        return re.compile(r'#\s*byexample:\s*([^\n\'"]*)$',
                                                    re.MULTILINE)

    def extend_option_parser(self, parser):
        parser.add_flag("stop-on-silence", help="stop the process after some period of inactivity or silence.")

class ShellInterpreter(ExampleRunner, PexepctMixin):
    language = 'shell'

    def __init__(self, verbosity, encoding, **unused):
        self.encoding = encoding

        PexepctMixin.__init__(self,
                                PS1_re = r"/byexample/sh/ps1> ",
                                any_PS_re = r"/byexample/sh/ps\d+> ")

    def get_default_cmd(self, *args, **kargs):
        return  "%e %p %a", {
                    'e': '/usr/bin/env',
                    'p': 'sh',
                    'a': [],
                    }

    def run(self, example, flags):
        try:
            return self._exec_and_wait(example.source,
                                    timeout=int(flags['timeout']))
        except TimeoutException as ex:
            if 'stop_on_silence' in flags and flags['stop_on_silence']:
                # get the current output
                out = ex.output

                # stop the process to get back the control of the shell.
                # this require that the job monitoring system of
                # the shell is on (set -m)
                self.interpreter.sendcontrol('z')

                # wait for the prompt, ignore any extra output
                self._expect_prompt(timeout=int(flags['timeout']),
                                        prompt_re=self.PS1_re)
                self._drop_output()
                return out
            raise

    def interact(self, example, options):
        PexepctMixin.interact(self)

    def initialize(self, options):
        shebang, tokens = self.get_default_cmd()
        shebang = options['shebangs'].get(self.language, shebang)

        cmd = ShebangTemplate(shebang).quote_and_substitute(tokens)
        self._spawn_interpreter(cmd, wait_first_prompt=False,
                                delaybeforesend=options['delaybeforesend'],
                                geometry=options['geometry'])

        self._exec_and_wait(
'''export PS1="/byexample/sh/ps1> "
export PS2="/byexample/sh/ps2> "
export PS3="/byexample/sh/ps3> "
export PS4="/byexample/sh/ps4> "
''', timeout=10)
        self._drop_output() # discard banner and things like that

    def shutdown(self):
        self._shutdown_interpreter()

