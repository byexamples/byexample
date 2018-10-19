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

import re, sys, time, pyte
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

        self._screen = pyte.Screen(*reversed(options['geometry']))
        self._stream = pyte.Stream(self._screen)


    def shutdown(self):
        self._shutdown_interpreter()


    def _get_output(self):
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
        for line in lines:
            self._stream.feed(line)

        # get each line in the Terminal's display and ignore each one that
        # belong with our prompt: those are the "echo" lines that
        # *we* sent to the cling and they are not part of *its* output.
        lines = (line.rstrip() for line in self._screen.display
                               if not line.startswith('[cling]$ '))

        # clean up the screen to not interfer with the rest of the
        # examples.
        self._screen.reset()
        return '\n'.join(lines)
