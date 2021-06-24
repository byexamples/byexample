"""
Example:

    PS> 1 + 2
    3

"""

from __future__ import unicode_literals
import pexpect, sys, time
import byexample.regex as re
from byexample.common import constant, Countdown
from byexample.parser import ExampleParser
from byexample.finder import ExampleFinder
from byexample.runner import ExampleRunner, PexpectMixin, ShebangTemplate
from byexample.executor import TimeoutException

stability = 'experimental'


class PowerShellPromptFinder(ExampleFinder):
    target = 'pwsh-prompt'

    @constant
    def example_regex(self):
        return re.compile(
            r'''
            (?P<snippet>
                (?:^(?P<indent> [ ]*) (?:PS>)[ ]  .*)      # PS1 line
                (?:\n           [ ]*  >>>         .*)*)    # PS2 lines
            \n?
            ## Want consists of any non-blank lines that do not start with PS1
            (?P<expected> (?:(?![ ]*$)        # Not a blank line
                          (?![ ]*(?:\$))      # Not a line starting with PS1
                          .+$\n?              # But any other line
                      )*)
            ''', re.MULTILINE | re.VERBOSE
        )

    def get_language_of(self, *args, **kargs):
        return 'pwsh'

    def get_snippet_and_expected(self, match, where):
        snippet, expected = ExampleFinder.get_snippet_and_expected(
            self, match, where
        )

        snippet = self._remove_prompts(snippet)
        return snippet, expected

    def _remove_prompts(self, snippet):
        lines = snippet.split("\n")
        return '\n'.join(line[4:] for line in lines)


class PowerShellParser(ExampleParser):
    language = 'pwsh'

    @constant
    def example_options_string_regex(self):
        return re.compile(r'#\s*byexample:\s*([^\n\'"]*)$', re.MULTILINE)

    def extend_option_parser(self, parser):
        parser.add_flag(
            "stop-on-timeout",
            default=False,
            help="stop the process if it timeout."
        )
        parser.add_argument(
            "+stop-on-silence",
            nargs='?',
            metavar='secs',
            default=False,
            const=0.2,
            type=float,
            help=
            "stop the process if no output is read in the last <secs> seconds (0.2 secs by default)."
        )
        parser.add_argument(
            "+shell",
            choices=['bash', 'dash', 'ksh', 'sh'],
            default='bash',
            help=
            "shell to use with default settings ('bash' by default). For full control use -x-shebang)"
        )


class PowerShellInterpreter(ExampleRunner, PexpectMixin):
    language = 'pwsh'

    def __init__(self, verbosity, encoding, **unused):
        self.encoding = encoding

        PexpectMixin.__init__(
            self, PS1_re=r"XXXXXXXXXXXXXXXX ", any_PS_re=r">> "
        )

    def get_default_cmd(self, *args, **kargs):
        return "%e %p %a", {
            'e':
            '/usr/bin/env',
            'p':
            'pwsh',
            'a': [
                #'-NonInteractive',
                #'-NoLogo',
                '-NoProfile',
                '-NoExit',
                '-Command',
                'Remove-Module psreadline ; function prompt { "XXXXXXXXXXXXXXXX " }'
            ],
        }

    def run(self, example, options):
        return PexpectMixin._run(self, example, options)

    def _run_impl(self, example, options):
        #stop_on_timeout = options['stop_on_timeout'] is not False
        #stop_on_silence = options['stop_on_silence'] is not False
        try:
            return self._exec_and_wait(
                example.source, options, from_example=example
            )
        except TimeoutException as ex:
            raise
            if stop_on_timeout or stop_on_silence:
                # get the current output
                out = ex.output

                # stop the process to get back the control of the shell.
                # this require that the job monitoring system of
                # the shell is on (set -m)
                self._sendcontrol('z')

                # wait for the prompt, ignore any extra output
                self._expect_prompt(
                    options,
                    countdown=Countdown(options['x']['dfl_timeout']),
                    prompt_re=self._PS1_re
                )

                self._drop_output()
                return out
            raise

    def XXXX_expect_prompt(
        self, options, countdown, prompt_re=None, earlier_re=None
    ):
        if options['stop_on_silence'] is not False:
            prev = 0
            while 1:
                tmp = min(options['stop_on_silence'], countdown.left())
                silence_countdown = Countdown(tmp)
                try:
                    countdown.start()
                    try:
                        return PexpectMixin._expect_prompt(
                            self, options, silence_countdown, prompt_re,
                            earlier_re
                        )
                    finally:
                        countdown.stop()
                except TimeoutException as ex:
                    # a real timeout
                    if countdown.did_run_out(
                    ) or silence_countdown.did_run_out():
                        raise

                    # inactivity or silence detected
                    if prev >= len(ex.output):
                        raise

                    prev = len(ex.output)

        else:
            return PexpectMixin._expect_prompt(
                self, options, countdown, prompt_re, earlier_re
            )

    def interact(self, example, options):
        PexpectMixin.interact(self)

    def initialize(self, options):
        shebang, tokens = self.get_default_cmd()
        shebang = options['shebangs'].get(self.language, shebang)

        cmd = ShebangTemplate(shebang).quote_and_substitute(tokens)
        self._spawn_interpreter(cmd, options, wait_first_prompt=True)

        #        self._exec_and_wait(
        #            '''function prompt { "XXXXXXXXXXXXXXXX " }
        #''',
        #            options,
        #            timeout=options['x']['dfl_timeout']
        #        )

        self._drop_output()  # discard banner and things like that

    def shutdown(self):
        self._shutdown_interpreter()

    def cancel(self, example, options):
        return False  # not supported

    #def _get_output(self, options):
    #    return self._get_output_echo_filtered(options)

    def _change_terminal_geometry(self, rows, cols, options):
        raise Exception("This should never happen")
