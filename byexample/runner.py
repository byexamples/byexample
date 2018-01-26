from .common import log, build_exception_msg, colored, print_example, print_execution
import string, re, difflib

class TimeoutException(Exception):
    pass

class ExampleRunner(object):
    def __init__(self, concerns, checker, verbosity, use_colors, **unused):
        self.concerns   = concerns
        self.checker    = checker
        self.use_colors = use_colors
        self.verbosity  = verbosity

    def initialize_interpreters(self, interpreters, examples, options):
        log("Initializing %i interpreters..." % len(interpreters),
                                                    self.verbosity-1)
        for interpreter in interpreters:
            log(" - %s" % str(interpreter), self.verbosity-1)
            interpreter.initialize(examples, options)

    def shutdown_interpreters(self, interpreters):
        log("Shutting down %i interpreters..." % len(interpreters),
                                                    self.verbosity-1)
        for interpreter in interpreters:
            log(" - %s" % str(interpreter), self.verbosity-1)
            interpreter.shutdown()

    def run(self, examples, options, filepath):
        interpreters = list(set(e.interpreter for e in examples))

        self.initialize_interpreters(interpreters, examples, options)
        self.concerns.start_run(examples, interpreters, filepath)

        fail_fast = options['FAIL_FAST']

        failed = False
        user_aborted = False
        crashed = False
        timedout = False
        for example in examples:
            options.up(example.options)
            try:
                if options['SKIP']:
                    self.concerns.skip_example(example, options)
                    continue

                print_example(example, True, self.verbosity-3)
                self.concerns.start_example(example, options)
                try:
                    got = example.interpreter.run(example, options)
                except TimeoutException as e:  # pragma: no cover
                    got = "**Execution timed out**\n" + str(e)
                    timedout = True
                except KeyboardInterrupt:      # pragma: no cover
                    self.concerns.user_aborted(example)
                    user_aborted = True
                except Exception as e:         # pragma: no cover
                    self.concerns.crashed(example, e)
                    crashed = True

                if user_aborted or crashed:    # pragma: no cover
                    failed = True
                    break # always fail fast if the user aborted or code crashed

                print_execution(example, got, self.verbosity-3)

                # We can pass the test regardless of the output
                # however, a Timeout is always a fail
                force_pass = options['PASS']
                if not timedout and \
                        (force_pass or self.checker.check_output(example, got, options)):
                    self.concerns.success(example, got, self.checker)
                else:
                    self.concerns.failure(example, got, self.checker)
                    failed = True

                    # start an interactive session if the example failes
                    # and the user wanted this
                    if options['INTERACT'] and not timedout:
                        self.concerns.start_interact(example, options)
                        ex = None
                        try:
                            example.interpreter.interact(example, options)
                        except Exception as e:
                            ex = e

                        self.concerns.finish_interact(ex)

                    # fail fast if the user want this or
                    # if we got a Timeout
                    if fail_fast or timedout:
                        break
            finally:
                options.down()

        self.concerns.end_run(failed, user_aborted, crashed)
        self.shutdown_interpreters(interpreters)

        return failed, (user_aborted or crashed)

