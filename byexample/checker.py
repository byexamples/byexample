from .common import log, colored
import string, re, difflib

class _LinearChecker(object):
    ''' Assume that all the example's tags are of the form .*
        Then we can just apply a quicker and more efficient algorithm
        to detect if example's expected matches or not the got string.

        >>> from byexample.parser import ExampleParser
        >>> from byexample.options import Options
        >>> parser = ExampleParser(0, 'utf8', None, Options()); parser.language = 'python'
        >>> parser.extract_options = lambda x: {'norm_ws': False, 'tags': True}

        >>> build_example = parser.build_example

        Consider the following example with a named capture in the expected:

        >>> ex = build_example('f()', 'aa<foo>bb<bar>cc', 0, None, None, (0, 1, 'file'))

        If <foo> is .* we can split the expected string into two: aa and bb; and
        check each of them in order from left to right without overlapping:

        >>> from byexample.checker import _LinearChecker
        >>> chk = _LinearChecker(0)

        >>> got = 'aaXYZbbcc'
        >>> chk.check_got_output(ex, got, 0)
        True

        Once we performed the check we can query the captured strings:

        >>> whole, captures = chk.get_captures(ex, got, 0)

        The whole string is the expected string with all of its capture tags
        replaced by the captured texts from the got string.

        Because the check passed we should have a copy of the got:

        >>> whole == got
        True

        The captures is a dictionary with the strings captures by name:

        >>> captures['foo'], captures['bar']
        ('XYZ', '')

        The things gets more interesting when the example fails.
        In this case the values returned by get_captures will be incomplete.

        >>> got = 'aaXYZccbb'
        >>> chk.check_got_output(ex, got, 0)
        False

        >>> whole, captures = chk.get_captures(ex, got, 0)

        In this case the whole string will have some tags replaced but others no
        in a best effort manner.

        >>> whole
        'aaXYZccbb<bar>cc'

        And the captures, obviously, will be incomplete too

        >>> captures['foo'], captures.get('bar')
        ('XYZcc', None)

        The algorithm works perfectly fine with unnamed captures

        >>> ex = build_example('f()', 'aa<...>bb<...>cc', 0, None, None, (0, 1, 'file'))

        >>> got = 'aaXYZbbcc'
        >>> chk.check_got_output(ex, got, 0)
        True

        >>> whole, captures = chk.get_captures(ex, got, 0)

        >>> whole == got
        True

        But nothing is captured of course (we keep the captured string of the
        named capture tags only)

        >>> captures
        {}

        The algorithm also takes into account what happen if the expected string
        starts or ends with a tag:

        >>> ex = build_example('f()', '<foo>bb<...>bb<bar>', 0, None, None, (0, 1, 'file'))

        >>> got = 'aabbxbbcc'
        >>> chk.check_got_output(ex, got, 0)
        True

        >>> chk.get_captures(ex, got, 0)
        ('aabbxbbcc', {'bar': 'cc', 'foo': 'aa'})

        Or if it has a single literal chunk

        >>> ex = build_example('f()', '<foo>bbbb<bar>', 0, None, None, (0, 1, 'file'))

        >>> got = 'aabbbbcc'
        >>> chk.check_got_output(ex, got, 0)
        True

        >>> chk.get_captures(ex, got, 0)
        ('aabbbbcc', {'bar': 'cc', 'foo': 'aa'})

        If it has a single tag

        >>> ex = build_example('f()', '<foo>', 0, None, None, (0, 1, 'file'))

        >>> got = 'bbbb'
        >>> chk.check_got_output(ex, got, 0)
        True

        >>> chk.get_captures(ex, got, 0)
        ('bbbb', {'foo': 'bbbb'})

        Or even if there is any tag at all:

        >>> ex = build_example('f()', 'bbbb', 0, None, None, (0, 1, 'file'))

        >>> got = 'bbbb'
        >>> chk.check_got_output(ex, got, 0)
        True

        >>> chk.get_captures(ex, got, 0)
        ('bbbb', {})


        We still need to use the regexs that represent the literal chunks
        as they may not be so 'literal'. Think for example that their regexs
        will be in charge of consume the whitespace if we ask for it

        >>> parser.extract_options = lambda x: {'norm_ws': True, 'tags': True}
        >>> ex = build_example('f()', '\n  <...>A \n\nB<...> C\n<...>', 0, None, None, (0, 1, 'file'))

        >>> got = ' A B  C '
        >>> chk.check_got_output(ex, got, 0)
        True

        >>> chk.get_captures(ex, got, 0)
        (' A B  C ', {})

        '''
    def __init__(self, verbosity, **unused):
        self.verbosity = verbosity
        self.check_good = False

    def check_got_output(self, example, got, flags):
        self.check_good = False

        regexs = example.expected.regexs
        tags_by_idx = example.expected.tags_by_idx
        expected_str = example.expected.str
        charnos = example.expected.charnos

        self._partial_expected_replaced = expected_str
        self._partial_captured = {}
        self.check_good = self._linear_matching(regexs, tags_by_idx, charnos, expected_str, got)
        return self.check_good

    def get_captures(self, example, got, flags):
        if self.check_good:
            return got, self._partial_captured
        else:
            return self._partial_expected_replaced, self._partial_captured

    def _linear_matching(self, regexs, tags_by_idx, charnos, expected_str, got):
        ''' Assume that all (if any) example's capture tags are regex
            of the form '.*'.
            If that's true, then the example will pass if all the literal
            regexs of the example's expected match the got strings.

            This is correct because the regex between the literal ones
            are capture tags and if we assume that those are .*, matching
            the literal regexs in order is like matching the whole thing
            with .* regexs in the middle.

            However this is a safer implementation that prevents pathological
            regexs

            For example matching 'aa.*bb.*cc' could be too expensive but
            matching ['aa', 'bb', 'cc'] is the same and faster.

            '''

        prev = 0
        literals = []
        capture_idxs = list(sorted(tags_by_idx.keys()))
        for capture_idx in capture_idxs + [len(regexs)]:
            literal = ''.join(regexs[prev:capture_idx])
            at = charnos[prev]
            if literal:
                literals.append((at, literal, tags_by_idx.get(prev-1)))

            prev = capture_idx + 1

        pos = 0
        for at, literal, prev_name in literals:
            r = re.compile(literal, re.MULTILINE | re.DOTALL)
            m = r.search(got, pos)

            if not m:
                self._partial_expected_replaced = got[:pos] + expected_str[at:]
                return False

            if prev_name is not None:
                captured = got[pos:m.start()]
                self._partial_captured[prev_name] = captured

            pos = m.end()

        self._partial_expected_replaced = got
        return True

