import re, pexpect, sys, time, termios, operator, string, shlex, os
from functools import reduce
from .executor import TimeoutException
from .common import tohuman

try:
    from shlex import quote as shlex_quote
except ImportError:
    from pipes import quote as shlex_quote

class ShebangTemplate(string.Template):
    delimiter = '%'

    def quote_and_substitute(self, tokens):
        '''
        Quote each token to be suitable for shell expansion and then
        perform a substitution in the template.

        >>> from byexample.runner import ShebangTemplate
        >>> tokens = {'a': ['-i', "-c", 'blue = "1"'],
        ...           'e': '/usr/bin/env', 'p': 'python'}

        The basic case is a simple template where each token
        is quoted except the lists: each item is quoted but not the
        whole list as a single unit.

        >>> shebang = '%e %p %a'
        >>> print(ShebangTemplate(shebang).quote_and_substitute(tokens))
        /usr/bin/env python -i -c 'blue = "1"'

        This works even if the token in the template are already quoted
        >>> shebang = '/bin/sh -c \'%e %p %a >/dev/null\''
        >>> print(ShebangTemplate(shebang).quote_and_substitute(tokens))
        /bin/sh -c '/usr/bin/env python -i -c '"'"'blue = "1"'"'"' >/dev/null'

        Here is another pair of examples:
        >>> tokens = {'a': ['-i', "-c", 'blue = \'1\''],
        ...           'e': '/usr/bin/env', 'p': 'py\'thon'}

        >>> shebang = '%e %p %a'
        >>> print(ShebangTemplate(shebang).quote_and_substitute(tokens))
        /usr/bin/env 'py'"'"'thon' -i -c 'blue = '"'"'1'"'"''

        >>> shebang = '/bin/sh -c \'%e %p %a >/dev/null\''
        >>> print(ShebangTemplate(shebang).quote_and_substitute(tokens))
        /bin/sh -c '/usr/bin/env '"'"'py'"'"'"'"'"'"'"'"'thon'"'"' -i -c '"'"'blue = '"'"'"'"'"'"'"'"'1'"'"'"'"'"'"'"'"''"'"' >/dev/null'
        '''

        self._tokens = {}
        self._not_quote_them = []
        for k, v in tokens.items():
            if isinstance(v, (list, tuple)):
                self._tokens[k] = ' '.join(shlex_quote(i) for i in v)
            else:
                self._tokens[k] = shlex_quote(v)

        cmd = []
        for x in shlex.split(self.template):
            # *before* the expansion, will this require quote? (will yield
            # more than a single item?)
            should_quote = len(shlex.split(x)) > 1

            # perform the expansion
            x = ShebangTemplate(x).substitute(self._tokens)

            # was needed to quote this *before* the expansion?
            if should_quote:
                x = shlex_quote(x)

            cmd.append(x)

        return ' '.join(cmd)

class ExampleRunner(object):
    def __init__(self, verbosity, encoding, **unused):
        self.verbosity = verbosity
        self.encoding = encoding

    def __repr__(self):
        return '%s Runner' % tohuman(self.language)

    def run(self, example, options):
        '''
        Run the example and return the output of the execution.

        The source code is in example.source.
        You may want to add additional new lines to the source
        to ensure that the underlying interpreter accept the code

        For example, if the source (in Python) is:
           'def f()
               pass
           '

        the Python interpreter will need an extra new line to understand
        that the function definition does not continue.

        See the documentation of Example to see what other attributes it
        has.

        The parameter 'options' configure some aspects of the execution.
        For example, the option 'timeout' set for how long an execution
        should be running.
        If time out, raise an exception of type TimeoutException.

        See the code of the default runners of ``byexample`` like
        PythonInterpreter and RubyInterpreter to get more information.
        '''
        raise NotImplementedError() # pragma: no cover

    def interact(self, example, options):
        '''
        Connect the current runner/interpreter session to the byexample's console
        allowing the user to manually interact with the interpreter.
        '''
        raise NotImplementedError() # pragma: no cover

    def initialize(self, options):
        '''
        Hook to initialize the runner. This method will be called
        before running any example.
        '''
        raise NotImplementedError() # pragma: no cover

    def shutdown(self):
        '''
        Hook to shutdown the runner. This method will be called
        after running all the examples.
        '''
        raise NotImplementedError() # pragma: no cover


