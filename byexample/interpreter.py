import re, pexpect, sys, time
from .runner import TimeoutException

class PexepctMixin(object):
    def __init__(self, cmd, PS1_re, any_PS_re):
        self.cmd = cmd
        self.PS1_re = PS1_re
        self.any_PS_re = any_PS_re

        self.last_output = []

    def _spawn_interpreter(self, delaybeforesend=0.010, wait_first_prompt=True,
                                        first_propmt_timeout=10):
        self._drop_output() # there shouldn't be any output yet but...
        self.interpreter = pexpect.spawn(self.cmd, echo=False,
                                                encoding=self.encoding)
        self.interpreter.delaybeforesend = delaybeforesend

        if wait_first_prompt:
            self._expect_prompt(timeout=first_propmt_timeout)
            self._drop_output() # discard banner and things like that

    def _drop_output(self):
        self.last_output = []

    def _shutdown_interpreter(self):
        self.interpreter.sendeof()
        self.interpreter.close()
        time.sleep(0.001)
        self.interpreter.terminate(force=True)

    def _exec_and_wait(self, source, timeout=2):
        self.interpreter.send(source)
        self._expect_prompt(timeout)

        return self._get_output()

    def _expect_prompt(self, timeout):
        ''' Wait for a PS1 prompt, raises a timeout if we cannot find one.

            if we get a timeout that could mean:
                - the code executed is taking too long to finish
                - the code is malformed and the interpreter is waiting
                  more data like this:
                    prompt-1) [ 1, 2,
                    prompt-2)   3, 4,
                    prompt-2)   5, 6,

                    (the ] is missing, for example)
            if we don't get a timeout that could mean:
                - good, we got the *last* prompt line
                - good but we may didn't get the *last* prompt line
                  and we should try to find the next prompt again
        '''
        expect = [self.PS1_re, pexpect.TIMEOUT]
        PS1_found, Timeout = range(len(expect))

        what = self.interpreter.expect(expect, timeout=timeout)
        self.last_output.append(self.interpreter.before)

        if what == PS1_found:
            while what != Timeout:
                what = self.interpreter.expect(expect, timeout=0.05)
                self.last_output.append(self.interpreter.before)

            # good, we found a prompt and we couldn't find another prompt after
            # the last one so we should be on the *last* prompt
        elif what == Timeout:
            raise TimeoutException("Prompt not found: the code is taking too long to finish or there is a syntax error.\nLast 1000 bytes read:\n%s" % self.interpreter.before[-1000:])

    def _get_output(self):
        out = "".join(self.last_output)
        self._drop_output()

        # remove any other 'prompt'
        out = re.sub(self.any_PS_re, '', out)

        # uniform the new line endings (aka universal new lines)
        out = self._universal_new_lines(out)

        return out

    def _universal_new_lines(self, out):
        out = re.sub(r'\r\n', r'\n', out)

        # TODO: is this ok?
        if out and not out.endswith('\n'):
            out += '\n'

        return out