class Checker(object):
    def __init__(self, verbosity, **unused):
        self._diff = []
        self.verbosity = verbosity

    def check_output(self, example, got, flags):
        m = re.compile(''.join(example.expected.regexs), re.MULTILINE | re.DOTALL)
        return m.match(got) is not None

    def output_difference(self, example, got, flags, use_colors):
        r'''
        Return a string with the differences between the example's expected
        output and the found or got.

        Depending of the flags the diff can be returned differently.
            >>> from byexample.runner import Checker
            >>> output_difference = Checker(verbosity=0).output_difference

            >>> expected = 'one\ntwo\nthree\nfour'
            >>> got      = 'zero\none\ntree\nfour'

            >>> flags = dict((k, False) for k in ('ENHANCE_DIFF', 'UDIFF', 'NDIFF', 'CDIFF'))
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

            >>> flags['UDIFF'] = False
            >>> flags['NDIFF'] = True
            >>> print(output_difference(expected, got, flags, False))
            Differences:
            + zero
              one
            - two
            - three
            ?  -
            <blankline>
            + tree
              four

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

            >>> expected = 'one\ntwo  \n\n\tthree'
            >>> got      = 'one  \ntwo\n\n    three'

            >>> flags['CDIFF'] = False
            >>> flags['ENHANCE_DIFF'] = True
            >>> print(output_difference(expected, got, flags, False))
            Nothing captured.
            Notes:
                $: trailing spaces
                ^n: a blank line    ?: non-printable    ^t: tab
                ^v: vertical tab   ^r: carriage return  ^f: form feed
            Expected:
            one
            two$$
            ^n
            ^tthree
            Got:
            one$$
            two
            ^n
                three

        '''

        # delete any previous diff
        del self._diff

        # the example may have *named* capture tags like <foo>
        # if possible, we will save what we captured from the got here
        replaced_captures = {}

        # get the expected string, and if it is possible (and the
        # user allows this), try to get the captured strings
        if hasattr(example, 'expected'):
            expected = example.expected.str

            if flags['ENHANCE_DIFF']:
                expected, replaced_captures = self._replace_captures(
                                                example.expected.regexs,
                                                example.expected.positions,
                                                example.expected.rcounts,
                                                expected, got)

        else:
            expected = example # aka literal string, mostly for internal testing

        self._diff = []

        # remove the last empty lines. this should improve the
        # diff when the algorithm is none (just_print)
        # it should be safe too because expected_regexs should have
        # a '\n*' regex at the end to match any possible empty line
        expected = self._remove_last_empty_lines(expected)
        got      = self._remove_last_empty_lines(got)

        if flags['ENHANCE_DIFF']:
            self._print_named_captures(replaced_captures)
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

    def _print_named_captures(self, replaced_captures):
        if not replaced_captures:
            pass

        max_len = 36
        def _format(k, v):
            if k is None or v is None:
                return ""

            _mlen = max_len - len(k) + 2 # plus the : and the space

            # remove any newline and replace them by a ^n
            v = self.NLs.sub('^n', v)

            v = self._human(v)
            if len(v) > _mlen:
                _mlen -= 5 # minus the ' ... '
                v = v[:_mlen/2] + " ... " + v[-_mlen/2:]


            return "%s: %s" % (k, v)

        k_vs = list(replaced_captures.items())
        if not k_vs:
            self._write("Nothing captured.")
            return

        self._write("Captured:\n")

        if len(k_vs) % 2 != 0:
            k_vs.append((None, None)) # make the list even

        for k_v1, k_v2 in zip(k_vs[::2], k_vs[1::2]):
            left, right = _format(*k_v1), _format(*k_v2)

            space_between = max(max_len - len(left), 1)
            self._write("    %s%s%s" % (left, " " * space_between, right))


    def _replace_captures(self, expected_regexs, positions, rcounts, expected, got, min_rcount=6):
        r'''
        Try to replace all the capture groups in the expected by
        the strings found in got.

        The idea is to have the expected and the got as much similar as
        possible making further diffs easier.

            >>> from byexample.runner import Checker
            >>> from functools import partial
            >>> _replace_captures = Checker(verbosity=0)._replace_captures

        We can only "safely" replace all the groups at the begin (left) of the
        string before the first difference and replace all the groups at the
        end (right) after the last difference.

            >>> expected = r'aa<...>bb<...>ddd<...>eee<...>cc'
            >>> got = r'aaAAbbBBxxxddeeeCCcc'

            >>> expected_regexs = ['\A', 'aa', '(.*?)', 'bb', '(.*?)', 'ddd',
            ...                    '(.*?)', 'eee', '(.*?)', 'cc', r'\n*\Z']
            >>> positions = [0, 0, 2, 7, 9, 14, 17, 22, 25, 30, 32]
            >>> rcounts   = [0, 2, 0, 2, 0, 3, 0, 3, 0, 2, 0]

            >>> s, c = _replace_captures(expected_regexs, positions, rcounts, expected, got, min_rcount=1)

            >>> s                               # byexample: -CAPTURE
            'aaAAbb<...>ddd<...>eeeCCcc'

            >>> got = r'aaAAbBBxxxddeeeCCcc'
            >>> s, c = _replace_captures(expected_regexs, positions, rcounts, expected, got, min_rcount=1)

            >>> s                               # byexample: -CAPTURE
            'aa<...>bb<...>ddd<...>eeeCCcc'

        The definition of "safely" is a little weak. A capture tag may match
        anything so we could consider it as "safe" if after and before the
        capture we also match enough literals.

        This can be controlled with the min_rcount parameter (see Parser class)

            >>> expected = r'aa<...>bb<...>ddd<...>eee<...>cc'
            >>> got = r'aaAAbbBBxxxddeeeCCcc'

        A small value of min_rcount means that we don't need much literals after
        and before the capture.

            >>> s, c = _replace_captures(expected_regexs, positions, rcounts, expected, got, min_rcount=1)
            >>> s                               # byexample: -CAPTURE
            'aaAAbb<...>ddd<...>eeeCCcc'

            >>> s, c = _replace_captures(expected_regexs, positions, rcounts, expected, got, min_rcount=2)
            >>> s                               # byexample: -CAPTURE
            'aaAAbb<...>ddd<...>eeeCCcc'

        Notice how a value of 3 changes the result because the 'bb' literal,
        after the capture has only a rcount of 2

            >>> s, c = _replace_captures(expected_regexs, positions, rcounts, expected, got, min_rcount=3)
            >>> s                               # byexample: -CAPTURE
            'aa<...>bb<...>ddd<...>eeeCCcc'

        Named groups are returned as well:

            >>> expected = r'aa<foo>bb<bar>ddd<baz>eee<zaz>cc'
            >>> got = r'aaAAbbBBxxxddeeeCCcc'

            >>> expected_regexs = ['\A', 'aa', '(?P<foo>.*?)', 'bb',
            ...                     '(?P<bar>.*?)', 'ddd', '(?P<baz>.*?)',
            ...                     'eee', '(?P<zaz>.*?)', 'cc', r'\n*\Z']
            >>> positions = [0, 0, 2, 7, 9, 14, 17, 22, 25, 30, 32]
            >>> rcounts   = [0, 2, 0, 2, 0, 3, 0, 3, 0, 2, 0]

            >>> s, c = _replace_captures(expected_regexs, positions, rcounts, expected, got, min_rcount=1)
            >>> s                                                       # byexample: -CAPTURE
            'aaAAbb<bar>ddd<baz>eeeCCcc'
            >>> c
            {'foo': 'AA', 'zaz': 'CC'}

        '''

        regs = expected_regexs
        def _compile(regexs):
            return re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)

        assert len(regs) == len(positions) == len(rcounts)

        best_left_index = 0
        best_right_index = len(regs)-1

        # from left to right, find the left most regex that match
        # a prefix of got by doing an incremental compile/matching
        accum = 0
        for i in range(len(regs)):
            # a regex with 0 rcount doesn't count and worst,
            # reset our accumulator of consecutive non zero rcounts
            if rcounts[i] == 0:
                accum = 0
                continue

            accum += rcounts[i]

            m = _compile(regs[:i+1]).match(got)
            if m:
                log("Left to Right's best at index % 3i (accum rcount % 3i/%i):\nPartial left regex: %s\n% 4i: %s\n" % (
                    i, accum, min_rcount,
                    repr(''.join(regs[:i+1])),
                    positions[i], m.group(0)),
                    self.verbosity-4)

                if accum >= min_rcount:
                    best_left_index = i

        left_side = regs[:best_left_index+1]
        r = _compile(left_side)
        got_left = r.match(got).group(0)

        left_ends_at = positions[best_left_index+1]

        # a 'capture anything' regex between the left and the right side
        # to hold all the rest of the string
        buffer_re = '(?P<XXXX>.*?)'

        # now go from the right to the left, add a regex each time
        # to see where the whole regex doesn't match
        accum = 0
        for i in range(len(regs)-1, best_left_index, -1):
            try:
                if not rcounts[i]:
                    accum = 0
                    continue

                accum += rcounts[i]
                m = _compile(left_side + [buffer_re] + regs[i:]).match(got)
                if m:
                    log("Right to Left's best at index % 3i (accum rcount % 3i/%i):\nPartial whole regex: %s\n" % (
                        i, accum, min_rcount,
                        repr(''.join(left_side + [buffer_re] + regs[i:]))),
                        self.verbosity-4)

                    if accum >= min_rcount:
                        best_right_index = i

            except Exception as e:
                if 'unknown group' in str(e):
                    # the right side has a named group of the form (?P=xxx) to
                    # match the value of a previous matched group named xxx.
                    # but this group is not in the left side so this fails
                    # we continue moving from the right to the left as it is
                    # possible that the group xxx is in some place in the right
                    # side so this technically is not an error
                    pass
                else:
                    raise

        right_side = regs[best_right_index:]

        # because we are using a regex that match all the got string
        # the got_right is a substring of it: everything after the
        # buffer in the middle
        r = _compile(left_side + [buffer_re] + right_side)
        m = r.match(got)
        got_right = m.group(0)[m.end('XXXX'):]

        right_begin_at = positions[best_right_index]

        replaced_captures = m.groupdict()
        XXXX = replaced_captures.pop('XXXX')

        # we cannot keep replacing the capture tags... leave the
        # string as it is: this always was a best-effort algorithm
        middle_part = expected[left_ends_at:right_begin_at]

        log("Incremental Match:\n##Left: %s\n\n##Middle: %s\n\n##Right: %s\n\n##Captured: %s\n\nBuffer: %s" % (
                got_left, middle_part, got_right, repr(replaced_captures), XXXX), self.verbosity-4)

        return got_left + middle_part + got_right, replaced_captures

    def _write(self, s, end_with_newline=True):
        self._diff.append(s)
        if end_with_newline and not s.endswith('\n'):
            self._diff.append('\n')

    HUMAN_EXPL  = "    $: trailing spaces\n" + \
                  "    ^n: a blank line    ?: non-printable    ^t: tab\n" + \
                  "    ^v: vertical tab   ^r: carriage return  ^f: form feed"

    WS  = re.compile(r"[ ]+$", flags=re.MULTILINE)
    NLs = re.compile(r"\n+",   flags=re.MULTILINE)
    last_NLs = re.compile(r"\n+\Z", flags=re.MULTILINE)

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

        # replace empty line by '^n'
        s = '\n'.join((l if l else '^n') for l in s.split('\n'))
        return s

    def _remove_last_empty_lines(self, s):
        return self.last_NLs.sub('', s)

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

