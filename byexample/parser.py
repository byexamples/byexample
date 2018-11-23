from __future__ import unicode_literals
import re, shlex, argparse
from .common import log, tohuman, constant
from .options import OptionParser, UnrecognizedOption, ExtendOptionParserMixin
from .expected import _LinearExpected, _RegexExpected
from .parser_state_machine import SM_NormWS, SM_NotNormWS

def tag_name_as_regex_name(name):
    return name.replace('-', '_')

class ExampleParser(ExtendOptionParserMixin):
    def __init__(self, verbosity, encoding, options, **unused):
        ExtendOptionParserMixin.__init__(self)
        self.verbosity = verbosity
        self.encoding  = encoding
        self.options   = options

        self._optparser_extended_cache = None
        self._opts_cache = {}

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

        Due implementation details the underscore character '_'
        *cannot* be used as a valid character in the name.
        Instead you should use minus '-'.
        '''
        return {
                'split': re.compile(r"(<(?:[^\W_]|-|\.)+>)"),
                'full': re.compile(r"<(?P<name>(?:[^\W_]|-|\.)+)>"),
                }

    @constant
    def one_or_more_ws_capture_regex(self):
        return re.compile(r'(\s+)', re.MULTILINE | re.DOTALL)

    @constant
    def one_or_more_nl_capture_regex(self):
        return re.compile(r'(\n+)', re.MULTILINE | re.DOTALL)

    @constant
    def trailing_whitespace_regex(self):
        return re.compile(r'\s*\Z', re.MULTILINE | re.DOTALL)

    @constant
    def trailing_newlines_regex(self):
        return re.compile(r'\n*\Z', re.MULTILINE | re.DOTALL)

    def ellipsis_marker(self):
        return '...'

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

        expected_regexs, charnos, rcounts, tags_by_idx = self.expected_as_regexs(
                                                example.expected_str,
                                                options['tags'],
                                                options['norm_ws'])

        ExpectedClass = _LinearExpected

        expected = ExpectedClass(
                          # the output expected
                          expected_str=example.expected_str,

                          # expected regex version
                          regexs=list(expected_regexs),

                          # where each regex comes from
                          charnos=list(charnos),

                          # the 'real count' of literals
                          rcounts=list(rcounts),

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

    def expected_tokenizer(self, expected_str, tags_enabled):
        ''' Iterate over the interesting tokens of the expected string:
             - newlines     - wspaces     - literals    - tag

            >>> from byexample.parser import ExampleParser
            >>> import re

            >>> parser = ExampleParser(0, 'utf8', None); parser.language = 'python'
            >>> _tokenizer = parser.expected_tokenizer

            >>> list(_tokenizer('', True))
            [(0, 'end', None)]

            Return an iterable of tuples: (<charno>, <token type>, <token val>)
            >>> list(_tokenizer(' ', True))
            [(0, 'wspaces', ' '), (1, 'end', None)]

            Multiple chars are considered a single 'literals' token
            >>> list(_tokenizer('abc', True))
            [(0, 'literals', 'abc'), (3, 'end', None)]

            Each tuple contains the <charno>: the position in the string
            where the token was found
            >>> list(_tokenizer('abc def', True))       # byexample: +norm-ws
            [(0, 'literals', 'abc'), (3, 'wspaces', ' '),
             (4, 'literals', 'def'), (7, 'end', None)]

            Multiple spaces are considered a single 'wspaces' token.
            >>> list(_tokenizer(' abc  def\t', True))          # byexample: +norm-ws
            [(0, 'wspaces', ' '),  (1, 'literals', 'abc'),
             (4, 'wspaces', '  '), (6, 'literals', 'def'), (9, 'wspaces', '\t'),
             (10, 'end', None)]

            Each tuple contains the string that constitutes the token.
            >>> list(_tokenizer('<foo><bar> \n\n<...> <...>def <...>', True))  # byexample: +norm-ws -tags
            [(0,  'tag', '<foo>'),      (5,  'tag', '<bar>'), (10, 'wspaces', ' '),
             (11, 'newlines', '\n\n'),  (13, 'tag', '<...>'),
             (18, 'wspaces', ' '),      (19, 'tag', '<...>'), (24, 'literals', 'def'),
             (27, 'wspaces', ' '),      (28, 'tag', '<...>'), (33, 'end', None)]

            If <tags_enabled> is False, the tags are considered literals
            >>> list(_tokenizer('<foo><bar> \n\n<...> <...>def <...>', False))  # byexample: +norm-ws -tags
            [(0,  'literals', '<foo><bar>'), (10, 'wspaces', ' '),
             (11, 'newlines', '\n\n'),       (13, 'literals', '<...>'),
             (18, 'wspaces', ' '),           (19, 'literals', '<...>def'),
             (27, 'wspaces', ' '),           (28, 'literals', '<...>'), (33, 'end', None)]
        '''

        nl_splitter = self.one_or_more_nl_capture_regex()
        ws_splitter = self.one_or_more_ws_capture_regex()
        tag_splitter = self.capture_tag_regex()['split']

        charno = 0
        for k, line_or_newlines in enumerate(nl_splitter.split(expected_str)):
            if k % 2 == 1:
                newlines = line_or_newlines
                yield (charno, 'newlines', newlines)
                charno += len(newlines)
                continue

            line = line_or_newlines
            for j, word_or_spaces in enumerate(ws_splitter.split(line)):
                if j % 2 == 1:
                    wspaces = word_or_spaces
                    yield (charno, 'wspaces', wspaces)
                    charno += len(wspaces)
                    continue

                word = word_or_spaces
                if not tags_enabled and word:
                    yield (charno, 'literals', word)
                    charno += len(word)
                    continue

                for i, lit_or_tag in enumerate(tag_splitter.split(word)):
                    if i % 2 == 1:
                        tag = lit_or_tag
                        yield (charno, 'tag', tag)
                        charno += len(tag)
                        continue

                    literals = lit_or_tag
                    if literals:
                        yield (charno, 'literals', literals)
                        charno += len(literals)
        yield (charno, 'end', None)


    def expected_as_regexs(self, expected, tags_enabled, normalize_whitespace):
        '''
        From the expected string create a list of regular expressions that
        joined with the flags re.MULTILINE | re.DOTALL, matches
        that string.

        This method returns four things:
            - a list of regexs: for literals, captures, wildcards, ...
            - a list with the character numbers, the positions in the expected
              string from where it was created each regex
            - a list of rcounts (see below)
            - a dict of non-literal 'regexs' names (capturing and non-capturing)
              also know as "tags" indexed by position.
              For non-capturing the name will be None.

            >>> from byexample.parser import ExampleParser
            >>> import re

            >>> parser = ExampleParser(0, 'utf8', None); parser.language = 'python'
            >>> _as_regexs = parser.expected_as_regexs

            >>> expected = 'a<foo>b<bar>c'
            >>> regexs, charnos, rcounts, tags_by_idx = _as_regexs(expected, True, False)

        We return the regexs

            >>> regexs
            ('\\A', 'a', '(?P<foo>.*?)', 'b', '(?P<bar>.*?)', 'c', '\\n*\\Z')

            >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
            >>> m.match('axxbyyyc').groups()
            ('xx', 'yyy')

        And we can see the charnos or the position in the original expected
        string from where each regex was built

            >>> charnos
            (0, 0, 1, 6, 7, 12, 13)

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

        The following example shows what happen when we use a non-capturing tag
        (ellipsis tag) also known as unnamed tag and what happen when we use
        a tag name with a - (Python regexs don't support this character):

            >>> expected = 'a<...>b<foo-bar>c'
            >>> regexs, _, _, tags_by_idx = _as_regexs(expected, True, False)

            >>> regexs
            ('\\A', 'a', '(?:.*)', 'b', '(?P<foo_bar>.*?)', 'c', '\\n*\\Z')

            >>> list(sorted(n for n in tags_by_idx.values() if n != None))
            ['foo-bar']

            >>> tags_by_idx
            {2: None, 4: 'foo-bar'}

        Notice how the unnamed tag is mapped to None and how a name with a -
        works out of the box with a subtle change: the regex name has a _
        instead of a -.

        Also notice that the unnamed tag's regex is greedy (.*) while the
        named tag's one is non-greedy (.*?).
        The reason of this is that typically the unnamed tag is used to
        match long unwanted strings while the named tag is for small
        and interesting strings.

        This heuristic does not claim to be bulletproof however.

        Multi line strings will yield splitted regexs: one regex per line.
        This in on purpose to support the concept of incremental matching
        (match the whole regex matching one regex at time)

            >>> expected = 'a\n<foo>bcd\nefg<bar>hi'
            >>> regexs, _, rcounts, _ = _as_regexs(expected, True, False)

            >>> regexs          # byexample: +norm-ws
            ('\\A',
             'a\\\n',
             '(?P<foo>.*?)',
             'bcd\\\n',
             'efg',
             '(?P<bar>.*?)',
             'hi',
             '\\n*\\Z')

        Notice also how the tags don't count as 'real counts' (zero).
        The first and the last regex either.

            >>> rcounts
            (0, 2, 0, 4, 3, 0, 2, 0)

        The normalize_whitespace and tags_enabled flags modify how the regexs
        are built:
         - if normalize_whitespace is true, replace all the consecutive
           whitespaces by a single regular expression that matches any amount
           of whitespaces. The net effect is that regardless of
           the spaces in the expected, the regexp will ignore that.
           However we preserve the new line as 'regex's boundaries'

           >>> r, p, c, _ = _as_regexs('a  \n   b  \t\vc', True, True)

           >>> r
           ('\\A', 'a\\s+(?!\\s)', 'b\\s+(?!\\s)', 'c', '\\s*\\Z')

           >>> p
           (0, 0, 7, 12, 13)

           >>> m = re.compile(''.join(r), re.MULTILINE | re.DOTALL)
           >>> m.match('a b c') is not None
           True

           And also, count the consecutive whitespaces as a +1 when the
           rcount is computed (do not count each whitespace)

           >>> c
           (0, 2, 2, 1, 0)

         - if tags_enabled is true, interpret the tags <...> as regexs.

            >>> r, p, _, i = _as_regexs('a<foo>b<bar>c', True, False)
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
            >>> _as_regexs('a<foo><bar>c', True, False)
            Traceback (most recent call last):
            <...>
            ValueError: <...>

         - if tags_enabled is False, all the <...> tags are taken literally.

            >>> r, p, _, i = _as_regexs('a<foo>b<bar>c', False, False)
            >>> m = re.compile(''.join(r), re.MULTILINE | re.DOTALL)
            >>> m.match('axxbyyyc') is None # don't matched as <foo> is not xx
            True

            >>> m.match('a<foo>b<bar>c') is None # the strings <foo> <bar> are literals
            False

            >>> [n for n in sorted(i.values()) if n != None]
            []

            >>> i
            {}


           Otherwise we will fail:

            >>> _as_regexs('a<foo>b<foo>c', True, False)
            Traceback (most recent call last):
            <...>
            ValueError: <...>


        The tags' regexs will behave differently if normalize_whitespace
        is true or false.

        In the default, normalize_whitespace == False, case, a regex will
        include any amount of spaces, including new lines even if they are at
        the begin or end of the match, always

            >>> expected = 'a<foo>b'
            >>> regexs, p, c, _ = _as_regexs(expected, True, False)

            >>> regexs
            ('\\A', 'a', '(?P<foo>.*?)', 'b', '\\n*\\Z')

            >>> p
            (0, 0, 1, 6, 7)

            >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
            >>> m.match('a  \n 123\n\n b').groups()
            ('  \n 123\n\n ',)

        When normalize_whitespace is True it will depend if the tag is
        preceded or followed by a whitespace.

        When no whitespace is around the tag, the things work as if
        normalize_whitespace was false

           >>> expected = 'a<foo>b'
           >>> regexs, p, _, _ = _as_regexs(expected, True, True)

           >>> regexs
           ('\\A', 'a', '(?P<foo>.*?)', 'b', '\\s*\\Z')

           >>> p
           (0, 0, 1, 6, 7)

           >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
           >>> m.match('a  \n 123\n\n b').groups()
           ('  \n 123\n\n ',)

        But if we add some whitespace

           >>> expected = 'a <foo>b'
           >>> regexs, p, _, _ = _as_regexs(expected, True, True)

           >>> regexs
           ('\\A', 'a\\s+(?!\\s)', '(?P<foo>.*?)', 'b', '\\s*\\Z')

           >>> p
           (0, 0, 2, 7, 8)

           >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
           >>> m.match('a  \n 123\n\n b').groups()
           ('123\n\n ',)

           >>> expected = 'a<foo> b'
           >>> regexs, p, _, _ = _as_regexs(expected, True, True)

           >>> regexs
           ('\\A', 'a', '(?:(?P<foo>.+?)(?<!\\s))?\\s+(?!\\s)', 'b', '\\s*\\Z')

           >>> p
           (0, 0, 1, 7, 8)

           >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
           >>> m.match('a  \n 123\n\n b').groups()
           ('  \n 123',)

        If you want to ignore all the whitespace at the begin or end of the tag,
        just add a whitespace around it

           >>> expected = 'a\n<foo>\tb'
           >>> regexs, p, _, _ = _as_regexs(expected, True, True)

           >>> regexs
           ('\\A', 'a\\s+(?!\\s)', '(?:(?P<foo>.+?)(?<!\\s))?\\s*(?!\\s)', 'b', '\\s*\\Z')

           >>> p
           (0, 0, 2, 8, 9)

           >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
           >>> m.match('a  \n 123\n\n b').groups()
           ('123',)

           >>> m.match('a  \n \n\n b').groups('')
           ('',)

           >>> m.match('a  b').groups('')
           ('',)

           # The following is "wrong" as it should not match (2 whitespaces
           # are expected at least), but it is a current limitation of
           # the engine (1 whitespace is enough)
           >>> m.match('a b').groups('')
           ('',)

        Any trailing new line will be ignored

            >>> expected = '<foo>\n\n\n'
            >>> regexs, _, _, _ = _as_regexs(expected, True, False)

            >>> regexs
            ('\\A', '(?:(?P<foo>.+?)(?<!\\n))?', '\\n*\\Z')

            >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
            >>> m.match('   123  \n\n\n\n').groups()
            ('   123  ',)

            >>> expected = '<foo>'
            >>> regexs, _, _, _ = _as_regexs(expected, True, False)

            >>> regexs
            ('\\A', '(?:(?P<foo>.+?)(?<!\\n))?', '\\n*\\Z')

            >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
            >>> m.match('123\n\n\n\n').groups()
            ('123',)

        And if normalize_whitespace is True, any trailing whitespace.

           >>> expected = '<foo>  \n\n'
           >>> regexs, p, _, _ = _as_regexs(expected, True, True)

           >>> regexs
           ('\\A', '(?:(?P<foo>.+?)(?<!\\s))?', '\\s*\\Z')

           >>> p
           (0, 0, 5)

           >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
           >>> m.match('   123  \n\n\n\n').groups()
           ('   123',)

           >>> expected = ' <foo>  \n\n'
           >>> regexs, p, _, _ = _as_regexs(expected, True, True)

           >>> regexs
           ('\\A', '\\s+(?!\\s)', '(?:(?P<foo>.+?)(?<!\\s))?', '\\s*\\Z')

           >>> p
           (0, 0, 1, 6)

           >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
           >>> m.match('   123  \n\n\n\n').groups()
           ('123',)

           >>> expected = ' <foo>'
           >>> regexs, p, _, _ = _as_regexs(expected, True, True)

           >>> regexs
           ('\\A', '\\s+(?!\\s)', '(?:(?P<foo>.+?)(?<!\\s))?', '\\s*\\Z')

           >>> p
           (0, 0, 1, 6)

           >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
           >>> m.match('   123  \n\n\n\n').groups()
           ('123',)

        # Note: in a previous version of Byexample there was a bug when the
        # the last capture was *after* a new line.
        #
        # The original regex was (?P<foo>.*?)(?<!\\n) which worked if
        # the capture was not empty but when it wasn't, the whole failed.
        #
        # The problem is that (?<!\\n) means "not preceded by a new line"
        # and if (?P<foo>.*?) matches the empty string, the regex (?<!\\n)
        # follows immediately *after* the \n which fails the whole match.
        #
        # The fix was to set the tag matches *something* or the whole is
        # optional:
            >>> expected = '\n<foo>'
            >>> regexs, _, _, _ = _as_regexs(expected, True, False)

            >>> regexs
            ('\\A', '\\\n', '(?:(?P<foo>.+?)(?<!\\n))?', '\\n*\\Z')

            >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
            >>> m.match('\n123\n\n\n\n').groups()
            ('123',)

            >>> m.match('\n\n\n\n\n').groups()
            (None,)
        '''

        results = [(0, r'\A', 0, False)]
        push = results.append

        tags_by_idx = {}
        names_seen = set()

        state_label = 'INIT'
        saved_state = ()

        norm_ws = normalize_whitespace  # alias
        ws_regex= r'\s+(?!\s)'

        trailing_re = self.trailing_whitespace_regex() if norm_ws \
                      else self.trailing_newlines_regex()
        expected = trailing_re.sub('', expected)

        tokenizer = self.expected_tokenizer(expected, tags_enabled)

        while 1:
            charno, ttype, token = next(tokenizer)

            #print(state_label, saved_state, charno, ttype, token)
            if state_label == 'INIT':
                assert not saved_state
                if ttype == 'literals':
                    saved_state = (charno, token)
                    state_label = 'LIT'
                elif ttype in ('wspaces', 'newlines'):
                    if norm_ws:
                        if results[-1][-1]:
                            continue
                        push((charno, ws_regex, 1, True))
                    else:
                        push((charno, re.escape(token), len(token), False))
                elif ttype == 'tag':
                    saved_state = (charno, token)
                    state_label = 'TAG'
                elif ttype == 'end':
                    push((charno, trailing_re.pattern, 0, False))
                    break

            elif state_label == 'LIT':
                c, t = saved_state
                saved_state = ()

                if ttype == 'literals':
                    assert False
                elif ttype in ('wspaces', 'newlines'):
                    if norm_ws:
                        r = len(t) + 1
                        t = re.escape(t) + ws_regex
                        push((c, t, r, True))
                    else:
                        r = len(t) + len(token)
                        t = re.escape(t + token)
                        push((c, t, r, False))
                    state_label = 'INIT'
                elif ttype == 'tag':
                    push((c, re.escape(t), len(t), False))
                    saved_state = (charno, token)
                    state_label = 'TAG'
                elif ttype == 'end':
                    push((c, re.escape(t), len(t), False))
                    push((charno, trailing_re.pattern, 0, False))
                    break

            elif state_label == 'TAG':
                c, t = saved_state
                saved_state = ()

                name = self.name_of_tag_or_None(t)
                tags_by_idx[len(results)] = name

                if name in names_seen:
                    msg = "The named capture tag '%s' is repeated in " +\
                          "the %ith character."

                    raise ValueError(msg % (name, charno))

                if name is not None:
                    names_seen.add(name)

                ws_re_on_left = results[-1][-1]

                if ttype == 'literals':
                    retag = self.regex_of_tag(name, '')
                    push((c, retag, 0, False))
                    saved_state = (charno, token)
                    state_label = 'LIT'
                elif ttype in ('wspaces', 'newlines'):
                    retag = self.regex_of_tag(name, 's'*norm_ws)
                    if norm_ws:
                        if ws_re_on_left:
                            # we made "optional" the trailing whitespace
                            # (on right) because if the tag matches empty, the
                            # regex on the left will take care of this
                            push((c, retag+r'\s*(?!\s)', 0, True))
                        else:
                            push((c, retag+ws_regex, 0+1, True))
                    else:
                        push((c, retag, 0, False))
                        push((charno, re.escape(token), len(token), False))

                    state_label = 'INIT'
                elif ttype == 'tag':
                    msg = "Two consecutive capture tags were found at %ith character. " +\
                          "This is ambiguous."
                    raise ValueError(msg % charno)
                elif ttype == 'end':
                    retag = self.regex_of_tag(name, 's' if norm_ws else 'n')
                    push((c, retag, 0, False))
                    push((charno, trailing_re.pattern, 0, False))
                    break

        # make sure that the tokenizer was exhausted
        assert next(tokenizer, None) == None

        charnos, regexs, rcounts, _ = zip(*results)
        return regexs, charnos, rcounts, tags_by_idx

    def expected_as_regexs_TMP_NORM(self, expected, tags_enabled, normalize_whitespace):
        '''
        From the expected string create a list of regular expressions that
        joined with the flags re.MULTILINE | re.DOTALL, matches
        that string.

        This method returns four things:
            - a list of regexs: for literals, captures, wildcards, ...
            - a list with the character numbers, the positions in the expected
              string from where it was created each regex
            - a list of rcounts (see below)
            - a dict of non-literal 'regexs' names (capturing and non-capturing)
              also know as "tags" indexed by position.
              For non-capturing the name will be None.

            >>> from byexample.parser import ExampleParser
            >>> import re

            >>> parser = ExampleParser(0, 'utf8', None); parser.language = 'python'
            >>> _as_regexs = parser.expected_as_regexs_TMP_NORM

        The normalize_whitespace and tags_enabled flags modify how the regexs
        are built:
         - if normalize_whitespace is true, replace all the consecutive
           whitespaces by a single regular expression that matches any amount
           of whitespaces. The net effect is that regardless of
           the spaces in the expected, the regexp will ignore that.
           However we preserve the new line as 'regex's boundaries'

           >>> r, p, c, _ = _as_regexs('a  \n   b  \t\vc', True, True)

           >>> r
           ('\\A', 'a', '\\s+(?!\\s)', 'b', '\\s+(?!\\s)', 'c', '\\s*\\Z')

           >>> p
           (0, 0, 1, 7, 8, 12, 13)

           >>> m = re.compile(''.join(r), re.MULTILINE | re.DOTALL)
           >>> m.match('a b c') is not None
           True

           And also, count the consecutive whitespaces as a +1 when the
           rcount is computed (do not count each whitespace)

           >>> c
           (0, 1, 1, 1, 1, 1, 0)

        When normalize_whitespace is True it will depend if the tag is
        preceded or followed by a whitespace.

        When no whitespace is around the tag, the things work as if
        normalize_whitespace was false

           >>> expected = 'a<foo>b'
           >>> regexs, p, _, _ = _as_regexs(expected, True, True)

           >>> regexs
           ('\\A', 'a', '(?P<foo>.*?)', 'b', '\\s*\\Z')

           >>> p
           (0, 0, 1, 6, 7)

           >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
           >>> m.match('a  \n 123\n\n b').groups()
           ('  \n 123\n\n ',)

        But if we add some whitespace

           >>> expected = 'a <foo>b'
           >>> regexs, p, _, _ = _as_regexs(expected, True, True)

           >>> regexs
           ('\\A', 'a', '\\s+(?!\\s)', '(?P<foo>.*?)', 'b', '\\s*\\Z')

           >>> p
           (0, 0, 1, 2, 7, 8)

           >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
           >>> m.match('a  \n 123\n\n b').groups()
           ('123\n\n ',)

           >>> expected = 'a<foo> b'
           >>> regexs, p, _, _ = _as_regexs(expected, True, True)

           >>> regexs
           ('\\A', 'a', '(?P<foo>.*?)(?<!\\s)', '\\s+(?!\\s)', 'b', '\\s*\\Z')

           >>> p
           (0, 0, 1, 6, 7, 8)

           >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
           >>> m.match('a  \n 123\n\n b').groups()
           ('  \n 123',)

        If you want to ignore all the whitespace at the begin or end of the tag,
        just add a whitespace around it

           >>> expected = 'a\n<foo>\tb'
           >>> regexs, p, _, _ = _as_regexs(expected, True, True)

           >>> regexs           # byexample: +norm-ws
           ('\\A', 'a', '\\s', '(?:\\s*(?!\\s)(?P<foo>.+?)(?<!\\s))?', '\\s+(?!\\s)', 'b', '\\s*\\Z')

           >>> p
           (0, 0, 1, 2, 7, 8, 9)

           >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
           >>> m.match('a  \n 123\n\n b').groups()
           ('123',)

           >>> m.match('a  \n \n\n b').groups('')
           ('',)

           >>> m.match('a  b').groups('')
           ('',)

           >>> m.match('a b') is None
           True

        And if normalize_whitespace is True, any trailing whitespace.

           >>> expected = '<foo>  \n\n'
           >>> regexs, p, _, _ = _as_regexs(expected, True, True)

           >>> regexs
           ('\\A', '(?P<foo>.*?)(?<!\\s)', '\\s*\\Z')

           >>> p
           (0, 0, 5)

           >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
           >>> m.match('   123  \n\n\n\n').groups()
           ('   123',)

           >>> expected = ' <foo>  \n\n'
           >>> regexs, p, _, _ = _as_regexs(expected, True, True)

           >>> regexs
           ('\\A', '\\s', '(?:\\s*(?!\\s)(?P<foo>.+?)(?<!\\s))?', '\\s*\\Z')

           >>> p
           (0, 0, 1, 6)

           >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
           >>> m.match('   123  \n\n\n\n').groups()
           ('123',)

           >>> expected = ' <foo>'
           >>> regexs, p, _, _ = _as_regexs(expected, True, True)

           >>> regexs
           ('\\A', '\\s', '(?:\\s*(?!\\s)(?P<foo>.+?)(?<!\\s))?', '\\s*\\Z')

           >>> p
           (0, 0, 1, 6)

           >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
           >>> m.match('   123  \n\n\n\n').groups()
           ('123',)
        '''

        norm_ws = normalize_whitespace  # alias
        assert norm_ws

        trailing_re = self.trailing_whitespace_regex() if norm_ws \
                      else self.trailing_newlines_regex()
        expected = trailing_re.sub('', expected)

        tokenizer = self.expected_tokenizer(expected, tags_enabled)

        sm = SM_NormWS(self)
        while not sm.ended():
            charno, ttype, token = next(tokenizer, (None, None, None))
            sm.feed(charno, ttype, token)

            assert (ttype == None and sm.ended()) or \
                    (ttype != None and not sm.ended())

        charnos, regexs, rcounts = zip(*sm.results)
        return regexs, charnos, rcounts, sm.tags_by_idx

    def expected_as_regexs_TMP(self, expected, tags_enabled, normalize_whitespace):
        '''
            >>> from byexample.parser import ExampleParser
            >>> import re

            >>> parser = ExampleParser(0, 'utf8', None); parser.language = 'python'
            >>> _as_regexs = parser.expected_as_regexs_TMP

            >>> expected = 'a<foo>b<bar>c'
            >>> regexs, charnos, rcounts, tags_by_idx = _as_regexs(expected, True, False)

        We return the regexs

            >>> regexs
            ('\\A', 'a', '(?P<foo>.*?)', 'b', '(?P<bar>.*?)', 'c', '\\n*\\Z')

            >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
            >>> m.match('axxbyyyc').groups()
            ('xx', 'yyy')

        And we can see the charnos or the position in the original expected
        string from where each regex was built

            >>> charnos
            (0, 0, 1, 6, 7, 12, 13)

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

        The following example shows what happen when we use a non-capturing tag
        (ellipsis tag) also known as unnamed tag and what happen when we use
        a tag name with a - (Python regexs don't support this character):

            >>> expected = 'a<...>b<foo-bar>c'
            >>> regexs, _, _, tags_by_idx = _as_regexs(expected, True, False)

            >>> regexs
            ('\\A', 'a', '(?:.*)', 'b', '(?P<foo_bar>.*?)', 'c', '\\n*\\Z')

            >>> list(sorted(n for n in tags_by_idx.values() if n != None))
            ['foo-bar']

            >>> tags_by_idx
            {2: None, 4: 'foo-bar'}

        Notice how the unnamed tag is mapped to None and how a name with a -
        works out of the box with a subtle change: the regex name has a _
        instead of a -.

        Also notice that the unnamed tag's regex is greedy (.*) while the
        named tag's one is non-greedy (.*?).
        The reason of this is that typically the unnamed tag is used to
        match long unwanted strings while the named tag is for small
        and interesting strings.

        This heuristic does not claim to be bulletproof however.

        Multi line strings will yield splitted regexs: one regex per line.
        This in on purpose to support the concept of incremental matching
        (match the whole regex matching one regex at time)

            >>> expected = 'a\n<foo>bcd\nefg<bar>hi'
            >>> regexs, _, rcounts, _ = _as_regexs(expected, True, False)

            >>> regexs          # byexample: +norm-ws
            ('\\A',
             'a',
             '\\\n',
             '(?P<foo>.*?)',
             'bcd',
             '\\\n',
             'efg',
             '(?P<bar>.*?)',
             'hi',
             '\\n*\\Z')

        Notice also how the tags don't count as 'real counts' (zero).
        The first and the last regex either.

            >>> rcounts
            (0, 1, 1, 0, 3, 1, 3, 0, 2, 0)

        The normalize_whitespace and tags_enabled flags modify how the regexs
        are built:

         - if tags_enabled is true, interpret the tags <...> as regexs.

            >>> r, p, _, i = _as_regexs('a<foo>b<bar>c', True, False)
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
            >>> _as_regexs('a<foo><bar>c', True, False)
            Traceback (most recent call last):
            <...>
            ValueError: <...>

         - if tags_enabled is False, all the <...> tags are taken literally.

            >>> r, p, _, i = _as_regexs('a<foo>b<bar>c', False, False)
            >>> m = re.compile(''.join(r), re.MULTILINE | re.DOTALL)
            >>> m.match('axxbyyyc') is None # don't matched as <foo> is not xx
            True

            >>> m.match('a<foo>b<bar>c') is None # the strings <foo> <bar> are literals
            False

            >>> [n for n in sorted(i.values()) if n != None]
            []

            >>> i
            {}


           Otherwise we will fail:

            >>> _as_regexs('a<foo>b<foo>c', True, False)
            Traceback (most recent call last):
            <...>
            ValueError: <...>


        The tags' regexs will behave differently if normalize_whitespace
        is true or false.

        In the default, normalize_whitespace == False, case, a regex will
        include any amount of spaces, including new lines even if they are at
        the begin or end of the match, always

            >>> expected = 'a<foo>b'
            >>> regexs, p, c, _ = _as_regexs(expected, True, False)

            >>> regexs
            ('\\A', 'a', '(?P<foo>.*?)', 'b', '\\n*\\Z')

            >>> p
            (0, 0, 1, 6, 7)

            >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
            >>> m.match('a  \n 123\n\n b').groups()
            ('  \n 123\n\n ',)

        Any trailing new line will be ignored

            >>> expected = '<foo>\n\n\n'
            >>> regexs, _, _, _ = _as_regexs(expected, True, False)

            >>> regexs
            ('\\A', '(?:(?P<foo>.+?)(?<!\\n))?', '\\n*\\Z')

            >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
            >>> m.match('   123  \n\n\n\n').groups()
            ('   123  ',)

            >>> expected = '<foo>'
            >>> regexs, _, _, _ = _as_regexs(expected, True, False)

            >>> regexs
            ('\\A', '(?:(?P<foo>.+?)(?<!\\n))?', '\\n*\\Z')

            >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
            >>> m.match('123\n\n\n\n').groups()
            ('123',)


        # Note: in a previous version of Byexample there was a bug when the
        # the last capture was *after* a new line.
        #
        # The original regex was (?P<foo>.*?)(?<!\\n) which worked if
        # the capture was not empty but when it wasn't, the whole failed.
        #
        # The problem is that (?<!\\n) means "not preceded by a new line"
        # and if (?P<foo>.*?) matches the empty string, the regex (?<!\\n)
        # follows immediately *after* the \n which fails the whole match.
        #
        # The fix was to set the tag matches *something* or the whole is
        # optional:
            >>> expected = '\n<foo>'
            >>> regexs, _, _, _ = _as_regexs(expected, True, False)

            >>> regexs
            ('\\A', '\\\n', '(?:(?P<foo>.+?)(?<!\\n))?', '\\n*\\Z')

            >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
            >>> m.match('\n123\n\n\n\n').groups()
            ('123',)

            >>> m.match('\n\n\n\n\n').groups()
            (None,)
        '''
        norm_ws = normalize_whitespace  # alias
        assert not norm_ws

        trailing_re = self.trailing_whitespace_regex() if norm_ws \
                      else self.trailing_newlines_regex()
        expected = trailing_re.sub('', expected)

        tokenizer = self.expected_tokenizer(expected, tags_enabled)

        sm = SM_NotNormWS(self)
        while not sm.ended():
            charno, ttype, token = next(tokenizer, (None, None, None))
            sm.feed(charno, ttype, token)

            assert (ttype == None and sm.ended()) or \
                    (ttype != None and not sm.ended())

        charnos, regexs, rcounts = zip(*sm.results)
        return regexs, charnos, rcounts, sm.tags_by_idx

    def name_of_tag_or_None(self, tag):
        name = self.capture_tag_regex()['full'].match(tag).group('name')
        if name == self.ellipsis_marker():
            name = None

        return name

    def regex_of_tag(self, name, lookahead):
        '''
            >>> from byexample.parser import ExampleParser
            >>> import re

            >>> parser = ExampleParser(0, 'utf8', None); parser.language = 'python'
            >>> regex_of_tag = parser.regex_of_tag

        A tag, named or unnamed, will try to capture anything.
            >>> regex_of_tag('foo', '')
            '(?P<foo>.*?)'

            >>> regex_of_tag(None, '')
            '(?:.*)'

        The name of the tag is 'normalized': Python's regexs
        must be valid Python names
            >>> regex_of_tag('foo-bar', '')
            '(?P<foo_bar>.*?)'

        If a whitespace regex is on his right, the tag must
        not end in a whitespace
            >>> regex_of_tag('foo', 's')
            '(?:(?P<foo>.+?)(?<!\\s))?'

        If the tag is followed by a regex that consume any
        newline, it must not consume them
            >>> regex_of_tag('foo', 'n')
            '(?:(?P<foo>.+?)(?<!\\n))?'

        # Note: in a previous version of byexample the regexs were like
        #   (?P<foo>.*?)(?<!\\n)
        #
        # This works but it *may fail* if the capture is empty.
        #
        # The problem is that (?<!\\n) means "not preceded by a new line".
        # If (?P<foo>.*?) matches *the empty string*, the regex (?<!\\n)
        # will be on the strings *before* the tag and if that ends in a newline
        # the whole match fails always.
        #
        # In other words, '\n<foo>' would fail.
        #
        # The solution was to change the internal regex as 'one or more' to
        # ensure that it will never be empty and wrap all as 'optional'
        '''

        assert lookahead in ('s', 'n', '')
        if lookahead == 's':
            posfix = r'(?<!\s)' # do not end with a whitespace
        elif lookahead == 'n':
            posfix = r'(?<!\n)' # do not end with a newline
        else:
            posfix = ""         # free

        if name is None:
            regex = r'(?:.{rep})'
        else:
            name = tag_name_as_regex_name(name)
            regex = r'(?P<{name}>.{rep}?)'
            #regex = r'(?P<{name}>(?:[^\s\n]{rep}?|[^\n]{rep}?|.{rep}?))'

        if posfix:
            regex = regex.format(name=name, rep='+') + posfix
            regex = r'(?:' + regex + ')?'
        else:
            regex = regex.format(name=name, rep='*')

        return regex

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

        return self._extend_parser_and_parse_options_strictly_and_cache(optlist)

    def _extend_parser_and_parse_options_strictly(self, optlist):
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

    def _extend_parser_and_parse_options_strictly_and_cache(self, optlist):
        ''' This is a thin wrapper around _extend_parser_and_parse_options_strictly
            to cache its results based on the optlist.

            Note that two different lists may represent the same options set
            like:
                l1 = [-foo, a, +bar, "1 2 3"]   => -foo=1 and +bar="1 2 3"
                l2 = [+bar, "1 2 3", -foo, a]   => -foo=1 and +bar="1 2 3"

            This cache system is very naive and will save two entries for
            those.

            And it works under the assumption that if a given example's options
            were parsed by X extended parser, the *same* options of another
            example *would* be parsed by the same *X parser* and it *would*
            yield the *same* result.

            If the parser object or its behaviour changes in runtime, you
            will need to override this method and change or disable the cache.
            '''
        try:
            return self._opts_cache[tuple(optlist)]
        except KeyError:
            val = self._extend_parser_and_parse_options_strictly(optlist)
            self._opts_cache[tuple(optlist)] = val
            return val

    def get_extended_option_parser(self, parent_parser, **kw):
        ''' This will call ExtendOptionParserMixin.get_extended_option_parser
            and it will cache its result.

            If you don't want to cache anything, you can override this method
            and call ExtendOptionParserMixin.get_extended_option_parser directly.
            '''
        if self._optparser_extended_cache == None:
            optparser_extended = ExtendOptionParserMixin.get_extended_option_parser(
                                        self, parent_parser)
            self._optparser_extended_cache = optparser_extended

        return self._optparser_extended_cache
