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
from byexample.parser import ExampleParser
from byexample.finder import MatchFinder
from byexample.interpreter import Interpreter, PexepctMixin

class ShellPromptFinder(MatchFinder):
    target = 'shell-prompt'

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

class ShellParser(ExampleParser):
    language = 'shell'

    def example_options_string_regex(self):
        return re.compile(r'#\s*byexample:\s*([^\n\'"]*)$',
                                                    re.MULTILINE)


    def source_from_snippet(self, snippet):
        lines = snippet.split("\n")
        if lines and lines[0].startswith("$ "):
            return '\n'.join(line[2:] for line in lines)

        return snippet

class ShellInterpreter(Interpreter, PexepctMixin):
    language = 'shell'

    def __init__(self, verbosity, encoding, **unused):
        self.encoding = encoding

        PexepctMixin.__init__(self,
                                cmd='/usr/bin/env sh',
                                PS1_re = r"/byexample/sh/ps1> ",
                                any_PS_re = r"/byexample/sh/ps\d+> ")

    def _spawn_new_shell(self, cmd):
        self._exec_and_wait('export PS1\n' +\
                            'export PS2\n' +\
                            'export PS3\n' +\
                            'export PS4\n' +\
                            cmd + '\n', timeout=2)


    def run(self, example, flags):
        if flags.get('bash', False):
            self._spawn_new_shell('/usr/bin/env bash --norc -i')
        elif flags.get('sh', False):
            self._spawn_new_shell('/usr/bin/env sh')

        return self._exec_and_wait(example.source,
                                    timeout=int(flags['TIMEOUT']))

    def interact(self, example, options):
        PexepctMixin.interact(self)

    def initialize(self, examples, options):
        self._spawn_interpreter(wait_first_prompt=False)

        self._exec_and_wait(
'''export PS1="/byexample/sh/ps1> "
export PS2="/byexample/sh/ps2> "
export PS3="/byexample/sh/ps3> "
export PS4="/byexample/sh/ps4> "
''', timeout=10)
        self._drop_output() # discard banner and things like that

    def shutdown(self):
        self._shutdown_interpreter()