class PexepctMixin(object):
    def __init__(self, PS1_re, any_PS_re):
        self.PS1_re = re.compile(PS1_re)
        self.any_PS_re = re.compile(any_PS_re)

        self.last_output = []

    def _spawn_interpreter(self, cmd, delaybeforesend=None,
                                        wait_first_prompt=True,
                                        first_prompt_timeout=10,
                                        geometry=(24, 80)):
        env = os.environ.copy()
        env.update({'LINES': str(geometry[0]), 'COLUMNS': str(geometry[1])})

        self._drop_output() # there shouldn't be any output yet but...
        self.interpreter = pexpect.spawn(cmd, echo=False,
                                                encoding=self.encoding,
                                                dimensions=geometry,
                                                env=env)
        self.interpreter.delaybeforesend = delaybeforesend
        self.interpreter.delayafterread = None

        if wait_first_prompt:
            self._expect_prompt(timeout=first_prompt_timeout, prompt_re=self.PS1_re)
            self._drop_output() # discard banner and things like that

    def interact(self, send='\n', escape_character=chr(29),
                                    input_filter=None, output_filter=None): # pragma: no cover
        def ensure_cooked_mode(input_str):
            self._set_cooked_mode(True)
            if input_filter:
                return input_filter(input_str)
            return input_str

        attr = termios.tcgetattr(self.interpreter.child_fd)
        try:
            if send:
                self.interpreter.send(send)
            self.interpreter.interact(escape_character=escape_character,
                                      input_filter=ensure_cooked_mode,
                                      output_filter=output_filter)
        finally:
            termios.tcsetattr(self.interpreter.child_fd, termios.TCSANOW, attr)


    def _drop_output(self):
        self.last_output = []

    def _shutdown_interpreter(self):
        self.interpreter.sendeof()
        self.interpreter.close()
        time.sleep(0.001)
        self.interpreter.terminate(force=True)

    def _exec_and_wait(self, source, timeout):
        lines = source.split('\n')
        for line in lines[:-1]:
            self.interpreter.sendline(line)

            begin = time.time()
            self._expect_prompt(timeout)
            timeout -= max(time.time() - begin, 0)

        self.interpreter.sendline(lines[-1])
        self._expect_prompt(timeout, prompt_re=self.PS1_re)

        return self._get_output()

    def _expect_prompt(self, timeout, prompt_re=None):
        ''' Wait for a <prompt_re> (any self.any_PS_re if <prompt_re> is None)
            and raise a timeout if we cannot find one.

            After the successful expect, collect the 'before' output into
            self.last_output
        '''
        _timeout_msg = "Prompt not found: the code is taking too long to finish or there is a syntax error.\nLast 1000 bytes read:\n%s"
        if timeout <= 0:
            out = self._get_output()
            raise TimeoutException(_timeout_msg % ''.join(self.last_output)[-1000:],
                                    out)

        if not prompt_re:
            prompt_re = self.any_PS_re

        expect = [prompt_re, pexpect.TIMEOUT]
        PS_found, Timeout = range(len(expect))

        what = self.interpreter.expect(expect, timeout=timeout)
        self.last_output.append(self.interpreter.before)

        if what == Timeout:
            out = self._get_output()
            raise TimeoutException(_timeout_msg % ''.join(self.last_output)[-1000:],
                                    out)


    def _get_output(self):
        out = "".join(self.last_output)
        self._drop_output()

        # remove any other 'prompt' if any
        if self.any_PS_re:
            out = self.any_PS_re.sub('', out)

        # uniform the new line endings (aka universal new lines)
        out = self._universal_new_lines(out)

        return out

    def _universal_new_lines(self, out):
        return out.replace('\r\n', '\n').replace('\r', '\n')

    def _set_cooked_mode(self, state): # pragma: no cover
        # code borrowed from ptyprocess/ptyprocess.py, _setecho, and
        # adapted adding more flags to it based in stty(1)
        errmsg = '_set_cooked_mode() may not be called on this platform'

        fd = self.interpreter.child_fd

        try:
            attr = termios.tcgetattr(fd)
        except termios.error as err:
            if err.args[0] == errno.EINVAL:
                raise IOError(err.args[0], '%s: %s.' % (err.args[1], errmsg))
            raise

        input_flags = (
                       'BRKINT',
                       'IGNPAR',
                       'ISTRIP',
                       'ICRNL',
                       'IXON',
                       )

        output_flags = (
                       'OPOST',
                       )

        local_flags = (
                      'ECHO',
                      'ISIG',
                      'ICANON',
                      )

        if state:
            attr[0] |= reduce(operator.or_,
                                [getattr(termios, flag_name) for flag_name in input_flags])
            attr[1] |= reduce(operator.or_,
                                [getattr(termios, flag_name) for flag_name in output_flags])
            attr[3] |= reduce(operator.or_,
                                [getattr(termios, flag_name) for flag_name in local_flags])
        else:
            attr[0] &= reduce(operator.and_,
                                [~getattr(termios, flag_name) for flag_name in input_flags])
            attr[1] &= reduce(operator.and_,
                                [~getattr(termios, flag_name) for flag_name in output_flags])
            attr[3] &= reduce(operator.and_,
                                [~getattr(termios, flag_name) for flag_name in local_flags])


        try:
            termios.tcsetattr(fd, termios.TCSANOW, attr)
        except IOError as err:
            if err.args[0] == errno.EINVAL:
                raise IOError(err.args[0], '%s: %s.' % (err.args[1], errmsg))
            raise
