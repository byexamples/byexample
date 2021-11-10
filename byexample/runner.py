from __future__ import unicode_literals
import pexpect, pexpect.popen_spawn, time, operator, os, itertools, contextlib
import signal
from . import regex as re
from functools import reduce, partial
from .executor import TimeoutException, InputPrefixNotFound, InterpreterClosedUnexpectedly, InterpreterNotFound
from .common import tohuman, ShebangTemplate, Countdown, short_string
from .example import Example
from .log import clog
from .prof import profile, profile_ctx

from pyte import Stream, Screen
import sys


class ExampleRunner(object):
    flavors = set()

    def __init__(self, verbosity, encoding, **unused):
        self.verbosity = verbosity
        self.encoding = encoding

    def __repr__(self):
        return '%s Runner' % tohuman(self.language if self.language else self)

    def run(self, example, options):
        r'''
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
        raise NotImplementedError()  # pragma: no cover

    def interact(self, example, options):
        r'''
        Connect the current runner/interpreter session to the byexample's console
        allowing the user to manually interact with the interpreter.
        '''
        raise NotImplementedError()  # pragma: no cover

    def initialize(self, options):
        r'''
        Hook to initialize the runner. This method will be called
        before running any example.

        If the reset() method is called and return True, it is assumed
        that the runner was reset and can be reused for another round
        of examples (another file) *without* calling initialize() again.

        initialize() will **not** be called as long as reset() is being
        called and returning True.

        Otherwise it will be called on each new file to process before
        executing any example.

        See also shutdown()

        The following state diagram should picture this:

                           new file,
        (not alive) --> call initialize() --> (alive, clean) --> call run() <-|
              ^                                      ^               |        |
              |                                      |               v        |
              |                                 reset True    (alive, dirty) -/
              |                                      ^               |
              |                     if forced        |               v
              |                  /- shutdown  <----- | ----- no more examples;
              |                 /                    |               |
              |                /                     |               v
         call shutdown() <----/- reset False or  <---\---- not forced shutdown,
                                     failed                   call reset()
        '''
        raise NotImplementedError()  # pragma: no cover

    def shutdown(self):
        r'''
        Hook to shutdown the runner. This method will be called
        after running all the examples.

        If the reset() method is called and return True, it is assumed
        that the runner was reset and can be reused for another round
        of examples (another file) so *no* shutdown will be done.

        shutdown() will **not** be called as long as reset() is being
        called and returning True in general but it *MAY* be called even that
        if an error is detected in another runner or the whole execution
        is shutting down.

        Otherwise it will be called after executing each file's examples.

        If the shutdown() was not called and no more files are assigned to
        this job (FileExecutor), the method will be called once at the end.

        Regardless of reset(), there is a 1-to-1 relationship with
        initialize(): if the initialize() is called N times, the shutdown()
        will be called N times and the calls will be interleaved (initialize()
        then shutdown() the initialize() then shutdown() and so on).
        '''
        raise NotImplementedError()  # pragma: no cover

    def reset(self, options):
        r'''
        Hook to reset the runner. This method *may* be called
        after running all the examples of the current processed file.

        The job (FileExecutor) will decide if this method will be called
        or not based on the user's options.

        It is up to the runner's implementation if the reset
        can be made without restarting the interpreter in which case *must*
        return True; otherwise False.

        A reset without a restart should keep the interpreter alive
        but with an clean state to run a new set of examples independently.

        By default, reset returns False (not supported).

        Returning False means that shutdown() will be called instead (and
        initialize() will be called on the next file)
        '''
        return False

    def cancel(self, example, options):
        r'''
        Abort the execution of the current example. This method will typically
        be called after the example timeout.

        Return True if the cancel succeeded and the runner can be still used,
        False otherwise.
        '''
        return False

    def get_version(self, options):
        r'''
        Return the version of the underlying interpreter or runner in form
        of a tuple. Return None if no version was determined.

        This method may be called several times: it may be beneficial to
        cache the results.
        '''
        return None


class PopenSpawnExt(pexpect.popen_spawn.PopenSpawn):
    ''' This is a compatibility layer that extends pexpect's PopenSpawn
        to work more similar to pexpect's spawn class.
    '''
    def __init__(self, cmd, **kargs):
        kargs.pop('echo')
        kargs.pop('dimensions')

        self.delayafterclose = 0.1
        self.delayafterterminate = 0.1

        super().__init__(cmd, **kargs)
        self._closed = False

    def isalive(self):
        return bool(self.proc.poll())

    def sendcontrol(self, control):
        if control == 'c':
            self.kill(signal.SIGINT)
        elif control == 'd':
            self.sendeof()
        else:
            raise NotImplementedError(
                f"Runner popen/subprocess-based does not support sending a control character '{control}'."
            )

    def close(self, force=True):
        if self._closed:
            return

        # Close the subprocess' stdin and wait.
        # This is a delay used by PtyProcess so we have the same semantics
        self.sendeof()
        time.sleep(self.delayafterclose)

        # It's ok to terminate the subprocess even if it is not alive:
        # terminate() will take care of that.
        if not self.terminate(force):
            raise Exception(
                'Could not close/terminate the popen/subprocess-based runner.'
            )

        self._closed = True

    def terminate(self, force=False):
        ''' Send to the subprocess a SIGHUP, SIGCONT and SIGINT to
            stop terminate it and if force is True send also a SIGKILL.

            Returns True if the process is dead, False otherwise.
        '''
        signals = [signal.SIGHUP, signal.SIGCONT, signal.SIGINT]
        if force:
            signals.append(signal.SIGKILL)

        for sig in signals:
            if not self.isalive():
                return True

            try:
                self.kill(sig)
            except:
                time.sleep(self.delayafterterminate)
                return not self.isalive()

            time.sleep(self.delayafterterminate)

        return not self.isalive()

    def setwinsize(self, rows, cols):
        pass


class PexpectMixin(object):
    def __init__(self, PS1_re, any_PS_re):
        self._set_prompts(PS1_re, any_PS_re)

        self._output_between_prompts = []
        self._last_output_may_be_incomplete = False
        self._cmd = None

    def _set_prompts(self, PS1_re, any_PS_re):
        self._PS1_re = re.compile(PS1_re)
        self._any_PS_re = re.compile(any_PS_re)

    def _send(self, s):
        self._interpreter.send(s)

    def _sendline(self, line):
        self._interpreter.sendline(line)

    def _sendcontrol(self, control):
        self._interpreter.sendcontrol(control)

    def _setwindowsize(self, rows, cols):
        self._interpreter.setwinsize(rows, cols)

    @profile
    def _spawn_interpreter(
        self,
        cmd,
        options,
        wait_first_prompt=True,
        first_prompt_timeout=None,
        initial_prompt=None,
        subprocess=False,
        env_update=None
    ):
        self._cmd = None

        if first_prompt_timeout is None:
            first_prompt_timeout = options['x']['dfl_timeout']

        rows, cols = options['geometry']
        self._terminal_default_geometry = (rows, cols)

        env = os.environ.copy()
        if env_update:
            env.update(env_update)
        env.update({'LINES': str(rows), 'COLUMNS': str(cols)})

        self._drop_output()  # there shouldn't be any output yet but...
        self._cmd = cmd

        clog().info("Spawn command line: %s", cmd)
        spawner = PopenSpawnExt if subprocess else pexpect.spawn
        try:
            self._interpreter = spawner(
                cmd,
                echo=False,
                encoding=self.encoding,
                dimensions=(rows, cols),
                env=env
            )
        except Exception as err:
            if 'command was not found' in str(err):
                msg = 'The command was not found or was not executable.'
                msg += '\nThe full command line tried is as follows:\n'
                msg += cmd
                msg += '\n\nThis could happen because you do not have it installed or' + \
                       '\nit is not in the PATH.'
                e = InterpreterNotFound(msg, self._cmd).with_traceback(
                    sys.exc_info()[2]
                )
                raise e from None
            raise

        self._interpreter.delaybeforesend = options['x']['delaybeforesend']
        self._interpreter.delayafterread = None

        self._last_num_lines_sent = 0

        self._create_terminal(options)

        if wait_first_prompt:
            prompt_re = self._PS1_re if initial_prompt is None else initial_prompt
            self._expect_prompt(
                options,
                countdown=Countdown(first_prompt_timeout),
                prompt_re=prompt_re
            )
            self._drop_output()  # discard banner and things like that

    @property
    def last_num_lines_sent(self):
        ''' Return the number of lines sent to the interpreter
            in the last call to _exec_and_wait().

            The counter is reset on each call to _exec_and_wait();
            calls to self._sendline() outside of _exec_and_wait() are
            not counted.
        '''
        return self._last_num_lines_sent

    def _interact(
        self,
        send='\n',
        escape_character=chr(29),
        input_filter=None,
        output_filter=None
    ):  # pragma: no cover
        def ensure_cooked_mode(input_str):
            self._set_cooked_mode(True)
            if input_filter:
                return input_filter(input_str)
            return input_str

        if not self._interpreter.isatty():
            return

        import termios
        attr = termios.tcgetattr(self._interpreter.child_fd)
        try:
            if send:
                self._send(send)
            self._interpreter.interact(
                escape_character=escape_character,
                input_filter=ensure_cooked_mode,
                output_filter=output_filter
            )
        finally:
            termios.tcsetattr(
                self._interpreter.child_fd, termios.TCSANOW, attr
            )

    def _run(self, example, options):
        with self._change_terminal_geometry_ctx(options):
            return self._run_impl(example, options)

    def _run_impl(self, example, options):
        raise NotImplementedError()  # pragma: no cover

    def _drop_output(self):
        self._output_between_prompts = []
        self._last_output_may_be_incomplete = False

    @profile
    def _shutdown_interpreter(self):
        self._interpreter.sendeof()
        try:
            self._interpreter.close()
        except Exception as ex:
            clog().debug(
                "Call to close() on interpreter failed (may happen): %s.",
                str(ex)
            )

        time.sleep(0.001)
        try:
            self._interpreter.terminate(force=True)
        except Exception as ex:
            clog().debug(
                "Call to terminate() on interpreter failed (may happen): %s.",
                str(ex)
            )

        time.sleep(0.001)
        if self._interpreter.isalive():
            who = tohuman(
                self.language
                if hasattr(self, 'language') and self.language else self
            )
            clog().warn(
                "Incomplete '%s' Runner shutdown: too slow and it is still running.",
                who
            )

    @profile
    def _exec_and_wait(self, source, options, *, from_example=None, **kargs):
        if from_example is None:
            input_list = kargs.get('input_list', [])
        else:
            input_list = kargs.get('input_list', from_example.input_list)

        timeout = kargs.get('timeout', options['timeout'])

        # get a copy: _expect_prompt_or_type will modify this in-place
        input_list = list(input_list)

        countdown = Countdown(timeout)
        lines = source.split('\n')

        self._last_num_lines_sent = 0
        for line in lines[:-1]:
            with profile_ctx("sendline"):
                self._sendline(line)
                self._last_num_lines_sent += 1
            self._expect_prompt_or_type(
                options, countdown, input_list=input_list
            )

        with profile_ctx("sendline"):
            self._sendline(lines[-1])
            self._last_num_lines_sent += 1

        self._expect_prompt_or_type(
            options, countdown, prompt_re=self._PS1_re, input_list=input_list
        )
        self._expect_delayed_output(options)

        if input_list:
            s = short_string(input_list[0][-1])
            if len(input_list) > 1:
                msg = "Some inputs were not typed: [%s] and %i more."
                args = (s, len(input_list) - 1)
            else:
                msg = "The last input was not typed: [%s]."
                args = (s, )

            clog().warn(msg, *args)

        return self._get_output(options)

    @profile
    def _expect_delayed_output(self, options):
        ''' Some interpreters may output text *after* printing the prompt.
            This method is called to do a last output recollection before
            processing the output and returning it to the user.
            '''
        timeout = options['x']['delayafterprompt']
        if not timeout:
            return

        expect = [pexpect.TIMEOUT, pexpect.EOF]
        Timeout, EOF = range(len(expect))

        what = self._interpreter.expect(expect, timeout=timeout)

        output = self._interpreter.before
        self._add_output(output)

        if what == EOF:
            self._interpreter_closed_unexpectedly_error(options)

    def _create_terminal(self, options):
        rows, cols = options['geometry']

        self._screen = Screen(cols, rows)
        self._stream = Stream(self._screen)

    @contextlib.contextmanager
    def _change_terminal_geometry_ctx(self, options, force=False):
        ''' Context manager to change the terminal geometry temporally.

            Change to the new (rows, cols) and restore it back to the
            default (read from options).

            Nothing is changed if (rows, cols) is equal to the default
            geometry unless you set force=True.

            Override/extend the method _change_terminal_geometry to customize
            what's to be done upon each window change.
            '''
        rows, cols = options['geometry']
        need_change = (
            self._terminal_default_geometry != (rows, cols) or force
        )
        if need_change:
            self._change_terminal_geometry(rows, cols, options)
            try:
                yield
            finally:
                rows, cols = self._terminal_default_geometry
                self._change_terminal_geometry(rows, cols, options)
        else:
            yield

    def _change_terminal_geometry(self, rows, cols, options):
        ''' Change the interpreter geometry or window size.

            By default just send a SIGWINCH signal but you may want to
            extend this with more things.
            '''
        self._screen.resize(rows, cols)
        self._setwindowsize(rows, cols)

    UNIV_NL = re.compile('\r\n|\r')

    @staticmethod
    def _universal_new_lines(out):
        return re.compile(PexpectMixin.UNIV_NL).sub('\n', out)

    def _emulate_ansi_terminal(self, chunks, join=True):
        for chunk in chunks:
            self._stream.feed(chunk)

        lines = self._screen.display
        self._screen.reset()
        lines = (line.rstrip() for line in lines)

        return '\n'.join(lines) if join else lines

    def _emulate_dumb_terminal(self, chunks):
        chunks = (self._universal_new_lines(chunk) for chunk in chunks)
        chunks = (chunk.expandtabs(8) for chunk in chunks)

        # remove trailing space from each line
        lines_group = (chunk.split('\n') for chunk in chunks)
        chunks = (
            '\n'.join(l.rstrip() for l in lines) for lines in lines_group
        )

        return ''.join(chunks)

    def _emulate_as_is_terminal(self, chunks):
        return ''.join((self._universal_new_lines(chunk) for chunk in chunks))

    @profile
    def _expect_prompt_or_type(
        self, options, countdown, prompt_re=None, input_list=[]
    ):
        assert isinstance(input_list, list)

        i = 0
        prompt_found = False
        while i < len(input_list):
            prefix, prefix_regex, input = input_list[i]

            # the regex may contain "escaped" newlines (\n) while
            # the runner may output any form of end line like
            # \n, \r and \r\n. In order to match any of those
            # we replace the literal "escaped" \n with a regex
            prefix_regex = prefix_regex.replace('\\\n', r'(?:\r\n|\n|\r)')
            try:
                prompt_found = self._expect_prompt(
                    options, countdown, prompt_re, earlier_re=prefix_regex
                )
            except TimeoutException as ex:
                raise InputPrefixNotFound(prefix, input, ex)

            if prompt_found:
                break

            # Add the prefix (output coming from the interpreter) and
            # the [ <input> ] that we typed in. This is a sort of
            # echo-emulation (TODO: some interpreters have echo activated,
            # should this be necessary?)
            chunk = "{}[{}]\n".format(self._interpreter.match.group(), input)
            self._output_between_prompts[-1] += chunk
            assert self._last_output_may_be_incomplete

            self._sendline(input)
            self._last_num_lines_sent += 1
            i += 1

        # remove in-place the inputs that were typed
        del input_list[:i]

        if not prompt_found:
            self._expect_prompt(options, countdown, prompt_re)

    @profile
    def _expect_prompt(
        self, options, countdown, prompt_re=None, earlier_re=None
    ):
        ''' Wait for a <prompt_re> (any self._any_PS_re if <prompt_re> is None)
            and raise a timeout if we cannot find one.

            If <earlier_re> is given, wait it along with the prompt: if it
            is found before the prompt, _expect_prompt will return False,
            otherwise will return True (or raise an exception if a timeout
            happens)

            During the waiting, collect the 'before' output into
            self._output_between_prompts
        '''
        if countdown == None:
            countdown = Countdown(options['timeout'])

        if not isinstance(countdown, Countdown):
            raise TypeError(
                "Invalid object for countdown: %s" % type(countdown)
            )

        # timeout of 0 or negative means do not wait, just do a single read and return back
        timeout = countdown.left()
        assert timeout >= 0

        if not prompt_re:
            prompt_re = self._any_PS_re

        # Note: earlier_re must be the last item of the list (see below why)
        expect = [prompt_re, pexpect.TIMEOUT, pexpect.EOF, earlier_re]
        PS_found, Timeout, EOF, Earlier = range(len(expect))

        # remove it if it was actually None (adding it before and
        # removing it now is weird but it makes the code easier and shorter)
        if earlier_re is None:
            del expect[-1]

        expect_kinds = (PS_found, Timeout, EOF, Earlier)

        countdown.start()
        what, output = self._expect_and_read(expect, timeout, expect_kinds)
        countdown.stop()

        self._add_output(output)

        if what == Timeout:
            msg = "Prompt not found: the code is taking too long to finish or there is a syntax error.\n\nLast 1000 bytes read:\n%s"
            msg = msg % ''.join(self._output_between_prompts)[-1000:]
            out = self._get_output(options)
            raise TimeoutException(msg, out)

        elif what == Earlier:
            self._last_output_may_be_incomplete = True
            return False

        elif what == EOF:
            self._interpreter_closed_unexpectedly_error(options)

        assert what == PS_found
        self._last_output_may_be_incomplete = False
        return True

    def _interpreter_closed_unexpectedly_error(self, options):
        msg = "Interpreter closed unexpectedly.\nThis could happen because the example triggered a close/shutdown/exit action,\nthe interpreter was killed by someone else or because the interpreter just crashed.\n\nLast 1000 bytes read:\n%s"
        msg = msg % ''.join(self._output_between_prompts)[-1000:]
        out = self._get_output(options)
        raise InterpreterClosedUnexpectedly(msg, out)

    def _add_output(self, output):
        ''' Add the given output to the output between prompts.

            If _last_output_may_be_incomplete is set, assume that the lastest
            output was incomplete and the given output is a continuation
            of it (like part of the same line).

            Otherwise assume that it is a new chunk/line.
            '''
        if self._last_output_may_be_incomplete:
            self._output_between_prompts[-1] += output
        else:
            self._output_between_prompts.append(output)

    @profile
    def _expect_and_read(self, expect_list, timeout, expect_kinds):
        ''' Interact with the Pexpect instance, expect one of the expect
            list and return what kind of the expected was satisfied
            having a limited in time.

            Returns the kind and the interpreter's collected output
            obtained so far.

            This method and its arguments have a very tight dependency
            with _expect_prompt so it is not 'stable'. Subclasses may override
            this as the last resort if they have to.

            This is a low-level hook with no backward-compatibility guarantees.
            '''
        what = self._interpreter.expect(expect_list, timeout=timeout)
        return what, self._interpreter.before

    @profile
    def _get_output(self, options):
        if options['force_echo_filtering']:
            return self._get_output_echo_filtered(options)

        if options['term'] == 'dumb':
            out = self._emulate_dumb_terminal(self._output_between_prompts)
        elif options['term'] == 'ansi':
            out = self._emulate_ansi_terminal(self._output_between_prompts)
        elif options['term'] == 'as-is':
            out = self._emulate_as_is_terminal(self._output_between_prompts)
        else:
            raise TypeError(
                "Unknown terminal type '+term=%s'." % options['term']
            )

        self._drop_output()
        return out

    def _get_output_echo_filtered(self, options):
        lines = self._filter_echo(options, self._output_between_prompts)

        self._drop_output()
        return '\n'.join(lines)

    def _filter_echo(self, options, output_between_prompts):
        # If the interpreter doesn't disable the TTY's echo,
        # everything we type in it will be reflected in the output.
        # so this breaks badly self._get_output
        # Experimental feature, use this instead of _get_output

        # self._output_between_prompts is a list of strings found by pexpect
        # after returning of each pexpect.expect
        # in other words if we prefix each line with the prompt
        # should get the original output from the process
        cookie = '[byexamplecookie]$'
        lines = (cookie + ' ' + line for line in output_between_prompts)

        # now, feed those lines to our ANSI Terminal emulator
        lines = self._emulate_ansi_terminal(lines, join=False)

        # get each line in the Terminal's display and ignore each one that
        # starts with our cookie: those are the "echo" lines that
        # *we* sent to the interpreter and they are not part of *its* output.
        filtered_lines = (
            line for line in lines if not line.startswith(cookie)
        )

        # a prompt may be at the end of the last line if the interpreter printed
        # something without adding a newline to separate it from the prompt.
        # for simplicity I will remove any prompt that it may be at
        # the end of all the lines:
        return (
            line[:-len(cookie)] if line.endswith(cookie) else line
            for line in filtered_lines
        )

    def _set_cooked_mode(self, state):  # pragma: no cover
        # code borrowed from ptyprocess/ptyprocess.py, _setecho, and
        # adapted adding more flags to it based in stty(1)
        errmsg = '_set_cooked_mode() may not be called on this platform'

        fd = self._interpreter.child_fd
        import termios
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

        output_flags = ('OPOST', )

        local_flags = (
            'ECHO',
            'ISIG',
            'ICANON',
        )

        if state:
            attr[0] |= reduce(
                operator.or_,
                [getattr(termios, flag_name) for flag_name in input_flags]
            )
            attr[1] |= reduce(
                operator.or_,
                [getattr(termios, flag_name) for flag_name in output_flags]
            )
            attr[3] |= reduce(
                operator.or_,
                [getattr(termios, flag_name) for flag_name in local_flags]
            )
        else:
            attr[0] &= reduce(
                operator.and_,
                [~getattr(termios, flag_name) for flag_name in input_flags]
            )
            attr[1] &= reduce(
                operator.and_,
                [~getattr(termios, flag_name) for flag_name in output_flags]
            )
            attr[3] &= reduce(
                operator.and_,
                [~getattr(termios, flag_name) for flag_name in local_flags]
            )

        try:
            termios.tcsetattr(fd, termios.TCSANOW, attr)
        except IOError as err:
            if err.args[0] == errno.EINVAL:
                raise IOError(err.args[0], '%s: %s.' % (err.args[1], errmsg))
            raise

    def _abort(self, example, options):
        self._sendcontrol('c')
        return self._recover_prompt_sync(example, options)

    def _recover_prompt_sync(self, example, options, cnt=5):
        ''' Expect for at least one prompt, return False if we
            didn't find one in a reasonable time (dfl_timeout).

            If we found one, keep reading up to find less than
            <cnt> additional prompts.

            If we found <cnt>, we fail too and return False.

            In other case, return sucess True.

            The idea is that if we lost the synchronization with
            the interpreter we may recover it reading at least
            one prompt (the interpreter is still alive) and
            less than <cnt> prompts (so we are at the 'end').

            This algorithm is not bug-free, just a best-effort one.
            '''
        err_msg = "Interpreter closed unexpectedly during the recovering. May be it is timming issue. Try to increase the timeout for the example."
        try:
            # wait for the prompt, ignore any extra output
            self._expect_prompt(
                options,
                countdown=Countdown(options['x']['dfl_timeout']),
                prompt_re=self._PS1_re
            )
            self._drop_output()
            good = True
        except TimeoutException as ex:
            self._drop_output()
            good = False
        except InterpreterClosedUnexpectedly:
            clog().warn(err_msg)
            good = False

        if good:
            try:
                cnt = 0
                while cnt < 5:
                    # "consume" spurious prompts until we know that we are
                    # in 'sync' with the interpreter (no more prompts
                    # are without be read)
                    self._expect_prompt(
                        options,
                        countdown=Countdown(options['x']['dfl_timeout']),
                        prompt_re=self._PS1_re
                    )
                    self._drop_output()
                    cnt += 1

                good = False  # we cannot ensure that we are in sync
            except TimeoutException as ex:
                self._drop_output()
            except InterpreterClosedUnexpectedly:
                clog().warn(err_msg)
                good = False

        return good
