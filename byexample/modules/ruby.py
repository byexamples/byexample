"""
Example:
  Multi line expressions (like definitions)
  >> def hello
  ..     'hello bla world'
  .. end;

  Single line expressions
  >> hello
  => "hello<...>world"

  Markdown's version (no prompt)
  ```ruby
  j = 2;
  (0..3).each do |i|
    j += i;
  end;

  j + 3

  out:
  => 11
  ```

  Pretty print
  >> { 1 => 2, 3=>{4=>"aaaaaaaa", 5=>Array(0..20)}}
  => {1=>2,
   3=>
    {4=>"aaaaaaaa",
     5=>
      [0,
       1,
       <...>
       19,
       20]}}

  Autodetect print expression:
  >> "foo bar 1"
  => "foo bar 1"

  >> "foo bar 2"

  >> "foo bar 3"
  => "foo bar 3"

  >> "foo bar 4"    # byexample: +norm-ws
  =>
  "foo bar 4"

  Heredocs
  ```ruby
  puts <<-FOO
  one
  two
  FOO

  out:
  one
  two
  ```

"""

import re, pexpect, sys, time
from byexample.common import constant
from byexample.parser import ExampleParser
from byexample.finder import ExampleFinder
from byexample.runner import ExampleRunner, PexepctMixin, ShebangTemplate

stability = 'experimental'

class RubyPromptFinder(ExampleFinder):
    target = 'ruby-prompt'

    @constant
    def example_regex(self):
        return re.compile(r'''
            # Snippet consists of one PS1 line >> and zero or more PS2 lines
            (?P<snippet>
                (?:^(?P<indent> [ ]*) >>[ ]     .*)    # PS1 line
                (?:\n           [ ]*  \.\.    .*)*)    # zero or more PS2 lines
            \n?
            # Want consists of any non-blank lines that do not start with PS1
            # The '=>' indicator is included (implicitly) and may not exist
            (?P<expected> (?:(?![ ]*$)     # Not a blank line
                          (?![ ]*>>)       # Not a line starting with PS1
                         .+$\n?            # But any other line
                      )*)
            ''', re.MULTILINE | re.VERBOSE)

    def get_language_of(self, *args, **kargs):
        return 'ruby'

    def get_snippet_and_expected(self, match, where):
        snippet, expected = ExampleFinder.get_snippet_and_expected(self, match, where)

        snippet = self._remove_prompts(snippet)
        return snippet, expected

    def _remove_prompts(self, snippet):
        lines = snippet.split("\n")
        return '\n'.join(line[3:] for line in lines)

class RubyParser(ExampleParser):
    language = 'ruby'

    @constant
    def example_options_string_regex(self):
        return re.compile(r'#\s*byexample:\s*([^\n\'"]*)$',
                                                    re.MULTILINE)

    def extend_option_parser(self, parser):
        parser.add_flag("ruby-pretty-print", help="enable the pretty print enhancement.")
        parser.add_argument("+ruby-expr-print", choices=['auto', 'true', 'false'],
                            default='auto',
                            help='print the expression\'s value (true); ' +\
                                 'suppress it (false); or print it only ' +\
                                 'if the example has a => (auto, the default)')
        return parser

class RubyInterpreter(ExampleRunner, PexepctMixin):
    language = 'ruby'

    def __init__(self, verbosity, encoding, **unused):
        PexepctMixin.__init__(self,
                                PS1_re = r'irb[^:]*:\d+:0(>|\*) ',
                                any_PS_re = r'irb[^:]*:\d+:\d+(>|\*|") ')

        self.encoding = encoding

    def run(self, example, flags):

        # turn on/off the echo mode base on the setting from the
        # start; per example setting is not supported
        src = example.source
        print_expr = False
        if self.expr_print_mode == 'auto':
            if self._detect_expression_print_expected(example):
                print_expr = True
                src = 'IRB.CurrentContext.echo = true;\n' + src
            else:
                print_expr = False
                src = 'IRB.CurrentContext.echo = false;\n' + src

        # there is no need to revert the echo=True if it was changed
        # because the execution of the next example will set it correctly
        return self._exec_and_wait(src, timeout=int(flags['timeout']))

    _EXPR_RESULT_RE = re.compile(r'^=>( |$)', re.MULTILINE | re.DOTALL)

    def _detect_expression_print_expected(self, example):
        # aka, check for a =>
        expected_str = example.expected.str
        return self._EXPR_RESULT_RE.search(expected_str) != None

    def interact(self, example, options):
        PexepctMixin.interact(self)

    def get_default_cmd(self, *args, **kargs):
        return  "%e %p %a", {
                    'e': '/usr/bin/env',
                    'p': 'irb',
                    'a': []
                    }

    def initialize(self, options):
        ruby_pretty_print = options.get('ruby_pretty_print', True)

        # always/yes; never/no; autoetect normalization
        self.expr_print_mode = options['ruby_expr_print']

        shebang, tokens = self.get_default_cmd()
        shebang = options['shebangs'].get(self.language, shebang)

        cmd = ShebangTemplate(shebang).quote_and_substitute(tokens)

        # run!
        self._spawn_interpreter(cmd, delaybeforesend=options['delaybeforesend'])

        # set the pretty print inspector
        if ruby_pretty_print:
            self._exec_and_wait('IRB.CurrentContext.inspect_mode = :pp\n',
                                    timeout=2)

        # disable the echo if we don't want it (false) or we may want it
        # but it will depend on the example (auto)
        if self.expr_print_mode in ('auto', 'false'):
            self._exec_and_wait('IRB.CurrentContext.echo = false\n', timeout=2)
        else:
            self._exec_and_wait('IRB.CurrentContext.echo = true\n', timeout=2)

    def shutdown(self):
        self._shutdown_interpreter()
