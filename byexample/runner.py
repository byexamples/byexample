from .common import log, build_exception_msg, colored
import string, re, difflib

class TimeoutException(Exception):
    pass

class ExampleRunner(object):
    def __init__(self, reporter, checker, verbosity=0):
        self.reporter  = reporter
        self.checker   = checker
        self.verbosity = verbosity

    def initialize_interpreters(self, interpreters):
        log("Initializing %i interpreters..." % len(interpreters),
                                                    self.verbosity-1)
        for interpreter in interpreters:
            log("* %s" % str(interpreter), self.verbosity-1)
            interpreter.initialize()

    def shutdown_interpreters(self, interpreters):
        log("Shutting down %i interpreters..." % len(interpreters),
                                                    self.verbosity-1)
        for interpreter in interpreters:
            log("* %s" % str(interpreter), self.verbosity-1)
            interpreter.shutdown()

    def run(self, examples, options, filepath):
        interpreters = list(set(e.interpreter for e in examples))

        self.initialize_interpreters(interpreters)
        self.reporter.start_run(examples, interpreters, filepath)

        fail_fast = options['FAIL_FAST']

        failed = False
        user_aborted = False
        crashed = False
        timedout = False
        for example in examples:
            options.up(example.options)
            try:
                if options['SKIP']:
                    self.reporter.skip_example(example, options)
                    continue

                self.reporter.start_example(example, options)
                try:
                    got = example.interpreter.run(example, options)
                except TimeoutException as e:  # pragma: no cover
                    got = "**Execution timed out**\n" + str(e)
                    timedout = True
                except KeyboardInterrupt:      # pragma: no cover
                    self.reporter.user_aborted(example)
                    user_aborted = True
                except Exception as e:         # pragma: no cover
                    self.reporter.crashed(example, e)
                    crashed = True

                if user_aborted or crashed:    # pragma: no cover
                    failed = True
                    break # always fail fast if the user aborted or code crashed

                # We can pass the test regardless of the output
                # however, a Timeout is always a fail
                force_pass = options['PASS']
                if not timedout and \
                        (force_pass or self.checker.check_output(example, got, options)):
                    self.reporter.success(example, got, self.checker)
                else:
                    self.reporter.failure(example, got, self.checker)
                    failed = True

                    # fail fast if the user want this or
                    # if we got a Timeout
                    if fail_fast or timedout:
                        break
            finally:
                options.down()

        self.reporter.end_run(examples, interpreters)
        self.shutdown_interpreters(interpreters)

        return failed, (user_aborted or crashed)

