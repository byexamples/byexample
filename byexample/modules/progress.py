from __future__ import unicode_literals
import traceback, time, os, sys
from byexample.executor import InputPrefixNotFound, InterpreterClosedUnexpectedly
from byexample.common import colored, highlight_syntax, indent, short_string
from byexample.concern import Concern

try:
    from tqdm import tqdm
    progress_bar_available = True
except ImportError:
    progress_bar_available = False

stability = 'provisional'


class SimpleReporter(Concern):
    def __init__(self, *, ns, sharer, **kargs):
        Concern.__init__(self, **kargs)
        if 'use_progress_bar' in self.cfg and self.cfg.use_progress_bar \
                and progress_bar_available:
            self.target = None  # disable ourselves
        else:
            self.target = 'progress'

        self.output = self.cfg.output
        self.use_colors = self.cfg.use_colors
        self.verbosity = self.cfg.verbosity

        self.jobs = self.cfg.jobs

        # Initialize once the write_lock the first time that
        # a SimpleReporter is created. Next SimpleReporter instances
        # will use the same write_lock
        if self.cfg.job_number == '__main__':
            ns.write_lock = sharer.RLock()

        self.write_lock = ns.write_lock
        self.header_printed = False

    def _write(self, msg, nl=False):
        ''' Call me once and just once per concern's method '''
        with self.write_lock:
            self.output.write(msg)
            if nl:
                self.output.write('\n')
            self.output.flush()

    def _update(self, x):
        pass

    def start(self, examples, runners, filepath, options):
        self.num_examples = len(examples)
        self.examplenro = 0
        self.filepath = filepath
        self.begin = time.time()

        self.fail = self.good = self.skipped = 0

    def finish(self, failed, user_aborted, crashed, broken, timedout):
        if self.num_examples == 0:
            if self.verbosity >= 1:
                self._write("File %s, no test found\n" % self.filepath)
            return

        msg = '\n'

        elapsed = max(time.time() - self.begin, 0)
        if elapsed < 300:
            elapsed_str = "%0.2f seconds" % elapsed
        elif elapsed < 3600:
            elapsed_str = "%i minutes, %i seconds" % (
                elapsed / 60, elapsed % 60
            )
        else:
            # if your examples run in terms of hours you may have
            # a real problem... I desire to you the best of the luck
            elapsed_str = "%i hours, %i minutes" % (
                elapsed / 3600, (elapsed % 3600) / 60
            )

        ran_number = self.examplenro
        tot_number = self.num_examples
        if user_aborted or crashed or broken or timedout:
            status_str = colored("[ABORT]", 'red', self.use_colors)
        elif failed:
            status_str = colored("[FAIL]", 'red', self.use_colors)
        else:
            status_str = colored("[PASS]", 'green', self.use_colors)

        msg += "File %s, %i/%i test ran in %s\n%s Pass: %i Fail: %i Skip: %i\n" % (
            self.filepath, ran_number, tot_number, elapsed_str, status_str,
            self.good, self.fail, self.skipped
        )
        self._write(msg)

    def skip_example(self, example, options):
        self.skipped += 1

    def start_example(self, example, options):
        self.current_merged_flags = options

    def start_interact(self, example, options):
        msg = '\n'
        msg += "Starting interactive session.\n"
        msg += "Escape character is '^]'.\n"
        self._write(msg)

    def _bullet(self, color, marker="=>"):
        return colored(marker, color, self.use_colors)

    def timedout(self, example, exception):
        self._update(1)
        msg = '\n'
        msg += self._error_header(example)

        msg += '%s Execution timedout at example %i of %i.\n' % (
            self._bullet('red'), self.examplenro, self.num_examples
        )
        msg += self._bullet('cyan', '-') + ' '
        msg += 'This could be because the example just ran too slow (try add more time\n' + \
               'with +timeout=<n>) or the example is "syntactically incorrect" and\n' + \
               'the interpreter hang (may be you forgot a parenthesis or something like that?).\n'

        if isinstance(exception, InputPrefixNotFound):
            input = short_string(exception.input)

            msg += self._bullet('cyan', '-') + ' '
            msg += ("This happen before typing '%s'.\n" % input) + \
                   "Perhaps the text before did not match what you expected?\n" + \
                   (exception.prefix) + '\n'

        exception_output = exception.output.rstrip()
        if exception_output:
            msg += self._bullet('cyan', '-') + ' '
            msg += 'This is the last output obtained:\n%s\n' % str(
                exception_output
            )

        exception_raw_output = exception.raw_output.rstrip()
        if self.verbosity >= 4 and exception_raw_output:
            msg += self._bullet('yellow', '-') + ' '
            msg += 'This is the last raw output obtained:\n%s\n' % str(
                exception_raw_output
            )

        for note in example.notes_on_failure:
            msg += self._bullet('yellow', '-') + ' ' + note + '\n'

        self._write(msg)
        self.fail += 1

    def aborted(self, example, by_the_user, options):
        msg = '\n'
        msg += self._error_header(example)

        msg += self._bullet('red') + ' '
        msg += 'Execution aborted '
        if by_the_user:
            msg += 'by the user '
        msg += 'at example %i of %i.\n' % (self.examplenro, self.num_examples)

        msg += self._bullet('cyan', '-') + ' '
        msg += 'Some resources may had not been cleaned.\n'
        self._write(msg)

    def crashed(self, example, exception):
        msg = '\n'
        msg += self._error_header(example)

        msg += self._bullet('red') + ' '
        msg += 'Execution of example %i of %i crashed.\n' % (
            self.examplenro, self.num_examples
        )

        if isinstance(exception, InterpreterClosedUnexpectedly):
            msg += self._bullet('cyan', '-') + ' '
            msg += 'Interpreter closed unexpectedly: the interpreter or runner closed unexpectedly.\n' + \
                   'This could happen because the example triggered a close/shutdown/exit action,\n' + \
                   'the interpreter was killed by someone else or because the interpreter just crashed.\n' + \
                   '\n' + \
                   'If the interpreter is just crashing, it may be possible to find a workaround,\n' + \
                   'you can open an issue at https://github.com/byexamples/byexample/issues\n'

            exception_output = exception.output.rstrip()
            if exception_output:
                msg += self._bullet('cyan', '-') + ' '
                msg += 'This is the last output obtained:\n%s\n' % str(
                    exception_output
                )

            exception_raw_output = exception.raw_output.rstrip()
            if self.verbosity >= 4 and exception_raw_output:
                msg += self._bullet('yellow', '-') + ' '
                msg += 'This is the last raw output obtained:\n%s\n' % str(
                    exception_raw_output
                )

        elif isinstance(exception, UnicodeDecodeError):
            msg += self._bullet('cyan', '-') + ' '
            msg += f'The output of the example could not be decoded as \'{exception.encoding}\'.\n'
            msg += f'The current setting is \'--encoding={self.cfg.encoding}:{self.cfg.enc_error_handler}\'.\n'
            msg += 'Try a different one with \'--encoding\' from the command line.\n'
            msg += 'If the encoding is correct, try to use a more relaxed error handler\n'
            msg += 'like \'replace\' or \'ignore\'.\n'
            msg += f'If it helps, this is the decoding error we got:\n{str(exception)}\n'

            if self.verbosity >= 3:
                tb = ''.join(
                    traceback.format_tb(self._get_traceback(exception))
                )
                ex = '%s: %s' % (
                    str(exception.__class__.__name__), str(exception)
                )
                msg += '%s\n%s\n' % (tb, ex)
        else:
            tb = ''.join(traceback.format_tb(self._get_traceback(exception)))
            ex = '%s: %s' % (str(exception.__class__.__name__), str(exception))

            msg += '%s\n%s\n' % (tb, ex)

        self._write(msg)

    def start_parse(self, example, options):
        self.header_printed = False
        self.current_parsing_example = example
        self.finish_parse_called = False

    def finish_parse(self, example, options, exception):
        if not self.finish_parse_called:
            self.examplenro += 1
            self.finish_parse_called = True

        if exception == None:
            return

        msg = '\n'
        msg += self._error_header(self.current_parsing_example)

        ex = '%s: %s' % (str(exception.__class__.__name__), str(exception))
        if self.verbosity >= 1:
            tb = ''.join(traceback.format_tb(self._get_traceback(exception)))
            ex = '\n'.join([tb, ex])

        msg += self._bullet('red') + ' '
        msg += 'Parse of example %i of %i failed.\n%s\n' % (
            self.examplenro, self.num_examples, ex
        )
        self._write(msg)

    def finish_interact(self, exception):
        if exception == None:
            return

        msg = '\n'

        ex = '%s: %s' % (str(exception.__class__.__name__), str(exception))
        if self.verbosity >= 1:
            tb = ''.join(traceback.format_tb(self._get_traceback(exception)))
            ex = '\n'.join([tb, ex])

        msg += self._bullet('red') + ' '
        msg += 'Interactive session failed.\n%s\n' % (ex)
        self._write(msg)

    def success(self, example, got, differ):
        self._update(1)
        self.good += 1

    def failure(self, example, got, differ):
        self._update(1)

        show_failures = example.current_options['show_failures']
        if show_failures != 'all' and self.fail >= show_failures:
            # increment the counter without doing anything else
            # we are effectively suppressing this and any further
            # failure
            self.fail += 1
            return

        msg = "\n"

        msg += self._error_header(example)
        msg += differ.output_difference(
            example, got, self.current_merged_flags, self.use_colors
        )
        msg += '\n'

        for note in example.notes_on_failure:
            msg += self._bullet('yellow', '-') + ' ' + note + '\n'

        self._write(msg)

        self.fail += 1

    def event(self, what, **data):
        if what != 'log':
            return

        self._write(data['msg'], nl=True)

    def _error_header(self, example):
        if self.header_printed:
            return ''

        self.header_printed = True
        filepath = example.filepath
        lineno = example.start_lineno

        msg = "*" * 70

        msg += '\nFile "%s", line %i\n' % (filepath, lineno)
        msg += "Failed example:\n"

        msg += indent(highlight_syntax(example, self.use_colors))
        if not msg.endswith('\n'):
            msg += '\n'

        return msg

    def _get_traceback(self, exception):
        if hasattr(exception, '__traceback__'):
            return exception.__traceback__
        else:
            return sys.exc_info()[2]


