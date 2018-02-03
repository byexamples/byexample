import collections, re, shlex, argparse
from .common import log, build_exception_msg, tohuman
from .options import OptionParser

Example = collections.namedtuple('Example', ['interpreter',
                                             'filepath',
                                             'finder',
                                             'start_lineno', 'end_lineno',
                                             'options', 'indentation',
                                             'source',
                                             'expected', 'match'])

Expected = collections.namedtuple('Expected', ['str',
                                               'regexs',
                                               'positions',
                                               'rcounts',
                                               'captures',
                                               ])

class ExampleParser(object):
    def __init__(self, verbosity, encoding, opts_from_cmdline, **unused):
        self.verbosity = verbosity
        self.encoding = encoding

        self.opts_from_cmdline = opts_from_cmdline

    def __repr__(self):
        return '%s Parser' % tohuman(self.language)

    def example_options_string_regex(self):
        '''
        Return a regular expressions to extract a string that contains all
        the options of the example.

        This regex will be used once per example and it must have an
        unnamed group.

        Example:
          #  byexample: bla bla
          /* byexample: bla bla
          # ~byexample~ bla bla

        '''
        raise NotImplementedError() # pragma: no cover

    def example_options_as_list(self, string):
        '''
        Return a list of tokens from the string that was captured by
        the regex of example_options_string_regex.

        For example:
         '-foo a +bar "1 2 3"' should yield [-foo, a, +bar, "1 2 3"]
        '''
        return shlex.split(string)

    def extend_option_parser(self, parent_parser):
        '''
        Return an instance of argparse.ArgumentParser that will be in
        charge of parsing the options list returned by example_options_as_list.

        Basically you need to see the options of an examples as if they were
        options and flags in a command line.

        Because some of the options are implemented by byexample directly,
        those are parsed with parent_parser.
        It is wise to add this parser as a parent parser of yours.

        You must not modify parent_parser in any way.
        '''
        return OptionParser(parents=[parent_parser])

    def capture_tag_regex(self):
        '''
        Return a regular expression to match a 'capture tag'.
        The regex must have a named group:
          - name: the name of the tag.
        '''
        return re.compile(r"<(?P<name>(?:\w|-|\.)+)>")

    def whitespace_non_compiled_regex(self):
        return r'\s+'

    def ellipsis_marker(self):
        return '...'

    def source_from_snippet(self, snippet):
        '''
        Remove the prompts from the snippet and any other thing that
        should not be sent to the interpreter.
        The resulting source code must be executable.
        The given snippet is already aligned and with its indentation removed.
        '''
        raise NotImplementedError() # pragma: no cover

    def expected_from_match(self, match):
        return match.group("expected")

    def get_example_from_match(self, optparser, options, match, example_str,
                                     interpreter, finder, where):
        self.options = options

        start_lineno, end_lineno, filepath = where
        indent = match.group('indent')

        # update the example string and the match removin any indentation
        example_str = self.check_and_remove_ident(example_str, indent, where)
        match = self.check_keep_matching(example_str, match, where)

        snippet  = match.group("snippet")
        options.up(self.extract_options(snippet, optparser, where))

        expected = self.expected_from_match(match)

        if not expected:
            expected = ''   # make sure that it is a string


        expected_regexs, positions, rcounts, captures = self.expected_as_regexs(
                                                expected,
                                                options['norm_ws'],
                                                options['capture'],
                                                where)

        source = self.source_from_snippet(snippet)
        if not source.endswith('\n'):
            source += '\n'


        expected = Expected(
                          # the output expected
                          str=expected,

                          # expected regex version
                          regexs=expected_regexs,

                          # where each regex comes from
                          positions=positions,

                          # the 'real count' of literals
                          rcounts=rcounts,

                          # the names of the capture tags in the expected regex
                          captures=captures
                          )

        example = Example(
                          # the source code to execute and the expected
                          source=source, expected=expected,

                          # the options to customize this example
                          options=options.copy(),

                          # full match of this example (without indentation)
                          match=match,

                          # the original indentation of the example
                          indentation=indent,

                          # file from where this example was extracted
                          filepath=filepath,

                          # by whom
                          finder=finder,

                          # start / end line numbers (inclusive) in the file
                          start_lineno=start_lineno, end_lineno=end_lineno,

                          # the interpreter for this example
                          interpreter=interpreter)

        options.down()

        del self.options
        return example

    def check_and_remove_ident(self, example_str, indent, where):
        r'''
        Given an example string, remove its indent, including a possible empty
        line at the end.
            >>> from byexample.parser import ExampleParser
            >>> parser = ExampleParser(0, 'utf8', ""); parser.language = 'python'
            >>> check_and_remove_ident = parser.check_and_remove_ident
            >>> check_and_remove_ident('  >>> 1 + 2\n  3\n ', '  ', (1, 2, 'foo.rst'))
            '>>> 1 + 2\n3'

        If the string contains a line with a lower level of indentation,
        raise an exception.

            >>> check_and_remove_ident('  >>> 1 + 2\n3\n', '  ', (1, 2, 'foo.rst'))
            Traceback (most recent call last):
            <...>
            ValueError: File "foo.rst", line 1, [Python Parser]
            The line 2 is misaligned (wrong indentation). Expected at least 2 spaces.
            001   >>> 1 + 2
            002 3

        '''
        start_lineno, _, filepath = where

        lines = example_str.split('\n')

        if not lines[-1].strip():
            lines = lines[:-1]  # remove last whitespace-only line

        indent_stripped = []
        for lineno, line in enumerate(lines):
            if not line.startswith(indent):
                msg = 'The line %i is misaligned (wrong indentation). ' +\
                      'Expected at least %i spaces.\n%s'

                radio = 2
                context = lines[max(lineno-radio, 0):lineno+radio+1]
                context = [("%03i " % (i + start_lineno)) + l
                            for i, l in enumerate(context, max(lineno-radio, 0))]

                msg = msg % (start_lineno + lineno,
                                len(indent),
                                '\n'.join(context))
                raise ValueError(build_exception_msg(msg, where, self))

            indent_stripped.append(line[len(indent):])

        return '\n'.join(indent_stripped)

    def check_keep_matching(self, example_str, match, where):
        r'''
        Given an example string, try to apply the match again.
        This is a health-check intended to be used after a call to
        'check_and_remove_ident'

            >>> from byexample.parser import ExampleParser
            >>> import re

            >>> parser = ExampleParser(0, 'utf8', ""); parser.language = 'python'
            >>> check_and_remove_ident = parser.check_and_remove_ident
            >>> check_keep_matching    = parser.check_keep_matching

            >>> code = '  >>> 1 + 2'
            >>> match = re.match(r'[ ]*>>> [^\n]*', code)

            >>> code_i = check_and_remove_ident(code, '  ', (1, 2, 'foo.rst'))
            >>> code_i != code
            True
            >>> new_match = check_keep_matching(code_i, match, (1, 2, 'foo.rst'))

        This should not happen but if for some reason the regex doesn't match
        the full string, raise an exception:

            >>> x_code = 'x' + code_i
            >>> check_keep_matching(x_code, match, (1, 2, 'foo.rst'))
            Traceback (most recent call last):
            <...>
            ValueError: <...>

            >>> code_x = code_i + '\nx'
            >>> check_keep_matching(code_x, match, (1, 2, 'foo.rst'))
            Traceback (most recent call last):
            <...>
            ValueError: <...>

        '''
        start_lineno, _, filepath = where

        new_match = match.re.match(example_str)
        if not new_match:
            msg = 'The regex does not match the example after ' +\
                  'removing the indentation. '

            raise ValueError(build_exception_msg(msg, where, self))

        if new_match.start() != 0 or new_match.end() != len(example_str):
            msg = '%i bytes were left out after removing the indentation. ' +\
                  'Dropped bytes at the %s of example:\n%s\n'

            if new_match.start() != 0:
                dropped = example_str[:new_match.start()]
                at = 'begin'
            else:
                dropped = example_str[new_match.end():]
                at = 'end'

            msg = msg % (len(dropped), at, dropped)
            raise ValueError(build_exception_msg(msg, where, self))

        return new_match

    def _as_safe_regexs(self, literals, charno, normalize_whitespace):
        r'''
        Process a possible multi line literals string and create one
        regex per line.

            >>> from byexample.parser import ExampleParser
            >>> parser = ExampleParser(0, 'utf8', ""); parser.language = 'python'
            >>> _safe = parser._as_safe_regexs

        A empty string doesn't yield anything useful

            >>> _safe('', 0, False)
            ([], [], [])

        But for something else, _as_safe_regexs returns a list of regexs
        that if they are joined with the flags re.MULTILINE | re.DOTALL,
        matches the initial 'literals' string.
        Because 'literals' can be anything, we need to protect us from
        strings that look like regex.

            >>> _safe('AB+', 0, False)
            (['AB\\+'], [0], [3])

        Also, it returns a list of positions that represent the position
        in which each regex should match in the 'expected' string.
        The charno parameter control the offset to shift all the positions

            >>> _safe('AB+', 4, False)
            (['AB\\+'], [4], [3])

        The third and last return item is the 'rcount' or the 'real count'.
        It is the count of how many literals a line has. In normal circustances,
        rcount == len(line) but if normalize_whitespace == True, each secuence
        of whitespaces will count as just +1.

        Because we are creating a regex per line, where we should put
        the new line character?

        The current implementation ensures that the new line character
        (if exists) will be appended to the end of the line.

            >>> r, p, c = _safe('A\nB', 0, False)
            >>> r
            ['A\\\n', 'B']

            >>> p
            [0, 2]

            >>> c
            [2, 1]

            >>> r, p, c = _safe('\n  A \n\nB  C\n', 0, False)
            >>> r
            ['\\\n', '\\ \\ A\\ \\\n', '\\\n', 'B\\ \\ C\\\n']

            >>> p
            [0, 1, 6, 7]

            >>> c
            [1, 5, 1, 5]


        When the flag normalize_whitespace is true, this things are a little
        different.

        The whitespaces are replaced by the \s+ regexs; consecutive \s+ regexs
        are merged into one.
        This is really important, things like \s+\s+ are considered pathological
        regexs with terrible performance.

            >>> r, p, c = _safe('\n  A \n\nB  C\n', 0, True)
            >>> r
            ['\\s+', 'A\\s+', 'B\\s+C\\s+']

            >>> p
            [0, 3, 7]

            >>> c
            [1, 2, 4]

        '''
        if not literals:
            return [], [], []

        # We start with a single element at charno position
        exprs   = [literals]
        charnos = [charno]
        next_charno = charno + len(literals)

        # A 'rcount' or 'real count' is how many bytes a literal has.
        # In normal circustances, rcount == len(literal) but if
        # normalize_whitespace is True, any whitespace secuence counts
        # as one.
        # In other words, the rcount of " A " is 3; of "  A  " is 3 too
        # and of "  A" is 2
        rcounts = []

        # Now we want to split the possible multi line literals
        # into lines: this will make the life easier for supporting
        # the incremental matching later (see Checker)
        #
        # Our definition is that the new line character will be
        # appended or at the end of the line.
        exprs = exprs[0].split('\n')
        exprs[:-1] = [e + '\n' for e in exprs[:-1]]

        # re calculate the new position for each expr
        assert len(charnos) == 1
        for e in exprs[:-1]:
            charnos.append(charnos[-1] + len(e))

        assert len(exprs) == len(charnos) # any charno missing?
        assert next_charno == charnos[-1] + len(exprs[-1]) # any byte missing?

        # it is possible that the last line is empty (because the previous
        # ended in a \n -> remove it
        if not exprs[-1]:
            del exprs[-1]
            del charnos[-1]

        # empty strings should not exist
        assert all(e for e in exprs)

        if normalize_whitespace:
            # Because all the exprs ends in \n (except the last one),
            # all of them will end in \s+ (except the last one)
            # Said that, any leading whitespace at the begin of a expr
            # can be stripped away because it will be matched by the \s+
            # of the previous expr (except for the first one)
            # By doing this, we need to re calculate their charnos too
            _es = [exprs[0]]
            _cs = [charnos[0]]
            leading_ws_re = re.compile(r'\A\s*', re.MULTILINE | re.DOTALL)
            for c, e in zip(charnos[1:], exprs[1:]):
                olen = len(e)
                lstripped = leading_ws_re.sub('', e)

                # if we stripped all the text, do not add it to the
                # list of regexs
                if not lstripped:
                    continue

                _es.append(lstripped)
                _cs.append(c + (olen - len(lstripped)))

            exprs   = _es
            charnos = _cs

        assert len(exprs) == len(charnos) # any charno missing?
        assert all(e for e in exprs) # any empty string?

        if normalize_whitespace:
            # We don't care about any kind of whitespace, so we will replace
            # them by a \s+ regex
            # Because we will be mixing regexs with literals, it is time
            # to build safe literals and count the 'real counts'
            any_ws_re = re.compile(r'\s+', re.MULTILINE | re.DOTALL)

            _rcs = []
            _es = []
            for e in exprs:
                # First, separate the chunks of literals
                chunks = any_ws_re.split(e)

                assert chunks

                # Count the literals (this will not count the whitespaces)
                rcount = sum(len(ck) for ck in chunks)

                # Now escape each chunk
                chunks = [re.escape(ck) for ck in chunks]

                # And recombine them joining them with the \s+ pattern
                _es.append(any_ws_re.pattern.join(chunks))

                # And compute the final rcount, this will add a +1 for
                # each secuence of whitespaces. In other words, given
                # N chunks, add +N-1
                rcount += len(chunks) - 1
                _rcs.append(rcount)


            exprs = _es
            rcounts = _rcs

        else:
            # Because each expr already has a new line, we compute
            # the real count just as the length of each expr
            rcounts = [len(e) for e in exprs]

            # We leave the whitespaces as they are and we escape them
            # along with the rest of the expressions
            exprs = [re.escape(e) for e in exprs]

            assert sum(rcounts) == len(literals)

        # There is no need to update the charnos: we replaced a chunk
        # by other "of equivalent length and position".
        # Because this "equivalent" version may contain more characters
        # we cannot relay on len(expr) to fix the charnos anymore
        assert len(exprs) == len(charnos) # any charno missing?
        assert all(e for e in exprs) # any empty string?
        assert len(exprs) == len(rcounts) # any rcount missing?

        return exprs, charnos, rcounts


    def expected_as_regexs(self, expected, normalize_whitespace, capture, where):
        r'''
        From the expected string create a list of regular expressions that
        joined with the flags re.MULTILINE | re.DOTALL, matches
        that string.

        This method returns four things: a list of regexs, a list with the
        position in the expected string from where it was created the regex,
        a list of rcounts and a list of capture tag names seen.

            >>> from byexample.parser import ExampleParser
            >>> parser = ExampleParser(0, 'utf8', ""); parser.language = 'python'
            >>> _as_regexs = parser.expected_as_regexs
            >>> where = (1, 2, 'foo.rst')

            >>> expected = 'a<foo>b<bar>c'
            >>> regexs, positions, rcounts, names = _as_regexs(expected, False, True, where)

        We return the names of the named capture groups

            >>> sorted(names)
            ['bar', 'foo']

        And the regexs

            >>> regexs
            ['\\A', 'a', '(?P<foo>.*?)', 'b', '(?P<bar>.*?)', 'c', '\\n*\\Z']

            >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
            >>> m.match('axxbyyyc').groups()
            ('xx', 'yyy')

        And we can see the positions of each regex

            >>> positions
            [0, 0, 1, 6, 7, 12, 13]

            >>> len(expected) == positions[-1]
            True

        And the rcount of each regex. A rcount or 'real count' count how many
        literals are. See _as_safe_regexs for more information about this but
        in a nutshell, rcount == len(line) if normalize_whitespace is False;
        if not, it is the len(line) but counting the secuence of whitespaces as
        +1.

        Multi line strings will yield splitted regexs: one regex per line.
        This in on purpose to support the concept of incremental matching
        (match the whole regex matching one regex at time)

            >>> expected = 'a\n<foo>bcd\nefg<bar>hi'
            >>> regexs, positions, rcounts, names = _as_regexs(expected, False, True, where)

            >>> regexs
            ['\\A',
             'a\\\n',
             '(?P<foo>.*?)',
             'bcd\\\n',
             'efg',
             '(?P<bar>.*?)',
             'hi',
             '\\n*\\Z']

        Notice also how the capture tags don't count as 'real counts' (zero).
        The first and the last regex either.

            >>> rcounts
            [0, 2, 0, 4, 3, 0, 2, 0]

        The normalize_whitespace and capture flags modify how the regexs
        are built:
         - if normalize_whitespace is true, replace all the consecutive
           whitespaces by a single regular expression that matches any amount
           of whitespaces. The net effect is that regardless of
           the spaces in the expected, the regexp will ignore that.
           However we preserve the new line as 'regex's boundaries'

            >>> r, p, c, _ = _as_regexs('a  \n   b  \t\vc', True, True, where)

            >>> r
            ['\\A', 'a\\s+', 'b\\s+c', '\\s*\\Z']

            >>> m = re.compile(''.join(r), re.MULTILINE | re.DOTALL)
            >>> m.match('a b c') is not None
            True

            And also, count the consecutive whitespaces as a +1 when the
            rcount is computed (do not count each whitespace)

            >>> c
            [0, 2, 3, 0]

         - if capture is true, replace the literals capture tags by regexs.

            >>> r, p, _, n = _as_regexs('a<foo>b<bar>c', False, True, where)
            >>> m = re.compile(''.join(r), re.MULTILINE | re.DOTALL)
            >>> m.match('axxbyyyc').groups()
            ('xx', 'yyy')

           Note that if two or more capture tags are consecutive,
           we will raise an exception as this is ambiguous:

            >>> # but here? foo is 'x' and bar 'xyyy'?, '' and 'xxyyy', or ....
            >>> _as_regexs('a<foo><bar>c', False, True, where)
            Traceback (most recent call last):
            <...>
            ValueError: <...>

         - if the capture flag is False, all the <...> tags are taken literally.

            >>> r, p, _, _ = _as_regexs('a<foo>b<bar>c', False, False, where)
            >>> m = re.compile(''.join(r), re.MULTILINE | re.DOTALL)
            >>> m.match('axxbyyyc') is None # don't matched as <foo> is not xx
            True

            >>> m.match('a<foo>b<bar>c') is None # the strings <foo> <bar> are literals
            False

        The capture will behave differently if normalize_whitespace is true or false.

        In the default, normalize_whitespace == False, case, a capture will
        include any amount of spaces, including new lines even if they are at
        the begin or end of the match, always

            >>> expected = 'a<foo>b'
            >>> regexs, positions, _, names = _as_regexs(expected, False, True, where)

            >>> regexs
            ['\\A', 'a', '(?P<foo>.*?)', 'b', '\\n*\\Z']

            >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
            >>> m.match('a  \n 123\n\n b').groups()
            ('  \n 123\n\n ',)

        When normalize_whitespace is True it will depend if the capture tag is
        preceded or followed by a whitespace.

        When no whitespace is around the tag, the things work as if
        normalize_whitespace was false

            >>> expected = 'a<foo>b'
            >>> regexs, positions, _, names = _as_regexs(expected, True, True, where)

            >>> regexs
            ['\\A', 'a', '(?P<foo>.*?)', 'b', '\\s*\\Z']

            >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
            >>> m.match('a  \n 123\n\n b').groups()
            ('  \n 123\n\n ',)

        But if we add some whitespace

            >>> expected = 'a <foo>b'
            >>> regexs, positions, _, names = _as_regexs(expected, True, True, where)

            >>> regexs
            ['\\A', 'a\\s+', '(?!\\s)(?P<foo>.*?)', 'b', '\\s*\\Z']

            >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
            >>> m.match('a  \n 123\n\n b').groups()
            ('123\n\n ',)

            >>> expected = 'a<foo> b'
            >>> regexs, positions, _, names = _as_regexs(expected, True, True, where)

            >>> regexs
            ['\\A', 'a', '(?P<foo>.*?)(?<!\\s)', '\\s+b', '\\s*\\Z']

            >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
            >>> m.match('a  \n 123\n\n b').groups()
            ('  \n 123',)

        If you want to ignore all the whitespace at the begin or end of the tag,
        just add a whitespace around it

            >>> expected = 'a\n<foo>\tb'
            >>> regexs, positions, _, names = _as_regexs(expected, True, True, where)

            >>> regexs
            ['\\A', 'a\\s+', '(?!\\s)(?P<foo>.*?)(?<!\\s)', '\\s+b', '\\s*\\Z']

            >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
            >>> m.match('a  \n 123\n\n b').groups()
            ('123',)

        Any trailing new line will be ignored and if normalize_whitespace is
        True, any trailing whitespace.

            >>> expected = '<foo>\n\n\n'
            >>> regexs, positions, _, names = _as_regexs(expected, False, True, where)

            >>> regexs
            ['\\A', '(?P<foo>.*?)(?<!\\n)', '\\n*\\Z']

            >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
            >>> m.match('   123  \n\n\n\n').groups()
            ('   123  ',)

            >>> expected = '<foo>  \n\n'
            >>> regexs, positions, _, names = _as_regexs(expected, True, True, where)

            >>> regexs
            ['\\A', '(?P<foo>.*?)(?<!\\s)', '\\s*\\Z']

            >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
            >>> m.match('   123  \n\n\n\n').groups()
            ('   123',)

        '''
        start_lineno, _, filepath = where

        # remove any trailing new lines, we will add a regex to match any
        # posible empty line at the end later
        # when normalize_whitespace == True, ignore remove all trailing
        # whitespaces
        expected = re.sub(r'\s+\Z' if normalize_whitespace else r'\n+\Z',
                          '', expected)

        charno = 0
        names_seen = []

        regexs = []
        charnos = []
        rcounts = []

        regexs.append(r'\A') # the begin of the string
        charnos.append(charno)
        rcounts.append(0)

        if capture:
            for match in self.capture_tag_regex().finditer(expected):
                if charno == match.start() and charno > 0:
                    msg = "Two consecutive capture tags were found. " +\
                          "This is ambiguous."
                    raise ValueError(build_exception_msg(msg, where, self))

                literals = expected[charno:match.start()]
                if literals:
                    _res, _pos, _rcount = self._as_safe_regexs(literals, charno, normalize_whitespace)
                    regexs.extend(_res)
                    charnos.extend(_pos)
                    rcounts.extend(_rcount)

                pre_capture  = literals
                post_capture = expected[match.end():]

                charno = match.start()

                name = match.group("name")
                name = name.replace("-", "_") # uniform the name

                rcount = 0

                if name == self.ellipsis_marker():
                    # capture anything (non-greedy)
                    regex = r"(?:.*?)"

                else:
                    if name in names_seen:
                        # matched the same string that a previous
                        # group matched with that name
                        regex = r"(?P=%s)" % name
                        rcount = 1

                    else:
                        # first seen, capture anything (non-greedy)
                        names_seen.append(name)
                        regex = r"(?P<%s>.*?)" % name

                # match 'anything' but do not match any leading
                # space if the previous regex already matches that
                # do the same for the trailing space and next regex
                if normalize_whitespace:
                    if re.search(r'\s\Z', pre_capture, re.MULTILINE | re.DOTALL):
                        regex = r'(?!\s)' + regex  # do not begin with a whitespace

                    if re.search(r'\A\s', post_capture, re.MULTILINE | re.DOTALL):
                        regex = regex + r'(?<!\s)' # do not end with a whitespace

                if not post_capture:
                    if normalize_whitespace:
                        regex = regex + r'(?<!\s)' # do not end with a whitespace
                    else:
                        regex = regex + r'(?<!\n)' # do not end with a newline

                regexs.append(regex)
                charnos.append(charno)
                rcounts.append(rcount)

                charno = match.end()

        literals = expected[charno:]
        if literals:
            _res, _pos, _rcount = self._as_safe_regexs(literals, charno, normalize_whitespace)
            regexs.extend(_res)
            charnos.extend(_pos)
            rcounts.extend(_rcount)

        charno = len(expected)

        # the end: ignore any trailing new line (trailing whitespace if
        # normalize_whitespace == True)
        regexs.append(r"\s*\Z" if normalize_whitespace else r'\n*\Z')
        charnos.append(charno)
        rcounts.append(0)

        return regexs, charnos, rcounts, names_seen

    def extract_options(self, snippet, optparser, where):
        start_lineno, _, filepath = where
        optstring_match = self.example_options_string_regex().search(snippet)

        if not optstring_match:
            optlist = []

        else:
            optlist = self.example_options_as_list(optstring_match.group(1))

        if not isinstance(optlist, list):
            raise ValueError("The option list returned by the parser is not a list!. This probably means that there is a bug in the parser %s." % str(self))

        optparser_extended = self.extend_option_parser(optparser)
        if not isinstance(optparser_extended, argparse.ArgumentParser):
            raise ValueError("The option parser is not an instance of ArgumentParser!.  This probably means that there is a bug in the parser %s." % str(self))

        # now we can re-parse this argument 'options' from the command line
        # this will enable the user to set some options for a specific language
        #
        # we parse this non-strictly because the 'options' string from the
        # command line may contain language-specific options for other
        # languages than this parser (self) is targeting.
        opts = optparser_extended.parse(self.opts_from_cmdline, strict=False)

        # then, we parse the example's options
        # in this case we parse it strictly because the example's options
        # must contain options standard of byexample and/or standard for this
        # parser (self)
        # any other options is treated as an error
        #
        # TODO handle errors here: we check this but we don't do anything useful
        opts.up(optparser_extended.parse(optlist, strict=True))

        return opts

