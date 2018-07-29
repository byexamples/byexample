import traceback, time, os, sys
from byexample.common import colored, highlight_syntax
from byexample.concern import Concern
from doctest import _indent

stability = 'unstable'

try:
    from tqdm import tqdm
    if os.environ.get('BYEXAMPLE_PROGRESS_ASCII'):
        raise ImportError() # fake error

except ImportError:
    class tqdm(object):
        def __init__(self, file, *args, **kargs):
            self.file = file

        def write(self, msg, file, end):
            file.write(msg)
            if end:
                file.write(end)

            file.flush()

        def set_postfix_str(self, msg):
            pass

        def update(self, n):
            self.file.write('.' * n)
            self.file.flush()

        def close(self):
            # do not close the output file
            self.file.flush()

class SimpleReporter(Concern):
    target = None # progress

    def __init__(self, verbosity, encoding, **unused):
        if 'use_progress_bar' in unused and unused['use_progress_bar']:
            self.target = None # disable ourselves
        else:
            self.target = 'progress'

        self.output = unused['output']
        self.use_colors = unused['use_colors']
        self.verbosity = verbosity

    def _write(self, msg):
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

    def finish(self, failed, user_aborted, crashed, broken):
        if self.num_examples == 0:
            if self.verbosity >= 1:
                self._write("File %s, no test found\n" % self.filepath)
            return

        self._write('\n')

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
        if user_aborted or crashed or broken:
            status_str = colored("[ABORT]", 'red', self.use_colors)
        elif failed:
            status_str = colored("[FAIL]", 'red', self.use_colors)
        else:
            status_str = colored("[PASS]", 'green', self.use_colors)

        msg = "File %s, %i/%i test ran in %s\n%s Pass: %i Fail: %i Skip: %i\n" % (
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
        self._write('\n')
        self._write("Starting interactive session.\n")
        self._write("Escape character is '^]'.\n")


    def user_aborted(self, example):
        self._write('\n')

        msg = 'Execution aborted by the user at example %i of %i.\n' % (
                                    self.examplenro, self.num_examples)
        self._print_error_header(example)
        self._write(msg)

    def crashed(self, example, exception):
        self._write('\n')

        tb = ''.join(traceback.format_tb(self._get_traceback(exception)))
        ex = '%s: %s' % (str(exception.__class__.__name__), str(exception))
        msg = 'Execution of example %i of %i crashed.\n%s\n%s\n' % (
                                    self.examplenro, self.num_examples,
                                    tb, ex)
        self._print_error_header(example)
        self._write(msg)

    def start_parse(self, example, options):
        self.current_parsing_example = example

    def finish_parse(self, example, options, exception):
        self.examplenro += 1

        if exception == None:
            return

        self._write('\n')

        ex = '%s: %s' % (str(exception.__class__.__name__), str(exception))
        if self.verbosity >= 1:
            tb = ''.join(traceback.format_tb(self._get_traceback(exception)))
            ex = '\n'.join([tb, ex])

        msg = 'Parse of example %i of %i failed.\n%s\n' % (
                                    self.examplenro, self.num_examples,
                                    ex)
        self._print_error_header(self.current_parsing_example)
        self._write(msg)

    def finish_interact(self, exception):
        if exception == None:
            return

        self._write('\n')

        ex = '%s: %s' % (str(exception.__class__.__name__), str(exception))
        if self.verbosity >= 1:
            tb = ''.join(traceback.format_tb(self._get_traceback(exception)))
            ex = '\n'.join([tb, ex])

        msg = 'Interactive session failed.\n%s\n' % (ex)
        self._write(msg)

    def success(self, example, got, differ):
        self._update(1)
        self.good += 1

    def failure(self, example, got, differ):
        self._update(1)
        self._write("\n")

        self._print_error_header(example)
        diff = differ.output_difference(example, got, self.current_merged_flags,
                                         self.use_colors)
        self._write(diff)
        self._write('\n')

        self.fail += 1

    def _print_error_header(self, example):
        filepath = example.filepath
        lineno = example.start_lineno

        self._write("*" * 70)

        msg = '\nFile "%s", line %i\n' % (filepath, lineno)
        self._write(msg)

        self._write("Failed example:\n")
        self._write(_indent(highlight_syntax(example, self.use_colors)))

    def _get_traceback(self, exception):
        if hasattr(exception, '__traceback__'):
            return exception.__traceback__
        else:
            return sys.exc_info()[2]

class ProgressBarReporter(SimpleReporter):
    target = None # progress

    def __init__(self, verbosity, encoding, **unused):
        SimpleReporter.__init__(self, verbosity, encoding, **unused)
        if 'use_progress_bar' in unused and not unused['use_progress_bar']:
            self.target = None # disable ourselves
        else:
            self.target = 'progress'

    def _write(self, msg):
        self.bar.write(msg, file=self.output, end="")
        self.output.flush()

    def _update(self, x):
        self.bar.update(x)

    def start(self, examples, runners, filepath):
        SimpleReporter.start(self, examples, runners, filepath)

        bar_format = '{desc} |{bar}| [{n_fmt}/{total_fmt}{postfix}]'
        self.bar = tqdm(total=len(examples), file=self.output,
                             desc=filepath, leave=False,
                             bar_format=bar_format,
                             disable=None # means disable if the output is not TTY
                             )

    def finish(self, failed, user_aborted, crashed, broken):
        self.bar.close()
        SimpleReporter.finish(self, failed, user_aborted, crashed, broken)

    def start_example(self, example, options):
        SimpleReporter.start_example(self, example, options)
        self.bar.set_postfix_str('line %i' % example.start_lineno)

    def skip_example(self, example, options):
        SimpleReporter.skip_example(self, example, options)
        self._update(1)

