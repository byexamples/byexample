import traceback, time
from .common import colored
from doctest import _indent

class SimpleReporter(object):
    def __init__(self, output, use_colors, quiet=False, verbosity=0):
        self.output = output
        self.use_colors = use_colors and output.isatty()
        self.quiet = quiet
        self.verbosity = verbosity

    def _write(self, msg):
        if self.quiet:
            return

        self.output.write(msg)
        self.output.flush()

    def start_run(self, examples, interpreters, filepath):
        self.num_examples = len(examples)
        self.examplenro = 0
        self.in_dot_line = True
        self.filepath = filepath
        self.begin = time.time()

        self.fail = self.good = self.aborted_or_crashed = self.skipped = 0

    def end_run(self, examples, interpreters):
        if not examples:
            if self.verbosity >= 1:
                self._write("File %s, no test found\n" % self.filepath)
            return

        if self.in_dot_line:
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
        tot_number = (self.num_examples - self.skipped)
        if ran_number == tot_number == self.good:
            status_str = colored("[PASS]", 'green', self.use_colors)
        else:
            status_str = colored("[FAIL]", 'red', self.use_colors)

        msg = "File %s, %i/%i test ran in %s\n%s Pass: %i Fail: %i Aborted: %i\n" % (
                    self.filepath,
                    ran_number, tot_number,
                    elapsed_str,
                    status_str,
                    self.good, self.fail, self.aborted_or_crashed)
        self._write(msg)

    def skip_example(self, example, options):
        self.skipped += 1

    def start_example(self, example, options):
        self.examplenro += 1
        self.current_merged_flags = options

    def user_aborted(self, example):
        if self.in_dot_line:  # pragma: no cover
            self._write('\n')
            self.in_dot_line = False

        msg = 'Execution aborted by the user at example %i of %i.\n' % (
                                    self.examplenro, self.num_examples)
        self._print_error_header(example)
        self._write(msg)
        self.aborted_or_crashed += 1

    def crashed(self, example, exception):
        if self.in_dot_line:  # pragma: no cover
            self._write('\n')
            self.in_dot_line = False

        msg = 'Execution of example %i of %i crashed.\n%s' % (
                                    self.examplenro, self.num_examples,
                                    traceback.format_exc(exception))
        self._print_error_header(example)
        self._write(msg)
        self.aborted_or_crashed += 1

    def success(self, example, got, checker):
        if not self.in_dot_line:  # pragma: no cover
            self._write('\n')
            self.in_dot_line = True

        self._write('.')

        self.good += 1

    def failure(self, example, got, checker):
        if not self.in_dot_line:  # pragma: no cover
            self._write('\n')
            self.in_dot_line = True

        self._write('F\n')

        self._print_error_header(example)
        diff = checker.output_difference(example, got, self.current_merged_flags,
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
        self._write(_indent(example.source))

