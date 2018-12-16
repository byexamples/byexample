"""
Example:
  ?: #include <iostream>

  ?: const char *hello = "hello bla world";
  ?: std::cout << hello << std::endl;
  hello<...>world

  ?: int i, j = 2;
  ?: for (i = 0; i < 4; ++i) {
  ::   j += i;
  :: }

  ?: j + 3
  (int) 11

"""

from __future__ import unicode_literals
import re, sys, time
from byexample.common import constant
from byexample.parser import ExampleParser
from byexample.runner import ExampleRunner, PexepctMixin, ShebangTemplate
from byexample.finder import ExampleFinder, ZoneDelimiter

stability = 'experimental'

class CppCommentDelimiter(ZoneDelimiter):
    target = {'.cpp', '.c', '.h', '.hpp'}

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

class CppPromptFinder(ExampleFinder):
    target = 'cpp-prompt'

    @constant
    def example_regex(self):
        return re.compile(r'''
            (?P<snippet>
                (?:^(?P<indent> [ ]*) (?:\?:)[ ]  .*)         # PS1 line
                (?:\n           [ ]*  ::             .*)*)    # PS2 lines
            \n?
            ## Want consists of any non-blank lines that do not start with PS1
            (?P<expected> (?:(?![ ]*$)        # Not a blank line
                          (?![ ]*(?:\?:))     # Not a line starting with PS1
                          .+$\n?              # But any other line
                      )*)
            ''', re.MULTILINE | re.VERBOSE)

    def get_language_of(self, *args, **kargs):
        return 'cpp'

    def get_snippet_and_expected(self, match, where):
        snippet, expected = ExampleFinder.get_snippet_and_expected(self, match, where)

        snippet = self._remove_prompts(snippet)
        return snippet, expected

    def _remove_prompts(self, snippet):
        lines = snippet.split("\n")
        return '\n'.join(line[3:] for line in lines)

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

    def run(self, example, options):
        # the algorithm to filter the echos from the cling's output
        # (see _get_output()) doesn't work if the terminal is resized
        # so we disable this:
        options['geometry'] = self._terminal_default_geometry

        # cling's output requeries to be emulated by an ANSI Terminal
        # so we force this (see _get_output())
        options['term'] = 'ansi'

        return PexepctMixin._run(self, example, options)

    def _run_impl(self, example, options):
        return self._exec_and_wait(example.source, options)

    def interact(self, example, options):
        PexepctMixin.interact(self)

    def initialize(self, options):
        shebang, tokens = self.get_default_cmd()
        shebang = options['shebangs'].get(self.language, shebang)

        cmd = ShebangTemplate(shebang).quote_and_substitute(tokens)

        options.up()
        options['geometry'] = (max(options['geometry'][0], 128), options['geometry'][1])
        self._spawn_interpreter(cmd, options)
        options.down()


    def _change_terminal_geometry(self, rows, cols, options):
        raise Exception("This should never happen")

    def shutdown(self):
        self._shutdown_interpreter()

    def _get_output(self, options):
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
        lines = self._emulate_ansi_terminal(lines, join=False)

        # get each line in the Terminal's display and ignore each one that
        # belong with our prompt: those are the "echo" lines that
        # *we* sent to the cling and they are not part of *its* output.
        lines = (line for line in lines
                               if not line.startswith('[cling]$'))

        return '\n'.join(lines)
