r"""
Example:

  :> ;! M
  [0x1000000-0x11fffff] (sz 0x200000)

  :> ;! M[0x1000:0x2000] = 0x41       # write like 'memset'
  Mapping memory region [0x1000-0x1fff] (sz 0x1000)

  :> ;! M[0x1055:0x105a] = b'B' * 5   # write like 'memcpy'

  :> ;! M[0x1050:0x105a]     # read
  [AAAAABBBBB]

  :> ;! M    # list mapped pages    # byexample: +norm-ws
  [0x1000-0x1fff]               (sz 0x1000)
  [0x1000000-0x11fffff]         (sz 0x200000)

  :> ;! M[0x1000:0x1000+46].hex() # display in hexdump
  00001000  41 41 41 41 41 41 41 41  41 41 41 41 41 41 41 41  |AAAAAAAAAAAAAAAA|
  *
  00001020  41 41 41 41 41 41 41 41  41 41 41 41 41 41        |AAAAAAAAAAAAAA  |

  :> ;! M[0x1000:0x1000+8].disass()   # disassembly
  00001000  .byte   0x41, 0x41, 0x41, 0x41
  00001004  .byte   0x41, 0x41, 0x41, 0x41

  :> ;! del M[0x1000:0x2000]    # unmap


"""

from __future__ import unicode_literals
import sys, time
import byexample.regex as re
from byexample.common import constant
from byexample.parser import ExampleParser
from byexample.runner import ExampleRunner, PexpectMixin, ShebangTemplate
from byexample.finder import ExampleFinder

stability = 'experimental'


class IAsmPromptFinder(ExampleFinder):
    target = 'iasm-prompt'

    @constant
    def example_regex(self):
        return re.compile(
            r'''
            (?P<snippet>
                (?:^(?P<indent> [ ]*) (?::>)[ ]  .*)         # PS1 line
                (?:\n           [ ]*  ->             .*)*)    # PS2 lines
            \n?
            ## Want consists of any non-blank lines that do not start with PS1
            (?P<expected> (?:(?![ ]*$)        # Not a blank line
                          (?![ ]*(?::>))     # Not a line starting with PS1
                          .+$\n?              # But any other line
                      )*)
            ''', re.MULTILINE | re.VERBOSE
        )

    def get_language_of(self, *args, **kargs):
        return 'iasm'

    def get_snippet_and_expected(self, match, where):
        snippet, expected = ExampleFinder.get_snippet_and_expected(
            self, match, where
        )

        snippet = self._remove_prompts(snippet)
        return snippet, expected

    def _remove_prompts(self, snippet):
        lines = snippet.split("\n")
        return '\n'.join(line[3:] for line in lines)


class IAsmParser(ExampleParser):
    language = 'iasm'

    @constant
    def example_options_string_regex(self):
        # anything of the form:
        #   # byexample:  +FOO -BAR +ZAZ=42
        #   ; byexample:  +FOO -BAR +ZAZ=42
        return re.compile(r'[;#][ ]\s*byexample:\s*([^\n\'"]*)$', re.MULTILINE)

    def extend_option_parser(self, parser):
        parser.add_argument(
            "+iasm-arch",
            metavar='<arch>',
            default='arm',
            help=
            "architecture name (arm, x86, sparc, ...); see iasm documentation."
        )
        parser.add_argument(
            "+iasm-mode",
            metavar='<mode>',
            default='arm',
            help="mode (arm, 32, 64, ...); see iasm documentation."
        )
        parser.add_argument(
            "+iasm-code-size",
            metavar='<sz>',
            default=2 * 1024 * 1024,
            type=int,
            help="size of the code segment; see iasm documentation."
        )
        parser.add_argument(
            "+iasm-pc",
            metavar='<addr>',
            default=0x1000000,
            type=int,
            help=
            "starting address, value of the program counter; see iasm documentation."
        )


class IAsmInterpreter(ExampleRunner, PexpectMixin):
    language = 'iasm'

    def __init__(self, verbosity, encoding, **unused):
        self.encoding = encoding

        PexpectMixin.__init__(self, PS1_re=r':>', any_PS_re=r'[:-]>')

    def get_default_cmd(self, arch, mode, sz, pc, *args, **kargs):
        return "%e %p %a", {
            'e':
            "/usr/bin/env",
            'p':
            "iasm",
            'a': [
                "-a",
                arch,
                "-m",
                mode,
                "--code-size",
                str(sz),
                "--program-counter",
                str(pc),
                "--simple-prompt",
                "--no-history",
                "--reg-glob",
                "''",
                "--style",
                "none",
            ]
        }

    def run(self, example, options):
        # iasm's output requeries to be emulated by an ANSI Terminal
        # so we force this (see _get_output())
        options['geometry'] = self._terminal_default_geometry
        options['term'] = 'ansi'

        return PexpectMixin._run(self, example, options)

    def _run_impl(self, example, options):
        src = example.source
        src = src.rstrip('\n')
        return self._exec_and_wait(src, options, from_example=example)

    def interact(self, example, options):
        PexpectMixin.interact(self)

    def initialize(self, options):
        arch = options['iasm_arch']
        mode = options['iasm_mode']
        sz = options['iasm_code_size']
        pc = options['iasm_pc']

        shebang, tokens = self.get_default_cmd(
            arch=arch, mode=mode, sz=sz, pc=pc
        )
        shebang = options['shebangs'].get(self.language, shebang)

        cmd = ShebangTemplate(shebang).quote_and_substitute(tokens)

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

    def _expect_and_read(self, expect_list, timeout, expect_kinds):
        # This is a hack
        #
        # iasm does not turn of the echo so we receive the prompt twice.
        # For these cases we should call _get_output_echo_filtered but due
        # the weird handling of iasm, the echo filtering algorithm doesn't
        # work.
        # A workaround was to wait for the prompt twice and return only
        # the output that happen between the two prompts.
        #
        # Later, in _get_output, the obtained output is echo-filtered
        # and emulated with an ANSI terminal.
        #
        # See _get_output and run methods of this class.
        #
        # It seems to work, not really sure how it would work when
        # expect_list has a non-prompt regex (like the ones to support
        # input_list (+type feature).
        #
        # See _expect_prompt.
        PS_found, Timeout, EOF, Earlier = expect_kinds
        what = self._interpreter.expect(expect_list, timeout=timeout)
        if what != PS_found:
            return what, self._interpreter.before

        what = self._interpreter.expect(expect_list, timeout=timeout)
        return what, self._interpreter.before

    def cancel(self, example, options):
        return self._abort(example, options)
