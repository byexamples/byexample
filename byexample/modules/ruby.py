"""
Example:
  Multi line expressions (like definitions)
  >> def hello
  ..     'hello bla world'
  .. end;

  Single line expressions
  >> hello               # byexample: +norm-ws
  => "hello   <...>   world"

  >> j = 2
  >> (0..3).each do |i|
  ..  j += i
  .. end

  >> j + 3
  => 11

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
  >> puts <<-FOO
  .. one
  .. two
  .. FOO
  one
  two

  >> print "num: "; gets     # byexample: +type  +skip
  num: [42]
  => "42\n"

  >> gets        # byexample: +type
  [it works!]
  => "it works!\n"
"""

from __future__ import unicode_literals
import pexpect, sys, time, subprocess
import byexample.regex as re
from byexample.common import constant
from byexample.log import clog
from byexample.parser import ExampleParser
from byexample.finder import ExampleFinder
from byexample.runner import ExampleRunner, PexpectMixin, ShebangTemplate

stability = 'provisional'


class RubyPromptFinder(ExampleFinder):
    target = 'ruby-prompt'

    @constant
    def example_regex(self):
        return re.compile(
            r'''
            # Snippet consists of one PS1 line >> and zero or more PS2 lines
            (?P<snippet>
                (?:^(?P<indent> [ ]*) >>[ ]   .*)    # PS1 line
                (?:\n           [ ]*  \.\.    .*)*)  # zero or more PS2 lines
            \n?
            # Want consists of any non-blank lines that do not start with PS1
            # The '=>' indicator is included (implicitly) and may not exist
            (?P<expected> (?:(?![ ]*$)            # Not a blank line
                             (?![ ]*   >>)        # Not a line starting with PS1
                             .+$\n?               # But any other line
                      )*)
            ''', re.MULTILINE | re.VERBOSE
        )

    def get_language_of(self, *args, **kargs):
        return 'ruby'

    def get_snippet_and_expected(self, match, where):
        snippet, expected = ExampleFinder.get_snippet_and_expected(
            self, match, where
        )

        snippet, expected = self._remove_prompts(snippet, expected)
        return snippet, expected

    def _remove_prompts(self, snippet, expected):
        lines = snippet.split("\n")
        n = lines[0].index(">> ")

        snippet = '\n'.join(line[n + 3:] for line in lines)
        expected = '\n'.join(line[n:] for line in expected.split('\n'))

        return snippet, expected


class RubyParser(ExampleParser):
    language = 'ruby'

    @constant
    def example_options_string_regex(self):
        return re.compile(r'#\s*byexample:\s*([^\n\'"]*)$', re.MULTILINE)

    def extend_option_parser(self, parser):
        parser.add_flag(
            "ruby-pretty-print",
            default=True,
            help="enable the pretty print enhancement."
        )
        parser.add_argument("+ruby-expr-print", choices=['auto', 'true', 'false'],
                            default='auto',
                            help='print the expression\'s value (true); ' +\
                                 'suppress it (false); or print it only ' +\
                                 'if the example has a => (auto, the default)')
        parser.add_flag(
            "ruby-start-large-output-in-new-line",
            default=False,
            help="add a newline after the => if the output that follows " +\
                 "does not fit in a single line. (irb >= 1.2.2)"
        )
        return parser


