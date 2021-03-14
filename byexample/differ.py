from __future__ import unicode_literals
from .common import colored, ShebangTemplate
import string, difflib, tempfile, os, subprocess
from . import regex as re

# what unicodes are control code?
#   import unicodedata
#   ctrl_codes = [i for i in range(sys.maxunicode+1)
#                   if unicodedata.category(chr(i)) == 'Cc']
#
#   0 <= i <= 31 or 127 <= i <= 159
#
# whitespace control codes?: 9 <= i <= 13
ctrl_tr = {
    i: u'?' if
    (0 <= i <= 31 or 127 <= i <= 159) and not (9 <= i <= 13) else chr(i)
    for i in range(160)
}


class Differ(object):
    def __init__(self, verbosity, encoding, **unused):
        self._diff = []
        self.verbosity = verbosity
        self.encoding = encoding

    def output_difference(self, example, got, flags, use_colors):
        r'''
        Return a string with the differences between the example's expected
        output and the found or got.

        Depending of the flags the diff can be returned differently.
            >>> from __future__ import unicode_literals
            >>> from byexample.differ import Differ
            >>> output_difference = Differ(verbosity=0, encoding='utf8').output_difference

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
            >>> got      = 'one  \ntwo\n\n    thr\x01ee'

            >>> flags['diff'] = 'none'
            >>> flags['enhance_diff'] = True
            >>> print(output_difference(expected, got, flags, False))   # byexample: +rm=~
            Some non-printable characters were replaced by printable ones.
                 $: trailing spaces     ?: ctrl character     ^t: tab
            (You can disable this with '--no-enhance-diff')
            Expected:
            one
            two$$
            ~
            ^tthree
            Got:
            one$$
            two
            ~
                thr?ee

            >>> expected = 'one$$\ntwo\n\n    thr?ee\n^tfour^v'
            >>> got      = 'one  \ntwo\n\n    thr\x01ee\n\tfour^v'

            >>> flags['diff'] = 'none'
            >>> flags['enhance_diff'] = True
            >>> print(output_difference(expected, got, flags, False))   # byexample: +rm=~
            Some non-printable characters were replaced by printable ones.
                 $: trailing spaces     ?: ctrl character     ^t: tab
            Warning, the characters '$', '?', '^t' were present *before* the replacement.
            That means that if you see a '$' it could mean 'trailing spaces' or
            it could mean a literal '$'.
            (You can disable this with '--no-enhance-diff')
            Expected:
            one$$
            two
            ~
                thr?ee
            ^tfour^v
            Got:
            one$$
            two
            ~
                thr?ee
            ^tfour^v
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
                    example, got, flags, self.verbosity
                )

        else:
            expected = example  # aka literal string, mostly for internal testing

        self._diff = []

        # remove the last empty lines. this should improve the
        # diff when the algorithm is none (just_print)
        # it should be safe too because expected_regexs should have
        # a '\n*' regex at the end to match any possible empty line
        expected = self._remove_last_empty_lines(expected)
        got = self._remove_last_empty_lines(got)

        if flags['enhance_diff']:
            namedcap, r1, p1 = self._human_named_captures(replaced_captures)

            expected, r2, p2 = self._human(expected)
            got, r3, p3 = self._human(got)

            self._print_human_replacement_table(r1 | r2 | r3, p1 | p2 | p3)

        diff_type = flags['diff']

        if diff_type not in ('none', 'tool'):
            self.print_diff(expected, got, diff_type, use_colors)
        elif diff_type == 'tool':
            self.use_external_tool(
                expected, got, flags['difftool'], use_colors
            )
        else:
            self.just_print(expected, got, use_colors)

        if flags['enhance_diff'] and namedcap:
            self._write('')
            self._write(namedcap)

        return ''.join(self._diff)

    def _print_human_replacement_table(self, wrepl, prepl):
        if not wrepl:
            return

        HUMAN_EXPL = {
            '$': 'trailing spaces',
            '?': 'ctrl character ',
            '^n': 'new line       ',
            '^t': 'tab            ',
            '^v': 'vertical tab   ',
            '^r': 'carriage return',
            '^f': 'form feed      ',
        }

        assert wrepl.issubset(set(HUMAN_EXPL.keys()))
        assert prepl.issubset(set(HUMAN_EXPL.keys()))

        # warn about replacements that did happen and they could be confused
        # because they were in the original strings before the replace operation
        prepl = wrepl & prepl

        wrepl = list(sorted(wrepl))
        self._write(
            "Some non-printable characters were replaced by printable ones."
        )
        for tmp in [wrepl[i:i + 3] for i in range(0, len(wrepl), 3)]:
            line = ['%02s: %s' % (r, HUMAN_EXPL[r]) for r in tmp]
            line = '    '.join(line)
            self._write("    %s" % line)

        if prepl:
            prepl = list(sorted(prepl))
            one = prepl[0]
            what = HUMAN_EXPL[one]
            self._write(("Warning, the characters %s were present *before* the replacement.\n" + \
                         "That means that if you see a '%s' it could mean '%s' or\n" + \
                         "it could mean a literal '%s'.") % (
                             ', '.join("'%s'" % c for c in prepl),
                             one,
                             what,
                             one))

        self._write("(You can disable this with '--no-enhance-diff')")

    def _human_named_captures(self, replaced_captures):
        wrepl = set()
        prepl = set()
        out = []

        max_len = 36

        def _format(k, v):
            if k is None or v is None:
                return ""

            _mlen = max_len - len(k) + 2  # plus the : and the space

            v, w, p = self._human(v, replace_newlines=True)
            wrepl.update(w)
            prepl.update(p)
            if len(v) > _mlen:
                _mlen -= 5  # minus the ' ... '
                v = v[:int(_mlen / 2)] + " ... " + v[-int(_mlen / 2):]

            return "%s: %s" % (k, v)

        k_vs = list(replaced_captures.items())
        k_vs.sort()
        if not k_vs:
            return '\n'.join(out), wrepl, prepl

        out.append("Tags replaced by the captured output:")

        if len(k_vs) % 2 != 0:
            k_vs.append((None, None))  # make the list even

        for k_v1, k_v2 in zip(k_vs[::2], k_vs[1::2]):
            left, right = _format(*k_v1), _format(*k_v2)

            space_between = max(max_len - len(left), 1) if right else 0
            out.append("    %s%s%s" % (left, " " * space_between, right))

        out.append("(You can disable this with '--no-enhance-diff')")
        return '\n'.join(out), wrepl, prepl

    def _write(self, s, end_with_newline=True):
        self._diff.append(s)
        if end_with_newline and not s.endswith('\n'):
            self._diff.append('\n')

    WS = re.compile(r"[ ]+$", flags=re.MULTILINE)
    NLs = re.compile(r"\n+", flags=re.MULTILINE)
    last_NLs = re.compile(r"\n+\Z", flags=re.MULTILINE)

    def _human(self, s, replace_newlines=False):
        ws = '\t\x0b\x0c\r'
        tr_ws = ['^t', '^v', '^f', '^r', '^s']

        present_before_repl = set()
        wrepl = set()
        prev = s

        # replace whitespace chars by the literal ^X except spaces
        for c, tr_c in zip(ws, tr_ws):
            before = tr_c in s
            if before:
                present_before_repl.add(tr_c)

            s = s.replace(c, tr_c)
            if s != prev:
                wrepl.add(tr_c)
                prev = s

        # replace trailing spaces by something like "$"
        before = any(line.endswith('$') for line in s.split('\n'))
        if before:
            present_before_repl.add('$')

        s = self.WS.sub(lambda m: '$' * (m.end(0) - m.start(0)), s)
        if s != prev:
            wrepl.add('$')
            prev = s

        if replace_newlines:
            before = '\n' in s
            if before:
                present_before_repl.add('^n')

            s = self.NLs.sub('^n', s)
            if s != prev:
                wrepl.add('^n')
                prev = s

        # any weird thing replace it by a '?'
        before = '?' in s
        if before:
            present_before_repl.add('?')

        s = s.translate(ctrl_tr)
        if s != prev:
            wrepl.add('?')
            prev = s

        return s, wrepl, present_before_repl

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

    def use_external_tool(self, expected, got, cmdline, use_colors):
        efilename = gfilename = None
        try:
            with tempfile.NamedTemporaryFile('wt', delete=False) as efile:
                efilename = efile.name
                efile.write(expected)

            with tempfile.NamedTemporaryFile('wt', delete=False) as gfile:
                gfilename = gfile.name
                gfile.write(got)

            tokens = {
                'e': efilename,
                'g': gfilename,
            }
            cmdline = ShebangTemplate(cmdline).quote_and_substitute(tokens)
            try:
                out = subprocess.check_output(
                    cmdline, shell=True, stderr=subprocess.STDOUT
                )
                returncode = 0
            except subprocess.CalledProcessError as err:
                out = err.output
                returncode = err.returncode

            out = out.decode(self.encoding)

            self._write(colored('External diff tool', 'yellow', use_colors))
            self._write(out)

            if returncode != 0:
                self._write(
                    colored('Return code: ', 'red', use_colors),
                    end_with_newline=False
                )
                self._write(str(returncode))

        finally:
            if efilename:
                os.remove(efilename)
            if gfilename:
                os.remove(gfilename)

    def print_diff(self, expected, got, diff_type, use_colors):
        expected_lines = expected.split('\n')
        got_lines = got.split('\n')

        if diff_type == 'unified':
            diff_lines = difflib.unified_diff(
                expected_lines, got_lines, n=2, lineterm=""
            )
            diff_lines = list(diff_lines)
            diff_lines = diff_lines[2:]  # drop diff's header
            diff_lines = self.colored_diff_lines(
                diff_lines, use_colors, green='+', red='-', yellow=['@']
            )

        elif diff_type == 'context':
            diff_lines = difflib.context_diff(
                expected_lines, got_lines, n=2, lineterm=""
            )
            diff_lines = list(diff_lines)
            diff_lines = diff_lines[3:]  # drop diff's header
            diff_lines = self.colored_diff_lines(
                diff_lines,
                use_colors,
                green='+ ',
                red='! ',
                yellow=['*', '-']
            )

        elif diff_type == 'ndiff':
            diff_lines = difflib.ndiff(
                expected_lines, got_lines, charjunk=difflib.IS_CHARACTER_JUNK
            )
            diff_lines = self.colored_diff_lines(
                diff_lines, use_colors, green='+ ', red='- ', yellow=[]
            )
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