class Checker(object):
    def check_output(self, example, got, flags):
        return example.expected_re.match(got) is not None

    def output_difference(self, example, got, flags, use_colors):
        r'''
        Return a string with the differences between the example's expected
        output and the found or got.

        Depending of the flags the diff can be returned differently.
            >>> from byexample.runner import Checker
            >>> output_difference = Checker().output_difference

            >>> expected = 'one\ntwo\nthree\nfour'
            >>> got      = 'zero\none\ntree\nfour'

            >>> flags = {k: False for k in ('H', 'UDIFF', 'NDIFF', 'CDIFF')}
            >>> print(output_difference(expected, got, flags, False))
            Expected:
            one
            two
            three
            four
            Got:
            zero
            one
            tree
            four
            <blankline>

            >>> flags['UDIFF'] = True
            >>> print(output_difference(expected, got, flags, False))
            Differences:
            @@ -1,4 +1,4 @@
            +zero
             one
            -two
            -three
            +tree
             four
            <blankline>

            >>> flags['UDIFF'] = False
            >>> flags['NDIFF'] = True
            >>> print(output_difference(expected, got, flags, False))
            Differences:
            + zero
              one
            - two
            - three
            ?  -
            <a-blank-line>
            + tree
              four
            <a-blank-line>

            >>> flags['NDIFF'] = False
            >>> flags['CDIFF'] = True
            >>> print(output_difference(expected, got, flags, False))
            Differences:
            *** 1,4 ****
              one
            ! two
            ! three
              four
            --- 1,4 ----
            + zero
              one
            ! tree
              four
            <blankline>

            >>> expected = 'one\ntwo  \n\n\tthree'
            >>> got      = 'one  \ntwo\n\n    three'

            >>> flags['CDIFF'] = False
            >>> flags['H'] = True
            >>> print(output_difference(expected, got, flags, False))
            Notes:
                <blankline>: a blank line
                $: trailing spaces  ?: non-printable    ^t: tab
                ^v: vertical tab   ^r: carriage return  ^f: form feed
            Expected:
            one
            two$$
            <blankline>
            ^tthree
            Got:
            one$$
            two
            <blankline>
                three
            <a-real-blankline>

        '''

        expected = getattr(example, 'expected', example)
        self._diff = []

        if got.endswith('\n'):
            got = got[:-1]

        if flags['H']:
            self._write("Notes:\n%s" % self.HUMAN_EXPL)
            expected, got = self._human(expected), self._human(got)

        if flags['UDIFF']:
            diff_type = 'unified'
        elif flags['NDIFF']:
            diff_type = 'ndiff'
        elif flags['CDIFF']:
            diff_type = 'context'
        else:
            diff_type = None

        if diff_type:
            self.print_diff(expected, got, diff_type, use_colors)
        else:
            self.just_print(expected, got, use_colors)

        return ''.join(self._diff)

    def _write(self, s, end_with_newline=True):
        self._diff.append(s)
        if end_with_newline and not s.endswith('\n'):
            self._diff.append('\n')

    HUMAN_EXPL  = "    <blankline>: a blank line\n" + \
                  "    $: trailing spaces  ?: non-printable    ^t: tab\n" + \
                  "    ^v: vertical tab   ^r: carriage return  ^f: form feed"

    WS = re.compile(r"[ ]+$", flags=re.MULTILINE)

    def _human(self, s):
        ws      = '\t\x0b\x0c\r'
        tr_ws   = ['^t', '^v', '^f', '^r', '^s']

        # replace whitespace chars by the literal ^X except spaces
        for c, tr_c in zip(ws, tr_ws):
            s = s.replace(c, tr_c)

        # replace trailing spaces by something like "$"
        s = self.WS.sub(lambda m: '$' * (m.end(0) - m.start(0)), s)

        # any weird thing replace it by a '?'
        others = set(range(256)) - set(ord(c) for c in string.printable)
        tr = ''.join('?' if i in others else chr(i) for i in range(256))

        s = s.translate(tr)

        # replace empty line by '<blankline>'
        s = '\n'.join((l if l else '<blankline>') for l in s.split('\n'))
        return s

    def just_print(self, expected, got, use_colors):
        if expected:
            self._write(colored("Expected:", 'green', use_colors))
            self._write(expected)

        else:
            self._write(colored("Expected nothing", 'green', use_colors))

        if got:
            self._write(colored("Got:", 'red', use_colors))
            self._write(got)

        else:
            self._write(colored("Got nothing", 'red', use_colors))

    def print_diff(self, expected, got, diff_type, use_colors):
        expected_lines = expected.split('\n')
        got_lines = got.split('\n')

        if diff_type == 'unified':
            diff_lines = difflib.unified_diff(expected_lines, got_lines,
                                                n=2, lineterm="")
            diff_lines = list(diff_lines)
            diff_lines = diff_lines[2:] # drop diff's header
            diff_lines = self.colored_diff_lines(diff_lines, use_colors,
                                                         green='+', red='-',
                                                         yellow=['@'])

        elif diff_type == 'context':
            diff_lines = difflib.context_diff(expected_lines, got_lines,
                                                n=2, lineterm="")
            diff_lines = list(diff_lines)
            diff_lines = diff_lines[3:] # drop diff's header
            diff_lines = self.colored_diff_lines(diff_lines, use_colors,
                                                         green='+ ', red='! ',
                                                         yellow=['*', '-'])

        elif diff_type == 'ndiff':
            diff_lines = difflib.ndiff(expected_lines, got_lines,
                                        charjunk=difflib.IS_CHARACTER_JUNK)
            diff_lines = self.colored_diff_lines(diff_lines, use_colors,
                                                         green='+ ', red='- ',
                                                         yellow=[])
        else:
            raise ValueError("Unknow diff report type '%s'" % diff_type)

        self._write("Differences:")
        self._write('\n'.join(diff_lines))

    def colored_diff_lines(self, lines, use_colors, green, red, yellow):
        def colored_line(line):
            if line.startswith(green):
                return colored(line, 'green', use_colors)
            if line.startswith(red):
                return colored(line, 'red', use_colors)

            for t in yellow:
                if line.startswith(t) and t is not None:
                    return colored(line, 'yellow', use_colors)

            return line

        return [colored_line(line) for line in lines]

