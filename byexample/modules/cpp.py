r"""
Example:
  ?: #include <iostream>

  ?: const char *hello = "hello bla world";
  ?: std::cout << hello << std::endl;           // byexample: +norm-ws
  hello   <...>   world

  ?: int i, j = 2;
  ?: for (i = 0; i < 4; ++i) {
  ::   j += i;
  :: }

  ?: j + 3
  (int) 11

  ?: std::cout << "this\n" \
  :: "is a multiline\n"    \
  :: "string\n";
  this
  is a multiline
  string

  ?: /* this
  :: is a multiline
  :: comment */

  ?: std::cout << "okay\n";
  okay

  These requires to use +pass because the output from the interpreter
  gets mixed with the string typed in.
  ?: int n;
  ?: std::cout << "num: " << std::flush; std::cin >> n;    // byexample: +type +pass
  num: [42]
  ?: n
  (int) 42

  TODO no newline is sent!
  ?: std::string what;
  ?: getline(std::cin, what);    // byexample: +type +pass
  [it works!]
  ?: what
  (std::string &) "it works!"
"""

from __future__ import unicode_literals
import sys, time
import byexample.regex as re
from byexample.common import constant
from byexample.parser import ExampleParser
from byexample.runner import ExampleRunner, PexpectMixin, ShebangTemplate
from byexample.finder import ExampleFinder

stability = 'experimental'


class CppPromptFinder(ExampleFinder):
    target = 'cpp-prompt'

    @constant
    def example_regex(self):
        return re.compile(
            r'''
            (?P<snippet>
                (?:^(?P<indent> [ ]*) (?:\?:)[ ]  .*)         # PS1 line
                (?:\n           [ ]*  ::             .*)*)    # PS2 lines
            \n?
            ## Want consists of any non-blank lines that do not start with PS1
            (?P<expected> (?:(?![ ]*$)        # Not a blank line
                          (?![ ]*(?:\?:))     # Not a line starting with PS1
                          .+$\n?              # But any other line
                      )*)
            ''', re.MULTILINE | re.VERBOSE
        )

    def get_language_of(self, *args, **kargs):
        return 'cpp'

    def get_snippet_and_expected(self, match, where):
        snippet, expected = ExampleFinder.get_snippet_and_expected(
            self, match, where
        )

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
        #   //  byexample:  +FOO -BAR +ZAZ=42
        return re.compile(r'//\s*byexample:\s*([^\n\'"]*)$', re.MULTILINE)


class CPPInterpreter(ExampleRunner, PexpectMixin):
    language = 'cpp'

    def __init__(self, verbosity, encoding, **unused):
        self.encoding = encoding

        PexpectMixin.__init__(
            self,
            PS1_re=r'\[cling\]\$',  # [cling]$
            any_PS_re=r'\[cling\][$!](?: \?)?'
        )  # [cling]!
        # [cling]$ ?

    def get_default_cmd(self, *args, **kargs):
        return "%e %p %a", {
            'e': "/usr/bin/env",
            'p': "cling",
            'a': [
                "--nologo",  # do not output the banner
            ]
        }

    def run(self, example, options):
        # the algorithm to filter the echos from the cling's output
        # (see _get_output()) doesn't work if the terminal is resized
        # so we disable this:
        options['geometry'] = self._terminal_default_geometry

        # cling's output requires to be emulated by an ANSI Terminal
        # so we force this (see _get_output())
        options['term'] = 'ansi'

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

        cmd = ShebangTemplate(shebang).quote_and_substitute(tokens)

        # setting the geometry here will also set
        # the _terminal_default_geometry variable for later
        options.up()
        options['geometry'] = (
            max(options['geometry'][0], 128), max(options['geometry'][1], 128)
        )
        self._spawn_interpreter(cmd, options)
        options.down()

    def _change_terminal_geometry(self, rows, cols, options):
        raise Exception("This should never happen")

    def shutdown(self):
        self._shutdown_interpreter()

    def _get_output(self, options):
        return self._get_output_echo_filtered(options)

    def cancel(self, example, options):
        return False  # not supported by cling
