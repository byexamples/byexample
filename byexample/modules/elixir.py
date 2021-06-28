"""
Example:
  Multi line expressions (like definitions)
  iex> defmodule Baz do
  ...>   def hello(w) do
  ...>      "hello      " <> w
  ...>   end
  ...> end

  Single line expressions
  iex> Baz.hello("world")               # byexample: +norm-ws
  => "hello <...> world"

  iex> j = 2
  iex> j = (if j < 4 do 8 end)

  iex> j + 3
  => 11

  Pretty print
  iex> %{:a => 1, 2 => :b, 3 => %{:c => 0, :d => %{:x => 0, :y => :e}}}
  =>
  %{
    2 => :b,
    3 => %{
      c: 0,
      d: %{x: 0, y: :e}
    },
    :a => 1
  }

  Autodetect print expression:
  iex> "foo bar 1"
  => "foo bar 1"

  iex> _ = "foo bar 2"

  iex> "foo bar 3"
  => "foo bar 3"

  iex> "foo bar 4"    # byexample: +norm-ws
  => "foo
  bar
  4"

  iex> IO.puts("hello world")
  hello world

  These requires to use +pass because the output from the interpreter
  gets mixed with the string typed in.
  *However* they never worked.
  iex> num = IO.gets("num: ")         # byexample: +input +pass
  num: [42]
  iex> num
  "42\n"


"""

from __future__ import unicode_literals
import pexpect, sys, time
import byexample.regex as re
from byexample.common import constant
from byexample.parser import ExampleParser
from byexample.finder import ExampleFinder
from byexample.runner import ExampleRunner, PexpectMixin, ShebangTemplate
from byexample.executor import TimeoutException

stability = 'experimental'


class ElixirPromptFinder(ExampleFinder):
    target = 'elixir-prompt'

    @constant
    def example_regex(self):
        return re.compile(
            r'''
            # Snippet consists of one PS1 line iex> and zero or more PS2 lines
            (?P<snippet>
                (?:^(?P<indent> [ ]*) iex>[ ]       .*)    # PS1 line
                (?:\n           [ ]*  \.\.\.>     .*)*)  # zero or more PS2 lines
            \n?
            # Want consists of any non-blank lines that do not start with PS1
            # The '=>' indicator is included (implicitly) and may not exist
            (?P<expected> (?:(?![ ]*$)            # Not a blank line
                             (?![ ]*   iex>)      # Not a line starting with PS1
                             .+$\n?               # But any other line
                      )*)
            ''', re.MULTILINE | re.VERBOSE
        )

    def get_language_of(self, *args, **kargs):
        return 'elixir'

    def get_snippet_and_expected(self, match, where):
        snippet, expected = ExampleFinder.get_snippet_and_expected(
            self, match, where
        )

        snippet, expected = self._remove_prompts(snippet, expected)

        # IEx prints ':nil' on empty lines which it is very annoying.
        # Ensure that the example has no leading or trailing spaces
        # including new lines.
        # We assume that this will not affect the behaviour of IEx
        # or the example and that the Runner will add a new line at the
        # end to flush the example into the interpreter
        snippet = snippet.strip()
        return snippet, expected

    def _remove_prompts(self, snippet, expected):
        lines = snippet.split("\n")
        return '\n'.join(line[5:] for line in lines), expected


class ElixirParser(ExampleParser):
    language = 'elixir'

    @constant
    def example_options_string_regex(self):
        return re.compile(r'#\s*byexample:\s*([^\n\'"]*)$', re.MULTILINE)

    def extend_option_parser(self, parser):
        parser.add_flag(
            "elixir-dont-display-hack",
            default=False,
            help="required for IEx < 1.9."
        )
        parser.add_argument("+elixir-expr-print", choices=['auto', 'true', 'false'],
                            default='auto',
                            help='print the expression\'s value (true); ' +\
                                 'suppress it (false); or print it only ' +\
                                 'if the example has a => (auto, the default)')
        return parser

    def process_snippet_and_expected(self, snippet, expected_str):
        # IEx prints *always* the value of the last expression and it
        # can be too much invasive so we offer a way to 'disable' this.

        # If the example's expected has the marker (aka =>) we assume
        # that the user wants to check the value of the expression
        found = self._EXPR_RESULT_RE.search(expected_str) != None

        # see if we should print or not the expression.
        # actually, it is IEx that prints every expression (example)
        # we just decide if we ignore it or not
        if self.options['elixir_expr_print'] == 'true' or \
            (self.options['elixir_expr_print'] == 'auto' and found):

            self._elixir_print_expected = True
        else:
            self._elixir_print_expected = False

        # remove, if any the "expr print" marker as this is not part
        # of the real output
        if self._elixir_print_expected:
            expected_str = self._EXPR_RESULT_RE.sub('', expected_str, count=1)

        return ExampleParser.process_snippet_and_expected(
            self, snippet, expected_str
        )

    def parse(self, example, concerns):
        example = ExampleParser.parse(self, example, concerns)

        # In process_snippet_and_expected we found if we should print
        # the example or not. To propagate this we save that
        # in the example so the Runner can act on this
        example._elixir_print_expected = self._elixir_print_expected
        del self._elixir_print_expected
        return example

    _EXPR_RESULT_RE = re.compile(r'^=>([ ]*\n| |$)', re.MULTILINE | re.DOTALL)