class RubyInterpreter(ExampleRunner, PexpectMixin):
    language = 'ruby'

    def __init__(self, verbosity, encoding, **unused):
        PexpectMixin.__init__(
            self,
            PS1_re=r'irb[^:]*:\d+:0(>|\*) ',
            any_PS_re=r'irb[^:]*:\d+:\d+(>|\*|") '
        )

        self.encoding = encoding

    def run(self, example, options):
        return PexpectMixin._run(self, example, options)

    def _run_impl(self, example, options):
        # turn on/off the echo mode base on the setting from the
        # start; per example setting is not supported
        src = example.source
        print_expr = False
        if self.expr_print_mode == 'auto':
            if self._detect_expression_print_expected(example):
                print_expr = True
                src = 'IRB.CurrentContext.echo = true; ' + src
            else:
                print_expr = False
                src = 'IRB.CurrentContext.echo = false; ' + src

        # there is no need to revert the echo=True if it was changed
        # because the execution of the next example will set it correctly
        return self._exec_and_wait(src, options, from_example=example)

    _EXPR_RESULT_RE = re.compile(r'^=>( |$)', re.MULTILINE | re.DOTALL)

    def _detect_expression_print_expected(self, example):
        # aka, check for a =>
        expected_str = example.expected.str
        return self._EXPR_RESULT_RE.search(expected_str) != None

    def interact(self, example, options):
        PexpectMixin.interact(self)

    def get_default_cmd(self, version, *args, **kargs):
        if version and version >= (1, 2, 0):
            args = ['-f', '--nomultiline', '--nocolorize', '--noreadline']
        else:
            args = ['--noreadline']

        return "%e %p %a", {'e': '/usr/bin/env', 'p': 'irb', 'a': args}

    def get_default_version_cmd(self, *args, **kargs):
        return "%e %p %a", {
            'e': '/usr/bin/env',
            'p': 'irb',
            'a': ['--version']
        }

    def build_cmd(self, options, default_shebang, default_tokens, joined=True):
        shebang, tokens = default_shebang, default_tokens
        shebang = options['shebangs'].get(self.language, shebang)

        return ShebangTemplate(shebang).quote_and_substitute(tokens, joined)

    @constant
    def version_regex(self):
        return re.compile(
            r'''
                ([^\d]|^)
                (?P<major>\d+)
                \.
                (?P<minor>\d+)
                (\. (?P<patch>\d+))?
                ([^\d]|$)
                ''', re.VERBOSE
        )

    @constant
    def get_version(self, options):
        cmd = self.build_cmd(
            options, *self.get_default_version_cmd(), joined=False
        )
        try:
            out = subprocess.check_output(cmd).decode(self.encoding)
            m = self.version_regex().search(out)

            version = (
                int(m.group(k) or 0) for k in ("major", "minor", "patch")
            )
            version = tuple(version)

        except Exception as err:
            clog().info(
                "Could not detect interpreter version: %s\nExecuted command: %s",
                str(err), cmd
            )
            return None

        return version

    def initialize(self, options):
        ruby_pretty_print = options['ruby_pretty_print']

        # always/yes; never/no; autodetect normalization
        self.expr_print_mode = options['ruby_expr_print']

        newline_before_multiline_output = options[
            'ruby_start_large_output_in_new_line']

        version = self.get_version(options)
        cmd = self.build_cmd(options, *self.get_default_cmd(version))

        dfl_timeout = options['x']['dfl_timeout']

        # run!
        self._spawn_interpreter(cmd, options, wait_first_prompt=False)

        # In RVM contexts the IRB's prompt mode is changed even
        # if we force the mode from the command line (whe we spawn IRB)
        # Make sure that the first thing executed restores the default prompt.
        #
        # Also, set if IRB should print or not a newline between the => marker
        # and the output if it is larger than a single line
        nl = "true" if newline_before_multiline_output else "false"
        self._exec_and_wait(
            'IRB.CurrentContext.prompt_mode = :DEFAULT\n' +
            'IRB.CurrentContext.newline_before_multiline_output = %s\n' % nl,
            options,
            timeout=dfl_timeout
        )
        self._drop_output()

        # set the pretty print inspector
        if ruby_pretty_print:
            self._exec_and_wait(_pp_code, options, timeout=dfl_timeout)

        # disable the echo if we don't want it (false) or we may want it
        # but it will depend on the example (auto)
        if self.expr_print_mode in ('auto', 'false'):
            self._exec_and_wait(
                'IRB.CurrentContext.echo = false\n',
                options,
                timeout=dfl_timeout
            )
        else:
            self._exec_and_wait(
                'IRB.CurrentContext.echo = true\n',
                options,
                timeout=dfl_timeout
            )

    def shutdown(self):
        self._shutdown_interpreter()

    def cancel(self, example, options):
        return self._abort(example, options)


'''
The following code is followed by several tabs (do not delete them).
In 7.4.3 and before, this tabs were interpreted by IRB and triggered
the 'autocomplete' suggestions, printing a lot of stuff to the terminal.
Now this should not happen anymore so the following code should print
nothing.
>> a = "hello"				

'''

_pp_code = '''
require "pp"

class PP
  module PPMethods
    alias_method :_original_pp_hash, :pp_hash

    def pp_hash(obj)
      obj = Hash[obj.sort]
      _original_pp_hash(obj)
    end
  end
end

IRB.CurrentContext.inspect_mode = :pp
'''
