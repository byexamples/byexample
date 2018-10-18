import traceback, time, os, sys, multiprocessing
from byexample.common import colored, highlight_syntax
from byexample.concern import Concern
from doctest import _indent

try:
    from tqdm import tqdm
    progress_bar_available = True
except ImportError:
    progress_bar_available = False

stability = 'unstable'

class _DummyLock(object):
    def __enter__(self):
        return
    def __exit__(self, *args):
        pass

    def acquire(self, *args, **kargs):
        pass

    def release(self, *args, **kargs):
        pass

class SimpleReporter(Concern):
    target = None # progress

    def __init__(self, verbosity, encoding, jobs, **unused):
        if 'use_progress_bar' in unused and unused['use_progress_bar'] \
                and progress_bar_available:
            self.target = None # disable ourselves
        else:
            self.target = 'progress'

        self.output = unused['output']
        self.use_colors = unused['use_colors']
        self.verbosity = verbosity

        self.jobs = jobs
        if self.jobs != 1:
            self.write_lock = multiprocessing.RLock()
        else:
            self.write_lock = _DummyLock()

    def _write(self, msg):
        ''' Call me once and just once per concern's method '''
        with self.write_lock:
            self.output.write(msg)
            self.output.flush()

    def _update(self, x):
        pass

    def start(self, examples, runners, filepath):
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

        elapsed   = max(time.time() - self.begin, 0)
        if elapsed < 300:
            elapsed_str = "%0.2f seconds" % elapsed
        elif elapsed < 3600:
            elapsed_str = "%i minutes, %i seconds" % (elapsed / 60,
                                                      elapsed % 60)
        else:
            # if your examples run in terms of hours you may have
            # a real problem... I desire to you the best of the luck
            elapsed_str = "%i hours, %i minutes" % ( elapsed / 3600,
                                                    (elapsed % 3600) / 60)

        ran_number = self.examplenro
        tot_number = self.num_examples
        if user_aborted or crashed or broken or timedout:
            status_str = colored("[ABORT]", 'red', self.use_colors)
        elif failed:
            status_str = colored("[FAIL]", 'red', self.use_colors)
        else:
            status_str = colored("[PASS]", 'green', self.use_colors)

        msg += "File %s, %i/%i test ran in %s\n%s Pass: %i Fail: %i Skip: %i\n" % (
                    self.filepath,
                    ran_number, tot_number,
                    elapsed_str,
                    status_str,
                    self.good, self.fail, self.skipped)
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

    def _bullet(self, color):
        return colored("=>", color, self.use_colors)

    def timedout(self, example, exception):
        msg = '\n'
        msg += self._error_header(example)

        msg += '%s Execution timedout at example %i of %i.\n' % (
                                    self._bullet('red'),
                                    self.examplenro, self.num_examples)
        msg += 'This could be because the example just ran too slow (try add more time\n' + \
               'with +timeout=<n>) or the example is "syntactically incorrect" and\n' + \
               'the interpreter hang (may be you forgot a parenthesis or something like that?).\n'

        if exception.output:
            msg += 'This is the last output obtained:\n%s\n' % str(exception.output)

        self._write(msg)

    def user_aborted(self, example):
        msg = '\n'
        msg += self._error_header(example)

        msg += self._bullet('red') + ' '
        msg += 'Execution aborted by the user at example %i of %i.\n' % (
                                    self.examplenro, self.num_examples)
        self._write(msg)

    def crashed(self, example, exception):
        msg = '\n'
        msg += self._error_header(example)

        tb = ''.join(traceback.format_tb(self._get_traceback(exception)))
        ex = '%s: %s' % (str(exception.__class__.__name__), str(exception))
        msg += self._bullet('red') + ' '
        msg += 'Execution of example %i of %i crashed.\n%s\n%s\n' % (
                                    self.examplenro, self.num_examples,
                                    tb, ex)
        self._write(msg)

    def start_parse(self, example, options):
        self.current_parsing_example = example

    def finish_parse(self, example, options, exception):
        self.examplenro += 1

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
                                    self.examplenro, self.num_examples,
                                    ex)
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
        msg = "\n"

        msg += self._error_header(example)
        msg += differ.output_difference(example, got, self.current_merged_flags,
                                         self.use_colors)
        msg += '\n'
        self._write(msg)

        self.fail += 1

    def _error_header(self, example):
        filepath = example.filepath
        lineno = example.start_lineno

        msg = "*" * 70

        msg += '\nFile "%s", line %i\n' % (filepath, lineno)
        msg += "Failed example:\n"
        msg += _indent(highlight_syntax(example, self.use_colors))

        return msg

    def _get_traceback(self, exception):
        if hasattr(exception, '__traceback__'):
            return exception.__traceback__
        else:
            return sys.exc_info()[2]

class ProgressBarReporter(SimpleReporter):
    target = None # progress

    def __init__(self, verbosity, encoding, jobs, **unused):
        SimpleReporter.__init__(self, verbosity, encoding, jobs, **unused)
        if ('use_progress_bar' in unused and not unused['use_progress_bar']) \
                or not progress_bar_available:
            self.target = None # disable ourselves
        else:
            self.target = 'progress'

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

        for pos in range(1, self.jobs+1):
            self.bar.moveto(pos)
            self.bar.fp.write('\r' + (' ' * self.bar.ncols)) # clear printing spaces
            self.bar.fp.write('\r')  # place cursor back at the beginning of line
            self.bar.moveto(-pos)

    def _write(self, msg):
        with self.write_lock:
            self._clear_all_bars()
            self.bar.write(msg, file=self.output, end="")
            self.output.flush()

    def _update(self, x):
        self.bar.update(x)

    def start(self, examples, runners, filepath):
        if self.jobs == 1:
            position = None
        else:
            # use multiprocessing.Process' id (number) as the position
            # of its bar
            position = int(multiprocessing.current_process().name) + 1

        SimpleReporter.start(self, examples, runners, filepath)

        bar_format = '{desc} |{bar}| [{n_fmt}/{total_fmt}{postfix}]'
        self.bar = tqdm(total=len(examples), file=self.output,
                             desc=filepath, leave=False,
                             bar_format=bar_format,
                             position=position,
                             disable=None # means disable if the output is not TTY
                             )
        self.bar.set_lock(self.write_lock)

    def finish(self, failed, user_aborted, crashed, broken, timedout):
        SimpleReporter.finish(self, failed, user_aborted, crashed, broken, timedout)
        self.bar.close()

    def start_example(self, example, options):
        SimpleReporter.start_example(self, example, options)
        self.bar.set_postfix_str('line %i' % example.start_lineno)

    def skip_example(self, example, options):
        SimpleReporter.skip_example(self, example, options)
        self._update(1)