class ElixirInterpreter(ExampleRunner, PexpectMixin):
    language = 'elixir'

    def __init__(self, verbosity, encoding, **unused):
        PexpectMixin.__init__(
            self,
            PS1_re=r'_byexample iex _byexample/iex> ',
            any_PS_re=r'_byexample (iex|\.\.\.) _byexample/iex> '
        )

        self.encoding = encoding

    def run(self, example, options):
        # the algorithm to filter the echos from the interpreter's output
        # (see _get_output()) doesn't work if the terminal is resized
        # so we disable this:
        options['geometry'] = self._terminal_default_geometry

        # interpreter's output requeries to be emulated by an ANSI Terminal
        # so we force this (see _get_output())
        options['term'] = 'ansi'

        return PexpectMixin._run(self, example, options)

    def _run_impl(self, example, options):
        src = example.source
        assert src[-1] == '\n'
        src = src[:-1]

        if self._elixir_dont_display_hack:
            # The user wants to use the dont_display_result hack.
            # This has some ugly side effects and it will not work if
            # the example (src) has a comment because it will comment out
            # our "; ..." appended hack.
            # However, this is the only way to silent IEx for version
            # that does not support the 'inspect_fun' config (IEx < 1.9)
            if not example._elixir_print_expected:
                src = src + ' ; IEx.dont_display_result'
        else:
            # Modern way to suppress or not the display of the result
            # for IEx >= 1.9.
            # We keep a state in _print_expre_activated so we know if we
            # need to switch or not the display suppression.
            if not example._elixir_print_expected and self._print_expre_activated:
                self._exec_and_wait(
                    r'IEx.configure(inspect: [inspect_fun: fn _a,_b -> "" end])',
                    options
                )
                self._print_expre_activated = False
            elif example._elixir_print_expected and not self._print_expre_activated:
                self._exec_and_wait(
                    r'IEx.configure(inspect: [inspect_fun: fn a,b -> Inspect.inspect(a,b) end])',
                    options
                )
                self._print_expre_activated = True

        return self._exec_and_wait(src, options)

    def interact(self, example, options):
        PexpectMixin.interact(self)

    def get_default_cmd(self, *args, **kargs):
        return "%e %p %a", {
            'e': '/usr/bin/env',
            'p': 'iex',
            'a': [
                '--dot-iex',
                '""',  # do not load any conf file
            ]
        }

    def initialize(self, options):
        shebang, tokens = self.get_default_cmd()
        shebang = options['shebangs'].get(self.language, shebang)

        cmd = ShebangTemplate(shebang).quote_and_substitute(tokens)

        self._print_expre_activated = True  # IEx default
        self._elixir_dont_display_hack = options['elixir_dont_display_hack']

        # run!
        options.up()
        options['geometry'] = (
            max(options['geometry'][0], 128), max(options['geometry'][1], 128)
        )
        self._spawn_interpreter(cmd, options, initial_prompt=r'iex\(\d+\)> ')
        options.down()
        self._drop_output()

        self._exec_and_wait(
            r'IEx.configure(default_prompt: "_byexample %prefix _byexample/iex>")',
            options
        )

        # Set a smaller width to force the pretty print of IEx to put some
        # new lines
        self._exec_and_wait(r'IEx.configure(inspect: [width: 32])', options)

        self._exec_and_wait(
            r'IEx.configure(colors: [enabled: false])', options
        )

    def _change_terminal_geometry(self, rows, cols, options):
        raise Exception("This should never happen")

    def _get_output(self, options):
        return self._get_output_echo_filtered(options)

    def shutdown(self):
        self._sendcontrol('c')
        time.sleep(0.001)
        self._sendcontrol('c')
        self._shutdown_interpreter()

    def cancel(self, example, options):
        # the following lines tries to ensure that we write '#iex:break'
        # at the begin of a new line so IEx will interpret it
        # unfortunately this also means that we will get spurious prompts
        # and ':nil' results.
        self._sendline("")
        self._sendline("")
        self._sendline("#iex:break")

        return self._recover_prompt_sync(example, options)
