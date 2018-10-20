"""
Example:
  ```cpp
  #include <iostream>

  const char *hello = "hello bla world";
  std::cout << hello << std::endl;

  out:
  hello<...>world
  ```

  ```cpp
  int i, j = 2;

  for (i = 0; i < 4; ++i) {
     j += i;
  }

  j + 3

  out:
  (int) 11
  ```

"""

import re, sys, time
from byexample.common import constant
from byexample.parser import ExampleParser
from byexample.runner import ExampleRunner, PexepctMixin, ShebangTemplate

stability = 'experimental'

class CPPParser(ExampleParser):
    language = 'cpp'

    @constant
    def example_options_string_regex(self):
        # anything of the form:
        #   /*  byexample:  +FOO -BAR +ZAZ=42  */
        # or:
        #   //  byexample:  +FOO -BAR +ZAZ=42
        return re.compile(r'''(?:                       # /* comment style */
                                   /*  \s*  byexample: \s* ([^\n\'"]*)  */ \s*$
                               ) |
                              (?:                       # // comment style
                                   //  \s*  byexample: \s* ([^\n\'"]*)  $
                               )''',
                                                    re.MULTILINE|re.VERBOSE)


class CPPInterpreter(ExampleRunner, PexepctMixin):
    language = 'cpp'

    def __init__(self, verbosity, encoding, **unused):
        self.encoding = encoding

        PexepctMixin.__init__(self,
                                PS1_re =    r'\[cling\]\$',           # [cling]$
                                any_PS_re = r'\[cling\][$!](?: \?)?') # [cling]!
                                                                      # [cling]$ ?

    def get_default_cmd(self, *args, **kargs):
        return  "%e %p %a", {
                    'e': "/usr/bin/env",
                    'p': "cling",
                    'a': [
                            "--nologo", # do not output the banner
                        ]
                    }

    def run(self, example, flags):
        return self._exec_and_wait(example.source,
                                    int(flags['timeout']))

    def interact(self, example, options):
        PexepctMixin.interact(self)

    def initialize(self, options):
        shebang, tokens = self.get_default_cmd()
        shebang = options['shebangs'].get(self.language, shebang)

        cmd = ShebangTemplate(shebang).quote_and_substitute(tokens)

        self._spawn_interpreter(cmd, delaybeforesend=options['delaybeforesend'],
                                     geometry=options['geometry'])


    def shutdown(self):
        self._shutdown_interpreter()


    def _get_output(self, emulate_terminal=True):
        # cling doesn't disable the TTY's echo so everything we type in
        # it will be reflected in the output.
        # so this breaks badly self._get_output

        # self.last_output is a list of strings found by pexpect
        # after returning of each pexpect.expect
        # in other words if we prefix each line with the prompt
        # should get the original output from the process
        lines = ('[cling]$ ' + line for line in self.last_output)
        self._drop_output()

        # now, feed those lines to our ANSI Terminal emulator
        lines = self._emulate_terminal(lines)

        # get each line in the Terminal's display and ignore each one that
        # belong with our prompt: those are the "echo" lines that
        # *we* sent to the cling and they are not part of *its* output.
        lines = (line for line in lines
                               if not line.startswith('[cling]$'))

        return '\n'.join(lines)
