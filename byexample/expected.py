from .common import log
import string, re, time

def regex_name_as_tag_name(name):
    return name.replace('_', '-')

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
        >>> from byexample.finder import _build_fake_example as build_example

        >>> opts = {'norm_ws': False, 'tags': True, 'rm': []}

        Consider the following example with a named capture in the expected:

        >>> ex = build_example('f()', 'aa<foo>bb<bar-baz>cc', opts=opts)
        >>> exp = ex.expected

        If <foo> is .* we can split the expected string into two: aa and bb; and
        check each of them in order from left to right without overlapping:

        >>> got = 'aaXYZbbcc'
        >>> exp.check_got_output(ex, got, opts, 0)
        True

        Once we performed the check we can query the captured strings:

        >>> whole, captures = exp.get_captures(ex, got, opts, 0)

        The whole string is the expected string with all of its capture tags
        replaced by the captured texts from the got string.

        Because the check passed we should have a copy of the got:

        >>> whole == got
        True

        The captures is a dictionary with the strings captures by name:

        >>> captures['foo'], captures['bar-baz']
        ('XYZ', '')

        The things gets more interesting when the example fails.
        In this case the values returned by get_captures will be incomplete.

        See _RegexExpected.get_captures documentation.

        The algorithm works perfectly fine with unnamed captures

        >>> ex = build_example('f()', 'aa<...>bb<...>cc', opts=opts)
        >>> exp = ex.expected

        >>> got = 'aaXYZbbcc'
        >>> exp.check_got_output(ex, got, opts, 0)
        True

        >>> whole, captures = exp.get_captures(ex, got, opts, 0)

        >>> whole == got
        True

        But nothing is captured of course (we keep the captured string of the
        named capture tags only)

        >>> captures
        {}

        The algorithm also takes into account what happen if the expected string
        starts or ends with a tag:

        >>> ex = build_example('f()', '<foo>bb<...>bb<bar>', opts=opts)
        >>> exp = ex.expected

        >>> got = 'aabbxbbcc'
        >>> exp.check_got_output(ex, got, opts, 0)
        True

        >>> exp.get_captures(ex, got, opts, 0)
        ('aabbxbbcc', {'bar': 'cc', 'foo': 'aa'})

        Or if it has a single literal chunk

        >>> ex = build_example('f()', '<foo>bbbb<bar>', opts=opts)
        >>> exp = ex.expected

        >>> got = 'aabbbbcc'
        >>> exp.check_got_output(ex, got, opts, 0)
        True

        >>> exp.get_captures(ex, got, opts, 0)
        ('aabbbbcc', {'bar': 'cc', 'foo': 'aa'})

        If it has a single tag

        >>> ex = build_example('f()', '<foo>', opts=opts)
        >>> exp = ex.expected

        >>> got = 'bbbb'
        >>> exp.check_got_output(ex, got, opts, 0)
        True

        >>> exp.get_captures(ex, got, opts, 0)
        ('bbbb', {'foo': 'bbbb'})

        Or even if there is any tag at all:

        >>> ex = build_example('f()', 'bbbb', opts=opts)
        >>> exp = ex.expected

        >>> got = 'bbbb'
        >>> exp.check_got_output(ex, got, opts, 0)
        True

        >>> exp.get_captures(ex, got, opts, 0)
        ('bbbb', {})


        We still need to use the regexs that represent the literal chunks
        as they may not be so 'literal'. Think for example that their regexs
        will be in charge of consume the whitespace if we ask for it

        (See byexample.parser docs)

        >>> opts = {'norm_ws': True, 'tags': True, 'rm': []}
        >>> ex = build_example('f()', '\n  <a>A \n\nB <bc> C\n<c>', opts=opts)
        >>> exp = ex.expected

        >>> got = ' A B  C '
        >>> exp.check_got_output(ex, got, opts, 0)
        True

        >>> exp.get_captures(ex, got, opts, 0)
        (' A B  C ', {'a': '', 'bc': '', 'c': ''})

        >>> got = ' 12A B 34 C 1'
        >>> exp.check_got_output(ex, got, opts, 0)
        True

        >>> exp.get_captures(ex, got, opts, 0)
        (' 12A B 34 C 1', {'a': '12', 'bc': '34', 'c': '1'})
        '''
    def __init__(self, *args, **kargs):
        Expected.__init__(self, *args, **kargs)
        self._regex_expected = _RegexExpected(*args, **kargs)
        self.check_good = self._regex_expected.check_good = False

        self._check_got_output_called = False


    def check_got_output(self, example, got, options, verbosity):
        self.check_good = False
        self.verbosity = verbosity

        regexs = example.expected.regexs
        tags_by_idx = example.expected.tags_by_idx
        expected_str = example.expected.str
        charnos = example.expected.charnos

        self.check_good = self._linear_matching(regexs, tags_by_idx, charnos, expected_str, got)
        self._check_got_output_called = True
        return self.check_good

    def get_captures(self, example, got, options, verbosity):
        if not self._check_got_output_called:
            self.check_got_output(example, got, options, verbosity)

        self.verbosity = verbosity
        self._regex_expected.check_good = self.check_good
        self._regex_expected.verbosity = self.verbosity

        # relay on _RegexExpected's get_captures algorithm
        # it is more complex and less safer than _LinearExpected but
        # yield results of much better quality
        if self.check_good:
            captured = self._regex_expected._get_all_capture_or_none(example, got, options)
            assert captured != None

            return got, captured

        else:
            return self._regex_expected._get_all_capture_as_possible(example, got, options)

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
            if literal:
                literals.append(literal)

            prev = capture_idx + 1

        pos = 0
        for literal in literals:
            r = re.compile(literal, re.MULTILINE | re.DOTALL)
            m = r.search(got, pos)

            if not m:
                return False

            pos = m.end()

        return True

class _RegexExpected(Expected):
    def __init__(self, *args, **kargs):
        Expected.__init__(self, *args, **kargs)
        self.check_good = False
        self._check_got_output_called = False

    def _get_all_capture_or_none(self, example, got, options):
        r = re.compile(''.join(example.expected.regexs), re.MULTILINE | re.DOTALL)
        m = r.match(got)

        if m:
            replaced_captures = m.groupdict('')
            return {regex_name_as_tag_name(n): v
                                    for n, v in replaced_captures.items()}

    def _get_all_capture_as_possible(self, example, got, options):
        expected = example.expected
        if not expected.tags_by_idx:
            return expected.str, {}

        captures = list(sorted(n for n in expected.tags_by_idx.values() if n != None))
        return self._get_captures_by_incremental_match(captures,
                                      expected.regexs,
                                      expected.charnos,
                                      expected.rcounts,
                                      expected.str,
                                      got,
                                      min_rcount = 16,
                                      timeout = 2)

    def check_got_output(self, example, got, options, verbosity):
        self.check_good = False
        self.verbosity = verbosity
        self._captures_from_good_check = None

        captured_or_none = self._get_all_capture_or_none(example, got, options)

        self._check_got_output_called = True
        if captured_or_none != None:
            self._captures_from_good_check = captured_or_none
            self.check_good = True
            return True

        else:
            self.check_good = False
            return False

    def get_captures(self, example, got, options, verbosity):
        if not self._check_got_output_called:
            self.check_got_output(example, got, options, verbosity)

        self.verbosity = verbosity
        if self.check_good:
            # already captured in check_got_output
            return got, self._captures_from_good_check
        else:
            return self._get_all_capture_as_possible(example, got, options)

    def _get_captures_by_incremental_match(self, captures, expected_regexs,
            charnos, rcounts, expected, got, min_rcount, timeout):
        r'''
        Try to replace all the capture groups in the expected by
        the strings found in got.

        The idea is to have the expected and the got as much similar as
        possible making further diffs easier.

            >>> from byexample.expected import _RegexExpected
            >>> from functools import partial
            >>> exp = _RegexExpected(0, 0, 0, 0, 0)
            >>> exp.verbosity = 0
            >>> _replace_captures = exp._get_captures_by_incremental_match

        We can only "safely" replace all the groups at the begin (left) of the
        string before the first difference and replace all the groups at the
        end (right) after the last difference.

            >>> expected = r'aa<...>bb<...>ddd<...>eee<...>cc'
            >>> got = r'aaAAbbBBxxxddeeeCCcc'

            >>> expected_regexs = ['\A', 'aa', '(.*?)', 'bb', '(.*?)', 'ddd',
            ...                    '(.*?)', 'eee', '(.*?)', 'cc', r'\n*\Z']
            >>> charnos = [0, 0, 2, 7, 9, 14, 17, 22, 25, 30, 32]
            >>> rcounts   = [0, 2, 0, 2, 0, 3, 0, 3, 0, 2, 0]

            >>> s, c = _replace_captures([], expected_regexs, charnos, rcounts, expected, got, 1, 1)

            >>> s                               # byexample: -tag
            'aaAAbb<...>ddd<...>eeeCCcc'

            >>> got = r'aaAAbBBxxxddeeeCCcc'
            >>> s, c = _replace_captures([], expected_regexs, charnos, rcounts, expected, got, 1, 1)

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

            >>> s, c = _replace_captures([], expected_regexs, charnos, rcounts, expected, got, min_rcount=1, timeout=1)
            >>> s                               # byexample: -tag
            'aaAAbb<...>ddd<...>eeeCCcc'

            >>> s, c = _replace_captures([], expected_regexs, charnos, rcounts, expected, got, min_rcount=2, timeout=1)
            >>> s                               # byexample: -tag
            'aaAAbb<...>ddd<...>eeeCCcc'

        Notice how a value of 3 changes the result because the 'bb' literal,
        after the capture has only a rcount of 2

            >>> s, c = _replace_captures([], expected_regexs, charnos, rcounts, expected, got, min_rcount=3, timeout=1)
            >>> s                               # byexample: -tag
            'aa<...>bb<...>ddd<...>eeeCCcc'

        Named groups are returned as well:

            >>> expected = r'aa<foo>bb<b-r>ddd<baz>eee<z-z>cc'
            >>> got = r'aaAAbbBBxxxddeeeCCcc'

            >>> expected_regexs = ['\A', 'aa', '(?P<foo>.*?)', 'bb',
            ...                     '(?P<b_r>.*?)', 'ddd', '(?P<baz>.*?)',
            ...                     'eee', '(?P<z_z>.*?)', 'cc', r'\n*\Z']
            >>> charnos = [0, 0, 2, 7, 9, 14, 17, 22, 25, 30, 32]
            >>> rcounts   = [0, 2, 0, 2, 0, 3, 0, 3, 0, 2, 0]

            >>> s, c = _replace_captures(['foo', 'b-r', 'baz', 'z-z'],
            ...                          expected_regexs, charnos, rcounts, expected, got, 1, 1)
            >>> s                               # byexample: -tag
            'aaAAbb<b-r>ddd<baz>eeeCCcc'
            >>> c
            {'foo': 'AA', 'z-z': 'CC'}



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
            ...                          charnos, rcounts, expected, got, min_rcount=2, timeout=1)
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

            >>> s, c = _replace_captures(['foo'], expected_regexs, charnos, rcounts, expected, got, min_rcount=2, timeout=1)
            >>> s                               # byexample: -tag
            'aaAAbb\ncc\nddAAee'
            >>> c
            {'foo': 'AA'}

        Because we are dealing with an expected that will not match the got
        string, it is possible that the regex takes a lot of time trying to
        fit itself into the got string as best as he can.
        This may do a lot of backtracking in the regex engine which can be
        really slow.
        To put a safe guard, the 'timeout' parameter control how much time
        we are willing to spend on this.

        Setting a value of 0 virtually disable this increcmental match:

            >>> s, c = _replace_captures(['foo'], expected_regexs, charnos, rcounts, expected, got, min_rcount=2, timeout=0)
            >>> s                               # byexample: -tag
            'aa<foo>bb\ncc\ndd<foo>ee'
            >>> c
            {}
        '''

        regs = expected_regexs
        def _compile(regexs):
            return re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)

        assert len(regs) == len(charnos) == len(rcounts)

        best_left_index = 0
        best_right_index = len(regs)-1

        timeout_left = timeout / 2.0
        timeout_right = timeout - timeout_left

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

            if timeout_left <= 0:
                log("Partial Matching on the Left Timed Out", self.verbosity-4)
                break

            accum += rcounts[i]

            log("|-->  | best at index % 3i (accum rcount % 3i/%i):\nTrying partial left regex: %s" % (
                i, accum, min_rcount,
                repr(''.join(regs[:i+1]))),
                self.verbosity-4)


            begin = time.time()
            m = _compile(regs[:i+1]).match(got)
            timeout_left -= (time.time() - begin)
            if m:
                log("Match\n% 4i: %s\n" % (
                    charnos[i], m.group(0)),
                    self.verbosity-4)

                if accum >= min_rcount:
                    best_left_index = i

        # Sum any extra time didn't spend on the left.
        # If the left timed out, timeout_left will be negative and
        # in deed will reduce the available timeout on the right
        timeout_right += timeout_left

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

                if timeout_right <= 0:
                    log("Partial Matching on the Right Timed Out", self.verbosity-4)
                    break

                accum += rcounts[i]

                log("|  <--| best at index % 3i (accum rcount % 3i/%i):\nTrying partial regex: %s" % (
                    i, accum, min_rcount,
                    repr(''.join(left_side + [buffer_re] + regs[i:]))),
                    self.verbosity-4)

                begin = time.time()
                m = _compile(left_side + [buffer_re] + regs[i:]).match(got)
                timeout_right -= (time.time() - begin)
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

        replaced_captures = m.groupdict('')
        buffer_captured = replaced_captures.pop(buffer_tag_name)

        # we cannot keep replacing the capture tags... leave the
        # string as it is: this always was a best-effort algorithm
        middle_part = expected[left_ends_at:right_begin_at]

        elapsed = timeout - timeout_right

        replaced_captures = {regex_name_as_tag_name(n): v
                                    for n, v in replaced_captures.items()}
        log("Incremental Match:\n##Elapsed: %0.2f secs\n##Left: %s\n\n##Middle: %s\n\n##Right: %s\n\n##Captured: %s\n\n##Buffer: %s" % (
                elapsed, got_left, middle_part, got_right, repr(replaced_captures), buffer_captured), self.verbosity-4)

        return got_left + middle_part + got_right, replaced_captures


