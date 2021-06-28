"""
Example:
  $ hello() {
  >     echo "hello bla world"
  > }

  $ hello               # byexample: +norm-ws
  hello   <...>   world

  $ for i in 0 1 2 3; do
  >    echo $i
  > done
  0
  1
  2
  3

  $ echo "this
  > is a multiline
  > string"
  this
  is a multiline
  string

  $ read -p "num: " ; echo $REPLY    # byexample: +type
  num: [42]
  42

  $ read ; echo $REPLY    # byexample: +type
  [it works!]
  it works!
"""

from __future__ import unicode_literals
import pexpect, sys, time
import byexample.regex as re
from byexample.common import constant, Countdown
from byexample.parser import ExampleParser
from byexample.finder import ExampleFinder
from byexample.runner import ExampleRunner, PexpectMixin, ShebangTemplate
from byexample.executor import TimeoutException

stability = 'provisional'


class ShellPromptFinder(ExampleFinder):
    target = 'shell-prompt'

    @constant
    def example_regex(self):
        return re.compile(
            r'''
            (?P<snippet>
                (?:^(?P<indent> [ ]*) (?:\$)[ ]  .*)      # PS1 line
                (?:\n           [ ]*  >             .*)*)    # PS2 lines
            \n?
            ## Want consists of any non-blank lines that do not start with PS1
            (?P<expected> (?:(?![ ]*$)        # Not a blank line
                          (?![ ]*(?:\$))      # Not a line starting with PS1
                          .+$\n?              # But any other line
                      )*)
            ''', re.MULTILINE | re.VERBOSE
        )

    def get_language_of(self, *args, **kargs):
        return 'shell'

    def get_snippet_and_expected(self, match, where):
        snippet, expected = ExampleFinder.get_snippet_and_expected(
            self, match, where
        )

        snippet = self._remove_prompts(snippet)
        return snippet, expected

    def _remove_prompts(self, snippet):
        lines = snippet.split("\n")
        return '\n'.join(line[2:] for line in lines)


class ShellParser(ExampleParser):
    language = 'shell'

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
            "+stop-signal",
            choices=['suspend', 'eof', 'interrupt'],
            default='suspend',
            help=
            "signal to send when stop-on-timeout/stop-on-silence is used (suspend ^Z by default)."
        )
        parser.add_argument(
            "+shell",
            choices=['bash', 'dash', 'ksh', 'sh'],
            default='bash',
            help=
            "shell to use with default settings ('bash' by default). For full control use -x-shebang)"
        )


class ShellInterpreter(ExampleRunner, PexpectMixin):
    language = 'shell'

    def __init__(self, verbosity, encoding, **unused):
        self.encoding = encoding

        PexpectMixin.__init__(
            self,
            PS1_re=r"/byexample/sh/ps1> ",
            any_PS_re=r"/byexample/sh/ps\d+> "
        )

    def get_default_cmd(self, *args, **kargs):
        shell = kargs.pop('shell', 'bash')
        return "%e %p %a", {
            'bash': {
                'e': '/usr/bin/env',
                'p': 'bash',
                'a': ['--norc', '--noprofile', '--posix', '--noediting'],
            },
            'dash': {
                'e': '/usr/bin/env',
                'p': 'dash',
                'a': [],
            },
            'ksh': {
                'e': '/usr/bin/env',
                'p': 'ksh',
                'a': ['+E'],
            },
            'sh': {
                'e': '/usr/bin/env',
                'p': 'sh',
                'a': [],
            },
        }[shell]

    def run(self, example, options):
        return PexpectMixin._run(self, example, options)

    def _run_impl(self, example, options):
        stop_on_timeout = options['stop_on_timeout'] is not False
        stop_on_silence = options['stop_on_silence'] is not False
        stop_signal = options['stop_signal']
        try:
            return self._exec_and_wait(
                example.source, options, from_example=example
            )
        except TimeoutException as ex:
            if stop_on_timeout or stop_on_silence:
                # get the current output
                out = ex.output

                if stop_signal == 'suspend':
                    # stop the process to get back the control of the shell.
                    # this require that the job monitoring system of
                    # the shell is on (set -m)
                    self._sendcontrol('z')
                elif stop_signal == "eof":
                    self._sendcontrol('d')
                elif stop_signal == "interrupt":
                    self._sendcontrol('c')
                else:
                    raise ValueError(
                        "Unexpected stop-signal '%s'" % stop_signal
                    )

                # wait for the prompt, ignore any extra output
                self._expect_prompt(
                    options,
                    countdown=Countdown(options['x']['dfl_timeout']),
                    prompt_re=self._PS1_re
                )

                self._drop_output()
                return out
            raise

    def _expect_prompt(
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
        shebang, tokens = self.get_default_cmd(shell=options['shell'])
        shebang = options['shebangs'].get(self.language, shebang)

        cmd = ShebangTemplate(shebang).quote_and_substitute(tokens)
        self._spawn_interpreter(cmd, options, wait_first_prompt=False)

        self._exec_and_wait(
            '''export PS1="/byexample/sh/ps1> "
export PS2="/byexample/sh/ps2> "
export PS3="/byexample/sh/ps3> "
export PS4="/byexample/sh/ps4> "
''',
            options,
            timeout=options['x']['dfl_timeout']
        )

        self._drop_output()  # discard banner and things like that

    def shutdown(self):
        self._shutdown_interpreter()

    def cancel(self, example, options):
        return self._abort(example, options)