class _RegexChecker(object):
    def __init__(self, verbosity, **unused):
        self.verbosity = verbosity
        self.check_good = False

    def check_got_output(self, example, got, flags):
        self.check_good = False
        self._captures_from_good_check = None

        r = re.compile(''.join(example.expected.regexs), re.MULTILINE | re.DOTALL)
        m = r.match(got)

        if m:
            self._captures_from_good_check = m.groupdict()
            self.check_good = True
            return True

        else:
            self.check_good = False
            return False

    def get_captures(self, example, got, flags):
        if self.check_good:
            return got, self._captures_from_good_check

        else:
            expected = example.expected
            return self._get_all_captures_as_possible(expected.captures,
                                          expected.regexs,
                                          expected.charnos,
                                          expected.rcounts,
                                          expected.str,
                                          got,
                                          min_rcount = 6)

    def _get_all_captures_as_possible(self, captures, expected_regexs, charnos, rcounts, expected, got, min_rcount=6):
        r'''
        Try to replace all the capture groups in the expected by
        the strings found in got.

        The idea is to have the expected and the got as much similar as
        possible making further diffs easier.

            >>> from byexample.checker import _RegexChecker
            >>> from functools import partial
            >>> _replace_captures = _RegexChecker(verbosity=0)._get_all_captures_as_possible

        We can only "safely" replace all the groups at the begin (left) of the
        string before the first difference and replace all the groups at the
        end (right) after the last difference.

            >>> expected = r'aa<...>bb<...>ddd<...>eee<...>cc'
            >>> got = r'aaAAbbBBxxxddeeeCCcc'

            >>> expected_regexs = ['\A', 'aa', '(.*?)', 'bb', '(.*?)', 'ddd',
            ...                    '(.*?)', 'eee', '(.*?)', 'cc', r'\n*\Z']
            >>> charnos = [0, 0, 2, 7, 9, 14, 17, 22, 25, 30, 32]
            >>> rcounts   = [0, 2, 0, 2, 0, 3, 0, 3, 0, 2, 0]

            >>> s, c = _replace_captures([], expected_regexs, charnos, rcounts, expected, got, min_rcount=1)

            >>> s                               # byexample: -tag
            'aaAAbb<...>ddd<...>eeeCCcc'

            >>> got = r'aaAAbBBxxxddeeeCCcc'
            >>> s, c = _replace_captures([], expected_regexs, charnos, rcounts, expected, got, min_rcount=1)

            >>> s                               # byexample: -tag
            'aa<...>bb<...>ddd<...>eeeCCcc'

        The definition of "safely" is a little weak. A capture tag may match
        anything so we could consider it as "safe" if after and before the
        capture we also match enough literals.

        This can be controlled with the min_rcount parameter (see Parser class)

            >>> expected = r'aa<...>bb<...>ddd<...>eee<...>cc'
            >>> got = r'aaAAbbBBxxxddeeeCCcc'

        A small value of min_rcount means that we don't need much literals after
        and before the capture.

            >>> s, c = _replace_captures([], expected_regexs, charnos, rcounts, expected, got, min_rcount=1)
            >>> s                               # byexample: -tag
            'aaAAbb<...>ddd<...>eeeCCcc'

            >>> s, c = _replace_captures([], expected_regexs, charnos, rcounts, expected, got, min_rcount=2)
            >>> s                               # byexample: -tag
            'aaAAbb<...>ddd<...>eeeCCcc'

        Notice how a value of 3 changes the result because the 'bb' literal,
        after the capture has only a rcount of 2

            >>> s, c = _replace_captures([], expected_regexs, charnos, rcounts, expected, got, min_rcount=3)
            >>> s                               # byexample: -tag
            'aa<...>bb<...>ddd<...>eeeCCcc'

        Named groups are returned as well:

            >>> expected = r'aa<foo>bb<bar>ddd<baz>eee<zaz>cc'
            >>> got = r'aaAAbbBBxxxddeeeCCcc'

            >>> expected_regexs = ['\A', 'aa', '(?P<foo>.*?)', 'bb',
            ...                     '(?P<bar>.*?)', 'ddd', '(?P<baz>.*?)',
            ...                     'eee', '(?P<zaz>.*?)', 'cc', r'\n*\Z']
            >>> charnos = [0, 0, 2, 7, 9, 14, 17, 22, 25, 30, 32]
            >>> rcounts   = [0, 2, 0, 2, 0, 3, 0, 3, 0, 2, 0]

            >>> s, c = _replace_captures(['foo', 'bar', 'baz', 'zaz'],
            ...                          expected_regexs, charnos, rcounts, expected, got, min_rcount=1)
            >>> s                               # byexample: -tag
            'aaAAbb<bar>ddd<baz>eeeCCcc'
            >>> c
            {'foo': 'AA', 'zaz': 'CC'}



        And the named groups also count as real count with a value of 1 only
        for the regexs that matches a previous match.

        For example, compare the following two scenarios.

        In this case, we have 2 capture tags and the minimum rcount is 2.
        Notice how the last part of the expected we couldn't complete it
        because before <bar> we don't have enough rcounts

            >>> expected = 'aa<foo>bb\ncc\ndd<bar>ee'
            >>> got = 'aaAAbb\nxx\nxxAAee'

            >>> expected_regexs = ['\A', 'aa', '(?P<foo>.*?)', 'bb\n',
            ...                     'cc\n', 'dd', '(?P<bar>.*?)',
            ...                     'ee', r'\n*\Z']
            >>> charnos = [0, 0, 2, 7, 10, 13, 15, 20, 22]
            >>> rcounts   = [0, 2, 0, 3, 3, 2, 0, 2, 0]

            >>> s, c = _replace_captures(['foo', 'bar'], expected_regexs,
            ...                          charnos, rcounts, expected, got, min_rcount=2)
            >>> s                               # byexample: -tag
            'aaAAbb\ncc\ndd<bar>ee'
            >>> c
            {'foo': 'AA'}

        But if instead of <bar> we reuse <foo>, this second group will count
        as 1 because we have information from the previous match (but no, we
        cannot count it as +n, the len of the previous match).

            >>> expected = 'aa<foo>bb\ncc\ndd<foo>ee'

            >>> expected_regexs = ['\A', 'aa', '(?P<foo>.*?)', 'bb\n',
            ...                     'cc\n', 'dd', '(?P=foo)',
            ...                     'ee', r'\n*\Z']
            >>> rcounts   = [0, 2, 0, 3, 3, 2, 1, 2, 0] # notice the +1

            >>> s, c = _replace_captures(['foo'], expected_regexs, charnos, rcounts, expected, got, min_rcount=2)
            >>> s                               # byexample: -tag
            'aaAAbb\ncc\nddAAee'
            >>> c
            {'foo': 'AA'}

        '''

        regs = expected_regexs
        def _compile(regexs):
            return re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)

        assert len(regs) == len(charnos) == len(rcounts)

        best_left_index = 0
        best_right_index = len(regs)-1

        log("Partial Matching:\nGot string to target:\n%s\n" % repr(got),
                self.verbosity-4)
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

            log("|-->  | best at index % 3i (accum rcount % 3i/%i):\nTrying partial left regex: %s" % (
                i, accum, min_rcount,
                repr(''.join(regs[:i+1]))),
                self.verbosity-4)


            m = _compile(regs[:i+1]).match(got)
            if m:
                log("Match\n% 4i: %s\n" % (
                    charnos[i], m.group(0)),
                    self.verbosity-4)

                if accum >= min_rcount:
                    best_left_index = i

        left_side = regs[:best_left_index+1]
        r = _compile(left_side)
        got_left = r.match(got).group(0)

        left_ends_at = charnos[best_left_index+1]

        # a 'capture anything' regex between the left and the right side
        # to hold all the rest of the string
        buffer_tag_name = 'buffer%06i'
        i = 0
        while (buffer_tag_name % i) in captures:
            i += 1

        buffer_tag_name = buffer_tag_name % i
        if buffer_tag_name in captures:
            raise Exception("Invalid state. Weird.... After several tries, the buffer tag is still not uniq. Last try was '%s'" % buffer_tag_name)

        buffer_re = '(?P<%s>.*?)' % buffer_tag_name

        # now go from the right to the left, add a regex each time
        # to see where the whole regex doesn't match
        accum = 0
        for i in range(len(regs)-1, best_left_index, -1):
            try:
                if not rcounts[i]:
                    accum = 0
                    continue

                accum += rcounts[i]

                log("|  <--| best at index % 3i (accum rcount % 3i/%i):\nTrying partial regex: %s" % (
                    i, accum, min_rcount,
                    repr(''.join(left_side + [buffer_re] + regs[i:]))),
                    self.verbosity-4)

                m = _compile(left_side + [buffer_re] + regs[i:]).match(got)
                if m:
                    log("Matched; Buffer between left and right:\n%s\n" % (
                        m.group(buffer_tag_name)),
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
                    accum -= rcounts[i]
                else:
                    raise

        right_side = regs[best_right_index:]

        # because we are using a regex that match all the got string
        # the got_right is a substring of it: everything after the
        # buffer in the middle
        r = _compile(left_side + [buffer_re] + right_side)
        m = r.match(got)
        got_right = m.group(0)[m.end(buffer_tag_name):]

        right_begin_at = charnos[best_right_index]

        replaced_captures = m.groupdict()
        buffer_captured = replaced_captures.pop(buffer_tag_name)

        # we cannot keep replacing the capture tags... leave the
        # string as it is: this always was a best-effort algorithm
        middle_part = expected[left_ends_at:right_begin_at]

        log("Incremental Match:\n##Left: %s\n\n##Middle: %s\n\n##Right: %s\n\n##Captured: %s\n\n##Buffer: %s" % (
                got_left, middle_part, got_right, repr(replaced_captures), buffer_captured), self.verbosity-4)

        return got_left + middle_part + got_right, replaced_captures


class Checker(object):
    def __init__(self, verbosity, **unused):
        self._diff = []
        self.verbosity = verbosity

    def check_got_output(self, example, got, flags):
        if example.expected.advanced_captures:
            self._checker = _RegexChecker(self.verbosity)
            return self._checker.check_got_output(example, got, flags)

        else:
            self._checker = _LinearChecker(self.verbosity)
            return self._checker.check_got_output(example, got, flags)

    def output_difference(self, example, got, flags, use_colors):
        r'''
        Return a string with the differences between the example's expected
        output and the found or got.

        Depending of the flags the diff can be returned differently.
            >>> from byexample.checker import Checker
            >>> output_difference = Checker(verbosity=0).output_difference

            >>> expected = 'one\ntwo\nthree\nfour'
            >>> got      = 'zero\none\ntree\nfour'

            >>> flags = {'enhance_diff': False, 'diff': 'none'}
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

            >>> flags['diff'] = 'unified'
            >>> print(output_difference(expected, got, flags, False))
            Differences:
            @@ -1,4 +1,4 @@
            +zero
             one
            -two
            -three
            +tree
             four

            >>> flags['diff'] = 'ndiff'
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

            >>> flags['diff'] = 'context'
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

            >>> flags['diff'] = 'none'
            >>> flags['enhance_diff'] = True
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

            if flags['enhance_diff']:
                expected, replaced_captures = self._checker.get_captures(
                                                example, got, flags)

        else:
            expected = example # aka literal string, mostly for internal testing

        self._diff = []

        # remove the last empty lines. this should improve the
        # diff when the algorithm is none (just_print)
        # it should be safe too because expected_regexs should have
        # a '\n*' regex at the end to match any possible empty line
        expected = self._remove_last_empty_lines(expected)
        got      = self._remove_last_empty_lines(got)

        if flags['enhance_diff']:
            self._print_named_captures(replaced_captures)
            self._write("Notes:\n%s" % self.HUMAN_EXPL)
            expected, got = self._human(expected), self._human(got)

        diff_type = flags['diff']

        if diff_type != 'none':
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

