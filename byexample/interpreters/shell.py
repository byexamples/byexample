import re, pexpect, sys, time
from byexample.byexample import ExampleParser

class ShellInterpreter(ExampleParser):
    def example_regex(self):
        return re.compile(r'''
            (?P<source>
                (?:^(?P<indent> [ ]*) (?:\$|\#)[ ]  .*)      # PS1 line
                (?:\n           [ ]*  >             .*)*)    # PS2 lines
            \n?
            # Want consists of any non-blank lines that do not start with PS1
            (?P<expected> (?:(?![ ]*$)        # Not a blank line
                          (?![ ]*(?:\$|\#))   # Not a line starting with PS1
                          .+$\n?              # But any other line
                      )*)
            ''', re.MULTILINE | re.VERBOSE)

    def example_options_regex(self):
        optstring_re = re.compile(r'#\s*byexample:\s*([^\n\'"]*)$',
                                                    re.MULTILINE)

        opt_re = re.compile(r'(?:(?P<add>\+)|(?P<del>-))(?P<name>\w+)',
                                                    re.MULTILINE)

        return optstring_re, opt_re

    def remove_prompts(self, source):
        return '\n'.join(line[1:] for line in source.split("\n"))

    def __repr__(self):
        return self.INTERPRETER_NAME

    INTERPRETER_NAME = "Shell (%s)" % "/bin/sh"

    def _spawn_new_shell(self, cmd):
        self.sh.send('export PS1\n' +\
                     'export PS2\n' +\
                     'export PS3\n' +\
                     'export PS4\n' +\
                     cmd + '\n')
        self._expect_prompt()


    def run(self, example, flags):
        if flags.get('bash', False):
            self._spawn_new_shell('/bin/bash --norc -i')
        elif flags.get('sh', False):
            self._spawn_new_shell('/bin/sh')

        self.sh.send(example.source + '\n')

        self._expect_prompt()
        return self._get_output()

    def _expect_prompt(self, timeout=2):
        expect = [self.PS1, pexpect.TIMEOUT]
        PS1_found, Timeout = range(len(expect))

        what = self.sh.expect(expect, timeout=timeout)
        self.last_output.append(self.sh.before)

        if what == PS1_found:
            while what != Timeout:
                what = self.sh.expect(expect, timeout=0.05)
                self.last_output.append(self.sh.before)

            # good, we found a prompt and we couldn't find another prompt after
            # the last one so we should be on the *last* prompt
        elif what == Timeout:
            raise Exception("Prompt not found: the code is taking too long to finish or there is a syntax error. Until now we got (last 1000 bytes):\n%s" % self.sh.before[-1000:])


    def _get_output(self):
        out = "".join(self.last_output)
        self.drop_output()

        # remove any other 'prompt'
        out = re.sub(self.PS2_re, '', out)

        # uniform the new line endings (aka universal new lines)
        out = re.sub(r'\r\n', r'\n', out)

        # TODO: is this ok?
        if out and not out.endswith('\n'):
            out += '\n'

        return out

    def drop_output(self):
        self.last_output = []

    def initialize(self):
        self.PS1     =  "/byexample/sh/ps1> "
        self.PS2_re  = r"/byexample/sh/ps\d+> "

        self.sh = pexpect.spawn('/bin/sh', echo=False)
        self.sh.delaybeforesend = 0.010
        self.last_output = []

        self.sh.send(
'''export PS1="/byexample/sh/ps1> "
export PS2="/byexample/sh/ps2> "
export PS3="/byexample/sh/ps3> "
export PS4="/byexample/sh/ps4> "
''')
        self._expect_prompt(timeout=10)
        self.drop_output() # discard banner and things like that

    def drop_output(self):
        self.last_output = []

    def shutdown(self):
        self.sh.sendeof()
        self.sh.close()
        time.sleep(0.01)
        self.sh.terminate(force=True)
