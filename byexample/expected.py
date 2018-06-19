from .common import log
import string, re

class Expected(object):
    def __init__(self, expected_str, regexs, charnos, rcounts, tags_by_idx):
        self.str = expected_str
        self.regexs = regexs
        self.charnos = charnos
        self.rcounts = rcounts
        self.tags_by_idx = tags_by_idx

class _LinearExpected(Expected):
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
        >>> exp = ex.expected

        If <foo> is .* we can split the expected string into two: aa and bb; and
        check each of them in order from left to right without overlapping:

        >>> got = 'aaXYZbbcc'
        >>> exp.check_got_output(ex, got, 0, 0)
        True

        Once we performed the check we can query the captured strings:

        >>> whole, captures = exp.get_captures(ex, got, 0, 0)

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
        >>> exp.check_got_output(ex, got, 0, 0)
        False

        >>> whole, captures = exp.get_captures(ex, got, 0, 0)

        In this case the whole string will have some tags replaced but others no
        in a best effort manner.

        >>> whole
        'aaXYZccbb<bar>cc'

        And the captures, obviously, will be incomplete too

        >>> captures['foo'], captures.get('bar')
        ('XYZcc', None)

        The algorithm works perfectly fine with unnamed captures

        >>> ex = build_example('f()', 'aa<...>bb<...>cc', 0, None, None, (0, 1, 'file'))
        >>> exp = ex.expected

        >>> got = 'aaXYZbbcc'
        >>> exp.check_got_output(ex, got, 0, 0)
        True

        >>> whole, captures = exp.get_captures(ex, got, 0, 0)

        >>> whole == got
        True

        But nothing is captured of course (we keep the captured string of the
        named capture tags only)

        >>> captures
        {}

        The algorithm also takes into account what happen if the expected string
        starts or ends with a tag:

        >>> ex = build_example('f()', '<foo>bb<...>bb<bar>', 0, None, None, (0, 1, 'file'))
        >>> exp = ex.expected

        >>> got = 'aabbxbbcc'
        >>> exp.check_got_output(ex, got, 0, 0)
        True

        >>> exp.get_captures(ex, got, 0, 0)
        ('aabbxbbcc', {'bar': 'cc', 'foo': 'aa'})

        Or if it has a single literal chunk

        >>> ex = build_example('f()', '<foo>bbbb<bar>', 0, None, None, (0, 1, 'file'))
        >>> exp = ex.expected

        >>> got = 'aabbbbcc'
        >>> exp.check_got_output(ex, got, 0, 0)
        True

        >>> exp.get_captures(ex, got, 0, 0)
        ('aabbbbcc', {'bar': 'cc', 'foo': 'aa'})

        If it has a single tag

        >>> ex = build_example('f()', '<foo>', 0, None, None, (0, 1, 'file'))
        >>> exp = ex.expected

        >>> got = 'bbbb'
        >>> exp.check_got_output(ex, got, 0, 0)
        True

        >>> exp.get_captures(ex, got, 0, 0)
        ('bbbb', {'foo': 'bbbb'})

        Or even if there is any tag at all:

        >>> ex = build_example('f()', 'bbbb', 0, None, None, (0, 1, 'file'))
        >>> exp = ex.expected

        >>> got = 'bbbb'
        >>> exp.check_got_output(ex, got, 0, 0)
        True

        >>> exp.get_captures(ex, got, 0, 0)
        ('bbbb', {})


        We still need to use the regexs that represent the literal chunks
        as they may not be so 'literal'. Think for example that their regexs
        will be in charge of consume the whitespace if we ask for it

        >>> parser.extract_options = lambda x: {'norm_ws': True, 'tags': True}
        >>> ex = build_example('f()', '\n  <...>A \n\nB<...> C\n<...>', 0, None, None, (0, 1, 'file'))
        >>> exp = ex.expected

        >>> got = ' A B  C '
        >>> exp.check_got_output(ex, got, 0, 0)
        True

        >>> exp.get_captures(ex, got, 0, 0)
        (' A B  C ', {})

        '''
    def __init__(self, *args, **kargs):
        Expected.__init__(self, *args, **kargs)
        self.check_good = False

    def check_got_output(self, example, got, flags, verbosity):
        self.check_good = False
        self.verbosity = verbosity

        regexs = example.expected.regexs
        tags_by_idx = example.expected.tags_by_idx
        expected_str = example.expected.str
        charnos = example.expected.charnos

        self._partial_expected_replaced = expected_str
        self._partial_captured = {}
        self.check_good = self._linear_matching(regexs, tags_by_idx, charnos, expected_str, got)
        return self.check_good

    def get_captures(self, example, got, flags, verbosity):
        self.verbosity = verbosity
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

class _RegexExpected(Expected):
    def __init__(self, *args, **kargs):
        Expected.__init__(self, *args, **kargs)
        self.check_good = False

    def check_got_output(self, example, got, flags, verbosity):
        self.check_good = False
        self.verbosity = verbosity
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

    def get_captures(self, example, got, flags, verbosity):
        self.verbosity = verbosity
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

            >>> from byexample.expected import _RegexExpected
            >>> from functools import partial
            >>> exp = _RegexExpected(0, 0, 0, 0, 0)
            >>> exp.verbosity = 0
            >>> _replace_captures = exp._get_all_captures_as_possible

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


