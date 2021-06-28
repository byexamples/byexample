"""
Example:
  php> function hello() {
  ...>     echo "hello bla world";
  ...> }

  php> hello();               // byexample: +norm-ws
  hello   <...>   world

  php> $j = 2;
  php> for ($i = 0; $i < 4; $i += 1) {
  ...>    $j += $i;
  ...> }

  php> var_dump($j);
  int(8)

  php> echo $j + 3;
  11

  php> $a = "this
  ...> is a multiline
  ...> string";

  php> echo $a;
  this
  is a multiline
  string

  php> /* this
  ...> is a multiline
  ...> comment */

  php> echo "okay";
  okay

  These requires to use +pass because the output from the interpreter
  gets mixed with the string typed in.
  *However* they never worked.
  php> $f = fopen('php://stdin', 'r');
  php> echo "num: "; $num = fgets($f);      // byexample: +input +pass
  num: [42]
  php> echo "$num";
  42

  php> $what = fgets($f);      // byexample: +input +pass
  [it works!]
  php> echo "$what";
  it works!

"""

from __future__ import unicode_literals
import byexample.regex as re
from byexample.common import constant
from byexample.parser import ExampleParser
from byexample.finder import ExampleFinder
from byexample.runner import ExampleRunner, PexpectMixin, ShebangTemplate

stability = 'experimental'


class PHPPromptFinder(ExampleFinder):
    target = 'php-prompt'

    @constant
    def example_regex(self):
        return re.compile(
            r'''
            (?P<snippet>
                (?:^(?P<indent> [ ]*) (?:php>)[ ]      .*)      # PS1 line
                (?:\n           [ ]*  \.\.\.>[ ]       .*)*)    # PS2 lines
            \n?
            ## Want consists of any non-blank lines that do not start with PS1
            (?P<expected> (?:(?![ ]*$)        # Not a blank line
                          (?![ ]*(?:php>))    # Not a line starting with PS1
                          .+$\n?              # But any other line
                      )*)
            ''', re.MULTILINE | re.VERBOSE
        )

    def get_language_of(self, *args, **kargs):
        return 'php'

    def get_snippet_and_expected(self, match, where):
        snippet, expected = ExampleFinder.get_snippet_and_expected(
            self, match, where
        )

        snippet = self._remove_prompts(snippet)
        return snippet, expected

    def _remove_prompts(self, snippet):
        lines = snippet.split("\n")
        return '\n'.join(line[5:] for line in lines)


class PHPParser(ExampleParser):
    language = 'php'

    @constant
    def example_options_string_regex(self):
        return re.compile(r'//\s*byexample:\s*([^\n\'"]*)$', re.MULTILINE)

    def extend_option_parser(self, parser):
        pass


class PHPInterpreter(ExampleRunner, PexpectMixin):
    language = 'php'

    def __init__(self, verbosity, encoding, **unused):
        PexpectMixin.__init__(
            self,
            # the format is '/byexample/php/ blk chr >'
            # where blk indicates in which block we are
            # and chr indicates in which unterminated block
            # we are
            PS1_re=r'/byexample/php/\s+php\s+>\s+> ',
            any_PS_re=r'/byexample/php/\s+[^ ]+\s+[^ ]+\s+> '
        )

        self.encoding = encoding

    def run(self, example, options):
        # the algorithm to filter the echos from the php's output
        # (see _get_output()) doesn't work if the terminal is resized
        # so we disable this:
        options['geometry'] = self._terminal_default_geometry

        # php's output requeries to be emulated by an ANSI Terminal
        # so we force this (see _get_output())
        options['term'] = 'ansi'

        return PexpectMixin._run(self, example, options)

    def _run_impl(self, example, options):
        return self._exec_and_wait(
            example.source, options, from_example=example
        )

    def interact(self, example, options):
        PexpectMixin.interact(self)

    def get_default_cmd(self, *args, **kargs):
        return "%e %p %a", {'e': '/usr/bin/env', 'p': 'php', 'a': ['-a']}

    def _get_output(self, options):
        return self._get_output_echo_filtered(options)

    def initialize(self, options):
        shebang, tokens = self.get_default_cmd()
        shebang = options['shebangs'].get(self.language, shebang)

        cmd = ShebangTemplate(shebang).quote_and_substitute(tokens)

        # run!
        options.up()
        options['geometry'] = (
            max(options['geometry'][0], 128), max(options['geometry'][1], 128)
        )
        self._spawn_interpreter(cmd, options, initial_prompt=r'php >')
        options.down()

        self._drop_output()  # discard banner and things like that

        # change the prompts
        # the \b indicates which block PHP is in (/* for comments, php
        # for normal php mode)
        # and the \> indicates if we are inside an unterminated block or string.
        prompt = r'/byexample/php/ \b \> > '
        self._exec_and_wait(r'#cli.prompt=%s' % prompt, options)
        self._drop_output()

    def _change_terminal_geometry(self, rows, cols, options):
        raise Exception("This should never happen")

    def shutdown(self):
        self._shutdown_interpreter()

    def cancel(self, example, options):
        return False  # not supported by php
