from .common import log, colored
import string, re, difflib

class Differ(object):
    def __init__(self, verbosity, **unused):
        self._diff = []
        self.verbosity = verbosity

    def output_difference(self, example, got, flags, use_colors):
        r'''
        Return a string with the differences between the example's expected
        output and the found or got.

        Depending of the flags the diff can be returned differently.
            >>> from byexample.differ import Differ
            >>> output_difference = Differ(verbosity=0).output_difference

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
                expected, replaced_captures = example.expected.get_captures(
                                                   example, got,
                                                   flags, self.verbosity)

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
                v = v[:int(_mlen/2)] + " ... " + v[-int(_mlen/2):]


            return "%s: %s" % (k, v)

        k_vs = list(replaced_captures.items())
        k_vs.sort()
        if not k_vs:
            self._write("Nothing captured.")
            return

        self._write("Captured:\n")

        if len(k_vs) % 2 != 0:
            k_vs.append((None, None)) # make the list even

        for k_v1, k_v2 in zip(k_vs[::2], k_vs[1::2]):
            left, right = _format(*k_v1), _format(*k_v2)

            space_between = max(max_len - len(left), 1) if right else 0
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