class ProgressBarReporter(SimpleReporter):
    def __init__(self, **kargs):
        SimpleReporter.__init__(self, **kargs)
        if ('use_progress_bar' in self.cfg and not self.cfg.use_progress_bar) \
                or not progress_bar_available:
            self.target = None  # disable ourselves
        else:
            self.target = 'progress'

        if self.cfg.job_number == '__main__':
            # this write lock is shared among all the instances of tqdm
            tqdm.set_lock(self.write_lock)
        else:
            self.job_number = self.cfg.job_number

        # the tqdm bar will be created at the start of the examples
        self.bar = None

    def _clear_all_bars(self):
        ''' Based on tqdm.clear method '''
        # Notes:
        #  moveto(x)  moves x lines down (insert x new lines \n)
        #  moveto(-x) moves x lines up (insert x special char to go up)
        #       all moveto are relative to the current position
        #  ncols is the columns that the terminal has (assume that all the
        #       bars have the same size)
        if not hasattr(self.bar, 'fp'):
            return

        for pos in range(1, self.jobs + 1):
            self.bar.moveto(pos)
            self.bar.fp.write(
                '\r' + (' ' * self.bar.ncols)
            )  # clear printing spaces
            self.bar.fp.write(
                '\r'
            )  # place cursor back at the beginning of line
            self.bar.moveto(-pos)

    def _write(self, msg, nl=False):
        with self.write_lock:
            if self.bar is None:
                SimpleReporter._write(self, msg, nl)
            else:
                self._clear_all_bars()
                end = '\n' if nl else ''
                self.bar.write(msg, file=self.output, end=end)
                self.output.flush()

    def _update(self, x):
        self.bar.update(x)

    def start(self, examples, runners, filepath, options):
        if self.jobs == 1:
            position = None
        else:
            # use the job number as the position of this bar
            position = self.job_number + 1

        SimpleReporter.start(self, examples, runners, filepath, options)

        bar_format = '{desc} |{bar}| [{n_fmt}/{total_fmt}{postfix}]'
        self.bar = tqdm(
            total=len(examples),
            file=self.output,
            desc=filepath,
            leave=False,
            bar_format=bar_format,
            position=position,
            disable=None  # means disable if the output is not TTY
        )

    def finish(self, failed, user_aborted, crashed, broken, timedout):
        SimpleReporter.finish(
            self, failed, user_aborted, crashed, broken, timedout
        )
        self.bar.close()
        self.bar = None

    def start_example(self, example, options):
        SimpleReporter.start_example(self, example, options)
        self.bar.set_postfix_str('line %i' % example.start_lineno)

    def skip_example(self, example, options):
        SimpleReporter.skip_example(self, example, options)
        self._update(1)
