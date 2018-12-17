import re
from .common import constant

INIT, WS, LIT, TAG, END, TWOTAGS, EXHAUSTED, ERROR = range(8)
tWS = ('wspaces', 'newlines')
tLIT = ('wspaces', 'newlines', 'literals')

'''
>>> from byexample.parser_sm import SM, SM_NormWS, SM_NotNormWS
>>> import re

>>> _tag_regex = re.compile(r"<(?P<name>(?:[^\W_]|-|\.)+)>")
>>> _tag_split_regex = re.compile(r"(<(?:[^\W_]|-|\.)+>)")
>>> _ellipsis_marker = '...'

>>> sm = SM(_tag_regex, _tag_split_regex, _ellipsis_marker)
>>> sm_norm_ws = SM_NormWS(_tag_regex, _tag_split_regex, _ellipsis_marker)
>>> sm_lit = SM_NotNormWS(_tag_regex, _tag_split_regex, _ellipsis_marker)

>>> def match(regexs, string):
...     r = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
...     return r.match(string)
'''

class SM(object):
    def __init__(self, capture_tag_regex, capture_tag_split_regex, ellipsis_marker):
        self.capture_tag_regex = capture_tag_regex
        self.capture_tag_split_regex = capture_tag_split_regex
        self.ellipsis_marker = ellipsis_marker

        self.reset()

    def reset(self):
        self.stash = []
        self.results = []
        self.state = INIT

        self.tags_by_idx = {}
        self.names_seen = set()

        self.emit(0, r'\A', 0)

    @constant
    def one_or_more_ws_capture_regex(self):
        return re.compile(r'(\s+)', re.MULTILINE | re.DOTALL)

    @constant
    def one_or_more_nl_capture_regex(self):
        return re.compile(r'(\n+)', re.MULTILINE | re.DOTALL)

    def ended(self):
        return self.state in (EXHAUSTED, ERROR)

    def push(self, charno, token):
        return self.stash.append((charno, token))

    def pull(self):
        return self.stash.pop(0)

    def drop(self, last=False):
        self.stash.pop(-1 if last else 0)

    def emit(self, charno, regex, rcount):
        item = (charno, regex, rcount)
        self.results.append(item)
        return item

    def emit_literals(self):
        '''
            The literals are escaped to be valid regexs without
            any special meaning.

            >>> sm.push(1, 'zaz+')
            >>> sm.emit_literals()
            (1, 'zaz\\+', 4)

            The rcount of them is just the count of characters.
        '''
        charno, l = self.pull()
        rx = re.escape(l)
        rc = len(l)

        return self.emit(charno, rx, rc)

    def name_of_tag_or_None(self, tag):
        name = self.capture_tag_regex.match(tag).group('name')
        if name == self.ellipsis_marker:
            name = None

        return name

    def emit_tag(self, ctx, endline):
        '''
            Emit the regex of a capture tag given a context,
            always with a rcount of zero.

            When the tag is not surrounded by a whitespace nor
            at the end of the expected, the tag can match anything.

            Depending on the tag name, the regex can be non-capture.
            >>> sm.push(0, '<...>')
            >>> sm.emit_tag(ctx='0', endline=False)
            (0, '(?:.*?)', 0)

            If the tag is named, the regex will have that name. Keep in
            mind that the character '-' will be mapped to '_' because
            the regex names in Python must be valid Python names.
            >>> sm.push(1, '<foo-bar>')
            >>> sm.emit_tag(ctx='0', endline=False)
            (1, '(?P<foo_bar>.*?)', 0)

            When a tag have whitespace at its left, nothing happens
            >>> sm.push(2, '<bar>')
            >>> sm.emit_tag(ctx='l', endline=False)
            (2, '(?P<bar>.*?)', 0)

            But if the whitespace is at its right, the regex must not
            match it.
            >>> sm.push(3, '<baz>')
            >>> sm.emit_tag(ctx='r', endline=False)
            (3, '(?P<baz>.*?)(?<!\\s)', 0)

            Something similar happens if it is at the end: the regex must
            not match any newline on its right.
            Because it is possible that a newline is on his left, the regex
            must also protect itself in case that it matches empty.
            >>> sm.push(4, '<zaz>')
            >>> sm.emit_tag(ctx='n', endline=False)
            (4, '(?:(?P<zaz>.+?)(?<!\\n))?', 0)

            The more complex scenario happens when the tag is surrounded
            by whitespace. Like before, the regex must take care of what
            happen if matches empty.
            >>> sm.push(5, '<sax>')
            >>> sm.emit_tag(ctx='b', endline=False)
            (5, '(?:\\s*(?!\\s)(?P<sax>.+?)(?<!\\s))?', 0)

            Duplicated names are not allowed
            >>> sm.push(6, '<sax>')
            >>> sm.emit_tag(ctx='0', endline=False)
            Traceback<...>
            ValueError: The named capture tag 'sax' is repeated in the 6th character.

            The regexs are non-greedy by default with one exception: if
            the tag is unamed and it its at the end of a line
            (<endline> is True) then the regex will be greedy:
            >>> sm.push(0, '<...>')
            >>> sm.emit_tag(ctx='0', endline=True)
            (0, '(?:.*)', 0)

        '''
        assert ctx in ('l', 'r', 'b', '0', 'n')
        charno, tag = self.pull()

        name = self.name_of_tag_or_None(tag)
        self.tags_by_idx[len(self.results)] = name

        if name in self.names_seen:
            msg = "The named capture tag '%s' is repeated in " +\
                  "the %ith character."

            raise ValueError(msg % (name, charno))

        if name is not None:
            self.names_seen.add(name)

        if ctx in ('l', '0'):
            rx = r'({capture}.*{greedy})'
        elif ctx == 'r':
            rx = r'({capture}.*{greedy})(?<!\s)'
        elif ctx == 'b':
            rx = r'(?:\s*(?!\s)({capture}.+{greedy})(?<!\s))?'
        elif ctx == 'n':
            rx = r'(?:({capture}.+{greedy})(?<!\n))?'
        else:
            assert False

        greedy = r'?'   # not greedy
        if not name and endline:
            greedy = r''    # yes, greedy

        rx = rx.format(capture=r'?P<%s>' % name.replace('-', '_') if name else r'?:',
                greedy=greedy)
        rc = 0
        return self.emit(charno, rx, rc)

    def emit_eof(self, ws):
        '''
            >>> sm.push(0, None)
            >>> sm.emit_eof(ws='s')
            (0, '\\s*\\Z', 0)

            >>> sm.push(0, None)
            >>> sm.emit_eof(ws='n')
            (0, '\\n*\\Z', 0)
        '''
        assert ws in ('s', 'n')
        charno, _ = self.pull()
        rx = r'\{ws}*\Z'.format(ws=ws)
        rc = 0
        return self.emit(charno, rx, rc)

    def expected_tokenizer(self, expected_str, tags_enabled):
        ''' Iterate over the interesting tokens of the expected string:
             - newlines     - wspaces     - literals    - tag

            >>> _tokenizer = sm.expected_tokenizer

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
        tag_splitter = self.capture_tag_split_regex

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

    def parse(self, expected, tags_enabled):
        self.reset()
        tokenizer = self.expected_tokenizer(expected, tags_enabled)

        while not self.ended():
            charno, ttype, token = next(tokenizer, (None, None, None))
            self.feed(charno, ttype, token)

            assert (ttype == None and self.ended()) or \
                    (ttype != None and not self.ended())

        charnos, regexs, rcounts = zip(*self.results)
        return regexs, charnos, rcounts, self.tags_by_idx

class SM_NormWS(SM):
    def __init__(self, capture_tag_regex, capture_tag_split_regex, ellipsis_marker):
        SM.__init__(self, capture_tag_regex, capture_tag_split_regex, ellipsis_marker)

    @constant
    def trailing_whitespace_regex(self):
        return re.compile(r'\s*\Z', re.MULTILINE | re.DOTALL)

    def emit_ws(self, just_one=False):
        charno, _ = self.pull()
        if just_one:
            rx = r'\s'
        else:
            rx = r'\s+(?!\s)'
        rc = 1

        return self.emit(charno, rx, rc)

    def emit_tag(self, ctx, endline):
        assert ctx in ('l', 'r', 'b', '0')
        return SM.emit_tag(self, ctx, endline)

    def emit_eof(self, ws):
        assert ws == 's'
        return SM.emit_eof(self, ws)

    def feed(self, charno, ttype, token):
        push = self.push
        drop = self.drop

        push(charno, token)
        stash_size = len(self.stash)
        if self.state == INIT:
            assert stash_size == 1
            if ttype in tWS:
                self.state = WS
            elif ttype == 'literals':
                self.state = LIT
            elif ttype == 'tag':
                self.state = TAG
            elif ttype == 'end':
                self.state = END
            else:
                assert False
        elif self.state == WS:
            assert stash_size == 2
            if ttype in tWS:
                self.drop(last=True)  # drop the last pushed wspaces/newlines
                self.state = WS
            elif ttype == 'literals':
                self.emit_ws()
                self.state = LIT
            elif ttype == 'tag':
                self.state = (WS, TAG)
            elif ttype == 'end':
                charno, _ = self.pull()  # get the position of the wspaces/newlines
                _, token = self.pull() # get the end token
                push(charno, token)
                self.state = END # ignore the first wspaces/newlines token
            else:
                assert False
        elif self.state == LIT:
            assert stash_size == 2
            if ttype in tWS:
                self.emit_literals()
                self.state = WS
            elif ttype == 'literals':
                self.emit_literals()
                self.state = LIT
            elif ttype == 'tag':
                self.emit_literals()
                self.state = TAG
            elif ttype == 'end':
                self.emit_literals()
                self.state = END
            else:
                assert False
        elif self.state == TAG:
            assert stash_size == 2
            if ttype in tWS:
                self.emit_tag(ctx='r', endline=(ttype=='newlines'))
                self.state = WS
            elif ttype == 'literals':
                self.emit_tag(ctx='0', endline=False)
                self.state = LIT
            elif ttype == 'tag':
                self.state = TWOTAGS
            elif ttype == 'end':
                self.emit_tag(ctx='r', endline=True)
                self.state = END
            else:
                assert False
        elif self.state == END:
            assert stash_size == 2
            assert ttype is None    # next token doesn't exist: tokenizer exhausted
            drop(last=True)
            self.emit_eof(ws='s')
            self.state = EXHAUSTED
        elif self.state == (WS, TAG):
            assert stash_size == 3
            if ttype in tWS:
                self.emit_ws(just_one=True)
                self.emit_tag(ctx='b', endline=(ttype=='newlines'))
                self.state = WS
            elif ttype == 'literals':
                self.emit_ws()
                self.emit_tag(ctx='l', endline=False)
                self.state = LIT
            elif ttype == 'tag':
                drop() # drop the WS, we will not use it
                self.state = TWOTAGS
            elif ttype == 'end':
                self.emit_ws(just_one=True)
                self.emit_tag(ctx='b', endline=True)
                self.state = END
            else:
                assert False
        elif self.state == TWOTAGS:
            assert stash_size == 3
            self.state = ERROR
            drop(last=True)  # don't care what we read next
            drop(last=True) # don't care the second tag
            charno, _ = self.pull()
            msg = "Two consecutive capture tags were found at %ith character. " +\
                  "This is ambiguous."
            raise ValueError(msg % charno)
        elif self.state in (EXHAUSTED, ERROR):
            assert False
        else:
            assert False

    def parse(self, expected, tags_enabled):
        '''
            >>> _as_regexs = sm_norm_ws.parse

            Parse a given <expected> string and return a list
            of regular expressions that joined matches the original
            string.

            The regexs will ignore the amount of whitespaces in the
            <expected> yielding a '\s+' regex for them (one or more
            whitespaces of any kind).

            >>> r, p, c, _ = _as_regexs('a  \n   b  \t\vc', True)

            >>> r
            ('\\A', 'a', '\\s+(?!\\s)', 'b', '\\s+(?!\\s)', 'c', '\\s*\\Z')

            >>> match(r, 'a b c') is not None
            True

            Next to the regexs, the parse method will return the positions
            of each regex in the <expected> (from where the regexs were built)

            >>> p
            (0, 0, 1, 7, 8, 12, 13)

            And also will return the 'rcount', a measure of how many bytes
            consume each regex. For any amount of whitespaces, its rcount is
            always 1.

            >>> c
            (0, 1, 1, 1, 1, 1, 0)

            Because we use a regex for each whitespace, we need to take
            care of how these regexs interact with the regex of a capture
            tag.

            When the tag is not surrounded by any whitespace, the regex
            will capture anything

            >>> expected = 'a<foo>b'
            >>> regexs, p, _, _ = _as_regexs(expected, True)

            >>> regexs
            ('\\A', 'a', '(?P<foo>.*?)', 'b', '\\s*\\Z')

            >>> p
            (0, 0, 1, 6, 7)

            >>> match(regexs, 'a  \n 123\n\n b').groups()
            ('  \n 123\n\n ',)

            But if we add some whitespace on its left or its right we need
            to make sure that the tag will not consume any whitespace from
            its left or right

            >>> expected = 'a <foo>b'
            >>> regexs, p, _, _ = _as_regexs(expected, True)

            >>> regexs               # byexample: -tags
            ('\\A', 'a', '\\s+(?!\\s)', '(?P<foo>.*?)', 'b', '\\s*\\Z')

            >>> p
            (0, 0, 1, 2, 7, 8)

            >>> match(regexs, 'a  \n 123\n\n b').groups()
            ('123\n\n ',)

            >>> expected = 'a<foo> b'
            >>> regexs, p, _, _ = _as_regexs(expected, True)

            >>> regexs               # byexample: -tags
            ('\\A', 'a', '(?P<foo>.*?)(?<!\\s)', '\\s+(?!\\s)', 'b', '\\s*\\Z')

            >>> p
            (0, 0, 1, 6, 7, 8)

            >>> match(regexs, 'a  \n 123\n\n b').groups()
            ('  \n 123',)

            The most complex scenario happens when the tag has whitespaces
            on its left *and* its right.

            >>> expected = 'a\n<foo>\tb'
            >>> regexs, p, _, _ = _as_regexs(expected, True)

            >>> regexs           # byexample: +norm-ws -tags
            ('\\A', 'a', '\\s', '(?:\\s*(?!\\s)(?P<foo>.+?)(?<!\\s))?', '\\s+(?!\\s)', 'b', '\\s*\\Z')

            >>> p
            (0, 0, 1, 2, 7, 8, 9)

            >>> match(regexs, 'a  \n 123\n\n b').groups()
            ('123',)

            >>> match(regexs, 'a  \n \n\n b').groups('')
            ('',)

            Notice how the <expected> request at least one whitespace on the
            left of the tag *and* at least one whitespace on its right.

            The following, with two whitespaces works:
            >>> match(regexs, 'a  b').groups('')
            ('',)

            But this one will note:
            >>> match(regexs, 'a b') is None
            True

            The parse method adds an extra regex at the end to remove any
            trailing whitespace. This must also needs to be taken into
            consideration.

            >>> expected = '<foo>  \n\n'
            >>> regexs, p, _, _ = _as_regexs(expected, True)

            >>> regexs               # byexample: -tags
            ('\\A', '(?P<foo>.*?)(?<!\\s)', '\\s*\\Z')

            >>> p
            (0, 0, 5)

            >>> match(regexs, '   123  \n\n\n\n').groups()
            ('   123',)

            >>> expected = ' <foo>  \n\n'
            >>> regexs, p, _, _ = _as_regexs(expected, True)

            >>> regexs               # byexample: -tags
            ('\\A', '\\s', '(?:\\s*(?!\\s)(?P<foo>.+?)(?<!\\s))?', '\\s*\\Z')

            >>> p
            (0, 0, 1, 6)

            >>> match(regexs, '   123  \n\n\n\n').groups()
            ('123',)

            >>> expected = ' <foo>'
            >>> regexs, p, _, _ = _as_regexs(expected, True)

            >>> regexs               # byexample: -tags
            ('\\A', '\\s', '(?:\\s*(?!\\s)(?P<foo>.+?)(?<!\\s))?', '\\s*\\Z')

            >>> p
            (0, 0, 1, 6)

            >>> match(regexs, '   123  \n\n\n\n').groups()
            ('123',)

            >>> expected = '<foo>'
            >>> regexs, p, _, _ = _as_regexs(expected, True)

            >>> regexs               # byexample: -tags
            ('\\A', '(?P<foo>.*?)(?<!\\s)', '\\s*\\Z')

            >>> p
            (0, 0, 5)

            >>> match(regexs, '   123  \n\n\n\n').groups()
            ('   123',)

            >>> expected = ' '
            >>> regexs, p, _, _ = _as_regexs(expected, True)

            >>> regexs               # byexample: -tags
            ('\\A', '\\s*\\Z')

            >>> p
            (0, 0)

            >>> expected = ''
            >>> regexs, p, _, _ = _as_regexs(expected, True)

            >>> regexs               # byexample: -tags
            ('\\A', '\\s*\\Z')

            >>> p
            (0, 0)
        '''
        return SM.parse(self, expected, tags_enabled)

class SM_NotNormWS(SM):
    def __init__(self, capture_tag_regex, capture_tag_split_regex, ellipsis_marker):
        SM.__init__(self, capture_tag_regex, capture_tag_split_regex, ellipsis_marker)

    @constant
    def trailing_newlines_regex(self):
        return re.compile(r'\n*\Z', re.MULTILINE | re.DOTALL)

    def emit_tag(self, ctx, endline):
        assert ctx in ('n', '0')
        return SM.emit_tag(self, ctx, endline)

    def emit_eof(self, ws):
        assert ws == 'n'
        return SM.emit_eof(self, ws)

    def feed(self, charno, ttype, token):
        push = self.push
        drop = self.drop

        push(charno, token)
        stash_size = len(self.stash)
        if self.state == INIT:
            assert stash_size == 1
            if ttype in tLIT:
                self.state = LIT
            elif ttype == 'tag':
                self.state = TAG
            elif ttype == 'end':
                self.state = END
            else:
                assert False
        elif self.state == LIT:
            assert stash_size == 2
            if ttype in tLIT:
                self.emit_literals()
                self.state = LIT
            elif ttype == 'tag':
                self.emit_literals()
                self.state = TAG
            elif ttype == 'end':
                self.emit_literals()
                self.state = END
            else:
                assert False
        elif self.state == TAG:
            assert stash_size == 2
            if ttype in tLIT:
                self.emit_tag(ctx='0', endline=(ttype=='newlines'))
                self.state = LIT
            elif ttype == 'tag':
                self.state = TWOTAGS
            elif ttype == 'end':
                self.emit_tag(ctx='n', endline=True)
                self.state = END
            else:
                assert False
        elif self.state == END:
            assert stash_size == 2
            assert ttype is None    # next token doesn't exist: tokenizer exhausted
            drop(last=True)
            self.emit_eof(ws='n')
            self.state = EXHAUSTED
        elif self.state == TWOTAGS:
            assert stash_size == 3
            self.state = ERROR
            drop(last=True)  # don't care what we read next
            drop(last=True) # don't care the second tag
            charno, _ = self.pull()
            msg = "Two consecutive capture tags were found at %ith character. " +\
                  "This is ambiguous."
            raise ValueError(msg % charno)
        elif self.state in (EXHAUSTED, ERROR):
            assert False
        else:
            assert False

    def parse(self, expected, tags_enabled):
        '''
            >>> _as_regexs = sm_lit.parse

            Parse a given <expected> string and return a list
            of regular expressions that joined matches the original
            string.

            >>> expected = 'a<foo>b<b-b>c<...>d'
            >>> regexs, charnos, rcounts, tags_by_idx = _as_regexs(expected, True)

            >>> regexs              # byexample: -tags +norm-ws
            ('\\A', 'a', '(?P<foo>.*?)', 'b', '(?P<b_b>.*?)', 'c', '(?:.*?)', 'd', '\\n*\\Z')

            >>> match(regexs, 'axxbyyyczzd').groups()
            ('xx', 'yyy')

            Along with the regexs the method returns the position
            in the original expected string from where each regex was built

            >>> charnos
            (0, 0, 1, 6, 7, 12, 13, 18, 19)

            >>> len(expected) == charnos[-1]
            True

            A rcount or 'real count' count how many literals are.

            >>> rcounts
            (0, 1, 0, 1, 0, 1, 0, 1, 0)

            We can see the names of the capturing regexs (named capture tags)
            or None if they are unnamed and the position of the tags in
            the regex list.

            >>> tags_by_idx
            {2: 'foo', 4: 'b-b', 6: None}

            Notice how the unnamed tag is mapped to None and how a name with a -
            works out of the box with a subtle change: the regex name has a _
            instead of a -.

            Also notice that the unnamed tag's regex is greedy (.*) if
            it is at the end of a line.

            The reason of this is that typically the unnamed tag is used to
            match long unwanted strings while the unamed tags in the middle
            of a line or named tags are for small strings.

            This heuristic does not claim to be bulletproof however.

            The regexs are split on each word boundary: spaces and newlines.
            This in on purpose to support the concept of incremental matching
            (match the whole regex matching one regex at time)

            >>> expected = 'a\n<foo>bcd\nefg<bar>hi'
            >>> regexs, _, rcounts, _ = _as_regexs(expected, True)

            >>> regexs          # byexample: +norm-ws -tags
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

            >>> rcounts
            (0, 1, 1, 0, 3, 1, 3, 0, 2, 0)

            Note that if two or more tags are consecutive,
            we will raise an exception as this is ambiguous:

            >>> # but here? foo is 'x' and bar 'xyyy'?, '' and 'xxyyy', or ....
            >>> _as_regexs('a<foo><bar>c', True)
            Traceback (most recent call last):
            <...>
            ValueError: <...>

            If tags_enabled is False, all the <...> tags are taken literally.

            >>> r, p, _, i = _as_regexs('a<foo>b<bar>c', False)
            >>> match(r, 'axxbyyyc') is None # don't matched as <foo> is not xx
            True

            >>> match(r, 'a<foo>b<bar>c') is None # the strings <foo> <bar> are literals
            False

            >>> i
            {}

            The tag names cannot be repeated:

            >>> _as_regexs('a<foo>b<foo>c', True)
            Traceback (most recent call last):
            <...>
            ValueError: <...>

            Any trailing new line will be ignored

            >>> expected = '<foo>\n\n\n'
            >>> regexs, _, _, _ = _as_regexs(expected, True)

            >>> regexs          # byexample: -tags
            ('\\A', '(?:(?P<foo>.+?)(?<!\\n))?', '\\n*\\Z')

            >>> match(regexs, '   123  \n\n\n\n').groups()
            ('   123  ',)

            >>> expected = '<foo>'
            >>> regexs, _, _, _ = _as_regexs(expected, True)

            >>> regexs          # byexample: -tags
            ('\\A', '(?:(?P<foo>.+?)(?<!\\n))?', '\\n*\\Z')

            >>> match(regexs, '123\n\n\n\n').groups()
            ('123',)

            >>> expected = '\n<foo>'
            >>> regexs, _, _, _ = _as_regexs(expected, True)

            >>> regexs          # byexample: -tags
            ('\\A', '\\\n', '(?:(?P<foo>.+?)(?<!\\n))?', '\\n*\\Z')

            >>> match(regexs, '\n123\n\n\n\n').groups()
            ('123',)

            >>> match(regexs, '\n\n\n\n\n').groups()
            (None,)
        '''
        expected = self.trailing_newlines_regex().sub('', expected)
        return SM.parse(self, expected, tags_enabled)
