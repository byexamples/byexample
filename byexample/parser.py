import re, shlex, argparse
from .common import log, tohuman, constant
from .options import OptionParser, UnrecognizedOption, ExtendOptionParserMixin
from .expected import _LinearExpected, _RegexExpected


class ExampleParser(ExtendOptionParserMixin):
    def __init__(self, verbosity, encoding, options, **unused):
        ExtendOptionParserMixin.__init__(self)
        self.verbosity = verbosity
        self.encoding  = encoding
        self.options   = options

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

    def extend_option_parser(self, parser):
        '''
        See options.ExtendOptionParserMixin.

        By default do not add any new flag.
        '''
        return parser

    @constant
    def capture_tag_regex(self):
        '''
        Return a regular expression to match a 'capture tag'.
        The regex must have a named group:
          - name: the name of the tag.
        '''
        return re.compile(r"<(?P<name>(?:\w|-|\.)+)>")

    @constant
    def leading_optional_whitespace_regex(self):
        return re.compile(r'\A\s*', re.MULTILINE | re.DOTALL)

    @constant
    def leading_single_whitespace_regex(self):
        return re.compile(r'\A\s', re.MULTILINE | re.DOTALL)

    @constant
    def one_or_more_whitespace_regex(self):
        return re.compile(r'\s+', re.MULTILINE | re.DOTALL)

    @constant
    def zero_or_more_whitespace_regex(self):
        return re.compile(r'\s*', re.MULTILINE | re.DOTALL)

    @constant
    def trailing_whitespace_regex(self):
        return re.compile(r'\s+\Z', re.MULTILINE | re.DOTALL)

    @constant
    def trailing_single_whitespace_regex(self):
        return re.compile(r'\s\Z', re.MULTILINE | re.DOTALL)

    @constant
    def trailing_newlines_regex(self):
        return re.compile(r'\n+\Z', re.MULTILINE | re.DOTALL)

    def ellipsis_marker(self):
        return '...'

    def do_not_begin_with_whitespace_regex_str(self):
        return r'(?!\s)'

    def do_not_end_with_whitespace_regex_str(self):
        return r'(?<!\s)'

    def do_not_end_with_newline_regex_str(self):
        return r'(?<!\n)'

    def trailing_optional_whitespace_regex_str(self):
        return r"\s*\Z"

    def trailing_optional_newline_regex_str(self):
        return r'\n*\Z'

    def end_of_string_regex_str(self):
        return r'\Z'

    def non_capture_anything_regex_str(self, name, at_least_one):
        repetition = r'+' if at_least_one else r'*'
        if name:
            return r"(?P<%s>.%s?)" % (name, repetition)
        else:
            return r"(?:.%s?)" % repetition

    def process_snippet_and_expected(self, snippet, expected):
        r'''
        Process the snippet code and the expected output.

        Take this opportunity to do any processing after the parsing of
        the example (in particular, after the extraction of the options)

        By default, the snippet will end with a new line: most of the
        runners use this to flush and execute the code.
        '''

        if not expected:
            expected = ''   # make sure that it is an empty string

        if not snippet.endswith('\n'):
            snippet += '\n' # make sure that we end the code with a newline
                            # most of the runners use this to flush and
                            # execute the code

        return snippet, expected

    def parse(self, example, concerns):
        options = self.options

        local_options = self.extract_options(example.snippet)
        options.up(local_options)

        example.source, example.expected_str = self.process_snippet_and_expected(
                                                              example.snippet,
                                                              example.expected_str)

        # the options to customize this example
        example.options = local_options

        if concerns:
            concerns.before_build_regex(example, options)

        for x in options['rm']:
            example.expected_str = example.expected_str.replace(x, '')

        are_advanced_captures_enabled = False
        expected_regexs, charnos, rcounts, tags_by_idx, adv = self.expected_as_regexs(
                                                example.expected_str,
                                                options['norm_ws'],
                                                options['tags'],
                                                are_advanced_captures_enabled)

        assert not adv
        ExpectedClass = _LinearExpected if not adv else _RegexExpected

        expected = ExpectedClass(
                          # the output expected
                          expected_str=example.expected_str,

                          # expected regex version
                          regexs=expected_regexs,

                          # where each regex comes from
                          charnos=charnos,

                          # the 'real count' of literals
                          rcounts=rcounts,

                          # all the regexs that are not literal (tags) indexed
                          # by their position in the regex list.
                          # we don't save the regex (use 'regexs' for that),
                          # instead save the name of the tag or None if it's
                          # unnamed
                          tags_by_idx=tags_by_idx,
                          )

        # the source code to execute and the expected
        example.expected = expected

        options.down()
        return example

    def _as_safe_regexs(self, literals, charno, normalize_whitespace):
        r'''
        Process a possible multi line literals string and create one
        regex per word.

            >>> from byexample.parser import ExampleParser
            >>> parser = ExampleParser(0, 'utf8', None); parser.language = 'python'
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
        It is the count of how many literals a word has (including the space
        at the end of the word).
        In normal circustances, rcount == len(word) but if
        normalize_whitespace == True, each secuence of whitespaces will count
        as just +1.

        Because we are creating a regex per word, where we should put
        the space character? or the new line character?

        The current implementation ensures that the space/new line character
        (if exists) will be appended to the end of the word.

            >>> r, p, c = _safe('A\nB', 0, False)
            >>> r
            ['A\\\n', 'B']

            >>> p
            [0, 2]

            >>> c
            [2, 1]

            >>> r, p, c = _safe('\n  A \n\nB  C\n', 0, False)
            >>> r
            ['\\\n', '\\ ', '\\ ', 'A\\ ', '\\\n', '\\\n', 'B\\ ', '\\ ', 'C\\\n']

            >>> p
            [0, 1, 2, 3, 5, 6, 7, 9, 10]

            >>> c
            [1, 1, 1, 2, 1, 1, 2, 1, 2]


        When the flag normalize_whitespace is true, this things are a little
        different.

        The whitespaces are replaced by the \s+ regexs; consecutive \s+ regexs
        are merged into one.
        This is really important, things like \s+\s+ are considered pathological
        regexs with terrible performance.

            >>> r, p, c = _safe('\n  A \n\nB  C\n', 0, True)
            >>> r
            ['\\s+', 'A\\s+', 'B\\s+', 'C\\s+']

            >>> p
            [0, 3, 7, 10]

            >>> c
            [1, 2, 2, 2]

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
        # into words: this will make the life easier for supporting
        # the incremental matching later (see byexample/expected.py)
        #
        # Our definition is that the new line character or the space
        # character will be appended at the end of the word.
        lines = exprs[0].split('\n')
        lines[:-1] = [e + '\n' for e in lines[:-1]]

        exprs = []
        for line in lines:
            words = line.split(' ')
            words[:-1] = [w + ' ' for w in words[:-1]]

            # all the words in 'words' ends in a space ' '
            # except the last.
            # so all of them are no-empty except, may be, the
            # last one.
            #
            # but because the words belong to a line that ends
            # in a new line, the last word must have a new line
            # at the end so it is not empty neither
            #
            # this however may not be true for the last word
            # of the last line... see below
            exprs.extend(words)

        # re calculate the new position for each expr
        assert len(charnos) == 1
        for e in exprs[:-1]:
            charnos.append(charnos[-1] + len(e))

        assert len(exprs) == len(charnos) # any charno missing?
        assert next_charno == charnos[-1] + len(exprs[-1]) # any byte missing?

        # it is possible that the last word is empty (because the previous
        # ended in a \n) -> remove it
        if not exprs[-1]:
            del exprs[-1]
            del charnos[-1]

        # empty strings should not exist
        assert all(e for e in exprs)

        if normalize_whitespace:
            # Because all the exprs ends in ' ' or \n (except the last one),
            # all of them will end in \s+ (except the last one)
            # Said that, any leading whitespace at the begin of a expr
            # can be stripped away because it will be matched by the \s+
            # of the previous expr (except for the first one)
            # By doing this, we need to re calculate their charnos too
            _es = [exprs[0]]
            _cs = [charnos[0]]
            leading_ws_re = self.leading_optional_whitespace_regex()
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
            # We don't care about whitespace, so we will replace
            # them by a \s+ regex
            # Because we will be mixing regexs with literals, it is time
            # to build safe literals and count the 'real counts'
            any_ws_re = self.one_or_more_whitespace_regex()

            _rcs = []
            _es = []
            for e in exprs:
                # First, separate the chunks of literals by any whitespace
                # which includes spaces, new lines but also others ws like tabs
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
            # We compute the real count just as the length of each expr
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


    def expected_as_regexs(self, expected, normalize_whitespace, tags_enabled, are_advanced_captures_enabled):
        r'''
        From the expected string create a list of regular expressions that
        joined with the flags re.MULTILINE | re.DOTALL, matches
        that string.

        This method returns five things:
            - a list of regexs: for literals, captures, wildcards, ...
            - a list with the character numbers, the positions in the expected
              string from where it was created each regex
            - a list of rcounts (see below)
            - a dict of non-literal regexs names (capturing and non-capturing)
              also know as "tags" indexed by position.
              For non-capturing the name will be None.
            - a flag saying if advanced captures are being used (currently
              advanced means repeated named capture tags like 'aa<foo>bb<foo>')

            >>> from byexample.parser import ExampleParser
            >>> import re

            >>> parser = ExampleParser(0, 'utf8', None); parser.language = 'python'
            >>> _as_regexs = parser.expected_as_regexs

            >>> expected = 'a<foo>b<bar>c'
            >>> regexs, charnos, rcounts, tags_by_idx, adv = _as_regexs(expected, False, True, True)

        We return the regexs

            >>> regexs
            ['\\A', 'a', '(?P<foo>.*?)', 'b', '(?P<bar>.*?)', 'c', '\\n*\\Z']

            >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
            >>> m.match('axxbyyyc').groups()
            ('xx', 'yyy')

        And we can see the charnos or the position in the original expected
        string from where each regex was built

            >>> charnos
            [0, 0, 1, 6, 7, 12, 13]

            >>> len(expected) == charnos[-1]
            True

        And the rcount of each regex. A rcount or 'real count' count how many
        literals are. See _as_safe_regexs for more information about this but
        in a nutshell, rcount == len(line) if normalize_whitespace is False;
        if not, it is the len(line) but counting the secuence of whitespaces as
        +1.

        We can see the names of the capturing regexs (named capture tags)

            >>> list(sorted(n for n in tags_by_idx.values() if n != None))
            ['bar', 'foo']

        And we can see the positions of the tags in the regex list
        of all the non-literal regexs or "tags". The value of each
        item is the name of tag or None if it is unnamed

            >>> tags_by_idx
            {2: 'foo', 4: 'bar'}

        No repeated named tags so in our currently definition of advanced capture
        tags this is not advanced:

            >>> adv
            False

        An example with non-capturing regex (unamed tag) could be:

            >>> expected = 'a<...>b<bar>c'
            >>> regexs, _, _, tags_by_idx, _ = _as_regexs(expected, False, True, True)

            >>> regexs
            ['\\A', 'a', '(?:.*?)', 'b', '(?P<bar>.*?)', 'c', '\\n*\\Z']

            >>> list(sorted(n for n in tags_by_idx.values() if n != None))
            ['bar']

            >>> tags_by_idx
            {2: None, 4: 'bar'}

        Multi line strings will yield splitted regexs: one regex per line.
        This in on purpose to support the concept of incremental matching
        (match the whole regex matching one regex at time)

            >>> expected = 'a\n<foo>bcd\nefg<bar>hi'
            >>> regexs, _, rcounts, _, _ = _as_regexs(expected, False, True, True)

            >>> regexs
            ['\\A',
             'a\\\n',
             '(?P<foo>.*?)',
             'bcd\\\n',
             'efg',
             '(?P<bar>.*?)',
             'hi',
             '\\n*\\Z']

        Notice also how the tags don't count as 'real counts' (zero).
        The first and the last regex either.

            >>> rcounts
            [0, 2, 0, 4, 3, 0, 2, 0]

        The normalize_whitespace and tags_enabled flags modify how the regexs
        are built:
         - if normalize_whitespace is true, replace all the consecutive
           whitespaces by a single regular expression that matches any amount
           of whitespaces. The net effect is that regardless of
           the spaces in the expected, the regexp will ignore that.
           However we preserve the new line as 'regex's boundaries'

            >>> r, p, c, _, _ = _as_regexs('a  \n   b  \t\vc', True, True, True)

            >>> r
            ['\\A', 'a\\s+', 'b\\s+', 'c', '\\s*\\Z']

            >>> p
            [0, 0, 7, 12, 13]

            >>> m = re.compile(''.join(r), re.MULTILINE | re.DOTALL)
            >>> m.match('a b c') is not None
            True

            And also, count the consecutive whitespaces as a +1 when the
            rcount is computed (do not count each whitespace)

            >>> c
            [0, 2, 2, 1, 0]

         - if tags_enabled is true, interpret the tags <..> as regexs.

            >>> r, p, _, i, _ = _as_regexs('a<foo>b<bar>c', False, True, True)
            >>> m = re.compile(''.join(r), re.MULTILINE | re.DOTALL)
            >>> m.match('axxbyyyc').groups()
            ('xx', 'yyy')

            >>> [n for n in sorted(i.values()) if n != None]
            ['bar', 'foo']

            >>> i
            {2: 'foo', 4: 'bar'}

           Note that if two or more tags are consecutive,
           we will raise an exception as this is ambiguous:

            >>> # but here? foo is 'x' and bar 'xyyy'?, '' and 'xxyyy', or ....
            >>> _as_regexs('a<foo><bar>c', False, True, True)
            Traceback (most recent call last):
            <...>
            ValueError: <...>

         - if tags_enabled is False, all the <...> tags are taken literally.

            >>> r, p, _, i, _ = _as_regexs('a<foo>b<bar>c', False, False, True)
            >>> m = re.compile(''.join(r), re.MULTILINE | re.DOTALL)
            >>> m.match('axxbyyyc') is None # don't matched as <foo> is not xx
            True

            >>> m.match('a<foo>b<bar>c') is None # the strings <foo> <bar> are literals
            False

            >>> [n for n in sorted(i.values()) if n != None]
            []

            >>> i
            {}

         - if the are_advanced_captures_enabled is True when a named capture is
           repeated we assume that all but first must match the value of
           the first captured:

            >>> r, p, _, _, adv = _as_regexs('a<foo>b<foo>c', False, True, True)
            >>> m = re.compile(''.join(r), re.MULTILINE | re.DOTALL)
            >>> m.match('axxbyyyc') is None # don't matched as <foo>=xx is not yy
            True

            >>> m.match('axxbxxc') is None # ok: <foo> matches xx always
            False

            >>> adv
            True

           Otherwise we will fail:

            >>> _as_regexs('a<foo>b<foo>c', False, True, False)
            Traceback (most recent call last):
            <...>
            ValueError: <...>


        The tags' regexs will behave differently if normalize_whitespace
        is true or false.

        In the default, normalize_whitespace == False, case, a regex will
        include any amount of spaces, including new lines even if they are at
        the begin or end of the match, always

            >>> expected = 'a<foo>b'
            >>> regexs, p, c, _, _ = _as_regexs(expected, False, True, True)

            >>> regexs
            ['\\A', 'a', '(?P<foo>.*?)', 'b', '\\n*\\Z']

            >>> p
            [0, 0, 1, 6, 7]

            >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
            >>> m.match('a  \n 123\n\n b').groups()
            ('  \n 123\n\n ',)

        When normalize_whitespace is True it will depend if the tag is
        preceded or followed by a whitespace.

        When no whitespace is around the tag, the things work as if
        normalize_whitespace was false

            >>> expected = 'a<foo>b'
            >>> regexs, p, _, _, _ = _as_regexs(expected, True, True, True)

            >>> regexs
            ['\\A', 'a', '(?P<foo>.*?)', 'b', '\\s*\\Z']

            >>> p
            [0, 0, 1, 6, 7]

            >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
            >>> m.match('a  \n 123\n\n b').groups()
            ('  \n 123\n\n ',)

        But if we add some whitespace

            >>> expected = 'a <foo>b'
            >>> regexs, p, _, _, _ = _as_regexs(expected, True, True, True)

            >>> regexs
            ['\\A', 'a\\s+', '(?!\\s)(?P<foo>.*?)', 'b', '\\s*\\Z']

            >>> p
            [0, 0, 2, 7, 8]

            >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
            >>> m.match('a  \n 123\n\n b').groups()
            ('123\n\n ',)

            >>> expected = 'a<foo> b'
            >>> regexs, p, _, _, _ = _as_regexs(expected, True, True, True)

            >>> regexs
            ['\\A', 'a', '(?P<foo>.*?)(?<!\\s)', '\\s+', 'b', '\\s*\\Z']

            >>> p
            [0, 0, 1, 6, 7, 8]

            >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
            >>> m.match('a  \n 123\n\n b').groups()
            ('  \n 123',)

        If you want to ignore all the whitespace at the begin or end of the tag,
        just add a whitespace around it

            >>> expected = 'a\n<foo>\tb'
            >>> regexs, p, _, _, _ = _as_regexs(expected, True, True, True)

            >>> regexs
            ['\\A', 'a\\s+', '(?:(?!\\s)(?P<foo>.+?)(?<!\\s)\\s+)?', 'b', '\\s*\\Z']

            >>> p
            [0, 0, 2, 8, 9]

            >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
            >>> m.match('a  \n 123\n\n b').groups()
            ('123',)

            >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
            >>> m.match('a  \n \n\n b').groups('')
            ('',)

        Any trailing new line will be ignored

            >>> expected = '<foo>\n\n\n'
            >>> regexs, _, _, _, _ = _as_regexs(expected, False, True, True)

            >>> regexs
            ['\\A', '(?P<foo>.*?)(?<!\\n)', '\\n*\\Z']

            >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
            >>> m.match('   123  \n\n\n\n').groups()
            ('   123  ',)

            >>> expected = '<foo>'
            >>> regexs, _, _, _, _ = _as_regexs(expected, False, True, True)

            >>> regexs
            ['\\A', '(?P<foo>.*?)(?<!\\n)', '\\n*\\Z']

            >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
            >>> m.match('123\n\n\n\n').groups()
            ('123',)

        And if normalize_whitespace is True, any trailing whitespace.

            >>> expected = '<foo>  \n\n'
            >>> regexs, p, _, _, _ = _as_regexs(expected, True, True, True)

            >>> regexs
            ['\\A', '(?P<foo>.*?)(?<!\\s)', '\\s*\\Z']

            >>> p
            [0, 0, 5]

            >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
            >>> m.match('   123  \n\n\n\n').groups()
            ('   123',)

            >>> expected = ' <foo>  \n\n'
            >>> regexs, p, _, _, _ = _as_regexs(expected, True, True, True)

            >>> regexs
            ['\\A', '\\s+', '(?:(?!\\s)(?P<foo>.+?)(?<!\\s)\\s*)?', '\\Z']

            >>> p
            [0, 0, 1, 10]

            >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
            >>> m.match('   123  \n\n\n\n').groups()
            ('123',)

            >>> expected = ' <foo>'
            >>> regexs, p, _, _, _ = _as_regexs(expected, True, True, True)

            >>> regexs
            ['\\A', '\\s+', '(?:(?!\\s)(?P<foo>.+?)(?<!\\s)\\s*)?', '\\Z']

            >>> p
            [0, 0, 1, 6]

            >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
            >>> m.match('   123  \n\n\n\n').groups()
            ('123',)

        '''
        # remove any trailing new lines, we will add a regex to match any
        # posible empty line at the end later
        # when normalize_whitespace == True, ignore remove all trailing
        # whitespaces
        trailing_re = self.trailing_whitespace_regex() if normalize_whitespace \
                      else self.trailing_newlines_regex()
        non_striped_expected_len = len(expected)
        expected = trailing_re.sub('', expected)

        charno = 0
        names_seen = set()
        tags_by_idx = {}

        regexs = []
        charnos = []
        rcounts = []

        regexs.append(r'\A') # the begin of the string
        charnos.append(charno)
        rcounts.append(0)

        are_advanced_captures_used = False
        trailing_ws_absorved = False

        if tags_enabled:
            for match in self.capture_tag_regex().finditer(expected):
                if charno == match.start() and charno > 0:
                    msg = "Two consecutive capture tags were found at %ith character. " +\
                          "This is ambiguous."
                    raise ValueError(msg % charno)

                literals = expected[charno:match.start()]

                pre_capture  = literals
                post_capture = expected[match.end():]

                need_match_at_least_one = False
                skip_next_leading_ws_count = 0
                if normalize_whitespace:
                    prev_literal_end_ws_match = self.trailing_single_whitespace_regex().search(pre_capture)
                    next_literal_begin_ws_match = self.leading_single_whitespace_regex().search(post_capture)

                    # aka: (?!\\s)(?P<foo>.*?)
                    do_not_begin_ws_prefix = prev_literal_end_ws_match != None

                    # aka: (?P<foo>.*?)(?<!\\s)
                    do_not_end_ws_posfix = next_literal_begin_ws_match != None \
                                            or not post_capture

                    # this is a special case....
                    if do_not_begin_ws_prefix and do_not_end_ws_posfix:
                        # we cannot use .*:
                        #   (?!\\s)(?P<foo>.*?)(?<!\\s)
                        #
                        # because if foo is empty the following regex will never
                        # match:
                        #   aaa\s+ (?!\\s)(?P<foo>.*?)(?<!\\s) \s+bbb
                        # which in turns is, because foo is empty:
                        #   aaa\s+ (?!\\s)(?<!\\s) \s+bbb
                        #
                        # That says follow 'aaa' by whitespace then, (?<!\\s) must
                        # not be preceeded by a whitespace (ups!)
                        # Also, (?!\\s) the next char cannot be whitespace, then
                        # \s+bbb must start with a whitespace (ups again!!)
                        #
                        # Forcing a .+ force to be no empty (this is onle a part
                        # of a bigger solution)
                        need_match_at_least_one = True

                        # Because aaa\s+ \s+bbb is a pathological case when <foo>
                        # is empty, we will strip the leading whitespace
                        # so the regex will be:
                        #   aaa\s+  bbb             if foo is empty
                        #   aaa\s+ .+ \s+ bbb       when foo is not empty
                        #
                        # To acomplish the first case we need to strip the leading
                        # whitespace: we need to move the charno pointer a little
                        # further
                        # How many bytes?, let's see:
                        if next_literal_begin_ws_match:
                            next_leading_span_ends = next_literal_begin_ws_match.span()[1]
                            skip_next_leading_ws_count = next_leading_span_ends

                            # update the post_capture too skipping the leading ws
                            post_capture = post_capture[skip_next_leading_ws_count:]

                if literals:
                    _res, _pos, _rcount = self._as_safe_regexs(literals, charno, normalize_whitespace)
                    regexs.extend(_res)
                    charnos.extend(_pos)
                    rcounts.extend(_rcount)

                charno = match.start()

                name = match.group("name")
                name = name.replace("-", "_") # uniform the name

                rcount = 0

                if name == self.ellipsis_marker():
                    # capture anything (non-greedy)
                    regex = self.non_capture_anything_regex_str(None, need_match_at_least_one)
                    name = None # unamed

                else:
                    if name in names_seen:
                        if are_advanced_captures_enabled:
                            # matched the same string that a previous
                            # group matched with that name
                            regex = r"(?P=%s)" % name
                            rcount = 1
                            are_advanced_captures_used = True

                        else:
                            msg = "The named capture tag '%s' is repeated in " +\
                                  "the %ith character. You need to explicitly " +\
                                  "allow this."

                            raise ValueError(msg % (name, charno))

                    else:
                        # first seen, capture anything (non-greedy)
                        names_seen.add(name)
                        regex = self.non_capture_anything_regex_str(name, need_match_at_least_one)

                # match 'anything' but do not match any leading
                # space if the previous regex already matches that
                # do the same for the trailing space and next regex
                if normalize_whitespace:
                    if do_not_begin_ws_prefix:
                        regex = self.do_not_begin_with_whitespace_regex_str() + \
                                regex

                    if do_not_end_ws_posfix:
                        regex = regex + \
                                self.do_not_end_with_whitespace_regex_str()

                    # this is a special case....
                    if do_not_begin_ws_prefix and do_not_end_ws_posfix:
                        assert need_match_at_least_one

                        if next_literal_begin_ws_match:
                            # so we need to consume at least one ws
                            ws_regex_str = self.one_or_more_whitespace_regex().pattern
                            regex = r'(?:' + regex + ws_regex_str + r')?'
                        else:
                            # the next literal doesn't begin with ws
                            # so we should consume zero or more ws
                            ws_regex_str = self.zero_or_more_whitespace_regex().pattern
                            regex = r'(?:' + regex + ws_regex_str + r')?'

                        trailing_ws_absorved = True

                if not post_capture and not normalize_whitespace:
                    regex = regex + \
                            self.do_not_end_with_newline_regex_str()

                tags_by_idx[len(regexs)] = name

                regexs.append(regex)
                charnos.append(charno)
                rcounts.append(rcount)

                charno = match.end()
                charno += skip_next_leading_ws_count

        literals = expected[charno:]
        if literals:
            _res, _pos, _rcount = self._as_safe_regexs(literals, charno, normalize_whitespace)
            regexs.extend(_res)
            charnos.extend(_pos)
            rcounts.extend(_rcount)


        # the end: ignore any trailing new line (trailing whitespace if
        # normalize_whitespace == True)
        # the only exception is when the previous tag already captured
        # and absorved the whitespace and there is any literal between
        # it and us
        if trailing_ws_absorved and not literals:
            charno = non_striped_expected_len
            trailing_re_str = self.end_of_string_regex_str()

        else:
            charno = len(expected)
            trailing_re_str = self.trailing_optional_whitespace_regex_str() \
                                   if normalize_whitespace \
                                   else self.trailing_optional_newline_regex_str()

        regexs.append(trailing_re_str)
        charnos.append(charno)
        rcounts.append(0)

        return regexs, charnos, rcounts, tags_by_idx, are_advanced_captures_used

    def extract_cmdline_options(self, opts_from_cmdline):
        # now we can re-parse this argument 'options' from the command line
        # this will enable the user to set some options for a specific language
        #
        # we parse this non-strictly because the 'options' string from the
        # command line may contain language-specific options for other
        # languages than this parser (self) is targeting.
        optparser = self.options['optparser']
        optparser_extended = self.get_extended_option_parser(optparser)
        return optparser_extended.parse(opts_from_cmdline, strict=False)

    def extract_options(self, snippet):
        optstring_match = self.example_options_string_regex().search(snippet)

        if not optstring_match:
            optlist = []

        else:
            optlist = self.example_options_as_list(optstring_match.group(1))

        if not isinstance(optlist, list):
            raise ValueError("The option list returned by the parser is not a list!. This probably means that there is a bug in the parser %s." % str(self))

        # we parse the example's options
        # in this case, at difference with extract_cmdline_options,
        # we parse it strictly because the example's options
        # must contain options standard of byexample and/or standard of this
        # parser (self)
        # any other options is an error
        optparser = self.options['optparser']
        optparser_extended = self.get_extended_option_parser(optparser)
        try:
          opts = optparser_extended.parse(optlist, strict=True)
        except UnrecognizedOption as e:
            raise ValueError(str(e))

        return opts

