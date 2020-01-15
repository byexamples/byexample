import re
from .common import constant

INIT, WS, LIT, TAG, END, TWOTAGS, EXHAUSTED, ERROR = range(8)
tWS = ('wspaces', 'newlines')
tLIT = ('wspaces', 'newlines', 'literals')
'''
>>> from byexample.parser_sm import SM, SM_NormWS, SM_NotNormWS
>>> from byexample.parser import ExampleParser
>>> import re
>>> from functools import partial

>>> parser = ExampleParser(0, 'utf8', None); parser.language = 'python'

>>> cap_regexs = parser.capture_tag_regexs()
>>> inp_regexs = parser.input_regexs()

>>> ellipsis_marker = parser.ellipsis_marker()

>>> input_prefix_len_range = (6, 12)

>>> sm = SM(cap_regexs, inp_regexs, ellipsis_marker, input_prefix_len_range)
>>> sm_norm_ws = SM_NormWS(cap_regexs, inp_regexs, ellipsis_marker, input_prefix_len_range)
>>> sm_lit = SM_NotNormWS(cap_regexs, inp_regexs, ellipsis_marker, input_prefix_len_range)

>>> def match(regexs, string):
...     r = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
...     return r.match(string)
'''


class SM(object):
    def __init__(
        self, capture_tag_regexs, input_regexs, ellipsis_marker,
        input_prefix_len_range
    ):
        self.capture_tag_regex = capture_tag_regexs.for_capture
        self.capture_tag_split_regex = capture_tag_regexs.for_split
        self.ellipsis_marker = ellipsis_marker

        self.input_capture_regex = input_regexs.for_capture
        self.input_check_regex = input_regexs.for_check

        self.input_prefix_min_len, self.input_prefix_max_len = input_prefix_len_range
        assert self.input_prefix_min_len <= self.input_prefix_max_len

        self.reset()

    def reset(self):
        self.stash = []
        self.results = []
        self.state = INIT

        self.tags_by_idx = {}
        self.names_seen = set()

        self.last_literals_seen = []
        self.input_list = []
        self.in_sync = True
        self.reset_prefix_at_charno = 0x7fffffffff

        self.emit(0, r'\A', 0, False)

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

    def pop(self):
        return self.stash.pop()

    def peek(self):
        return self.stash[0][1] if self.stash else None

    def drop(self, last=False):
        self.stash.pop(-1 if last else 0)

    def reset_prefix(self, sync_lost):
        self.in_sync = sync_lost == False
        self.last_literals_seen.clear()

    def get_last_literals_seen(self):
        if not self.last_literals_seen:
            return (None, '', 0)

        rc = 0
        ix = 0
        for charno, regex, rcount in reversed(self.last_literals_seen):
            rc += rcount
            ix += 1

            if rc >= self.input_prefix_max_len:
                break

        charno = self.last_literals_seen[-ix][0]
        rx = ''.join(regex for _, regex, _ in self.last_literals_seen[-ix:])

        return charno, rx, rc

    def emit(self, charno, regex, rcount, add_as_prefix):
        if charno >= self.reset_prefix_at_charno:
            self.reset_prefix(sync_lost=False)
            self.reset_prefix_at_charno = 0x7fffffffff

        # track of the last literals seen
        if add_as_prefix:
            self.last_literals_seen.append((charno, regex, rcount))

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

        return self.emit(charno, rx, rc, True)

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
            >>> sm.emit_tag(ctx='0', endline=False)         # byexample: +rm=~
            Traceback<...>
            ValueError: The same capture tag cannot be used twice
            and 'sax' is repeated at the 6th character.
            ~
            May be you wanted to paste them and you forgot
            '+paste' or their were not captured in a previous
            example. Or perhaps you do not want capture/paste
            anything: you want to treat the tags as literals
            and you forgot '-tags'.

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
            msg = "The same capture tag cannot be used twice\n"+\
                  "and '%s' is repeated at the %ith character.\n\n"+\
                  "May be you wanted to paste them and you forgot\n"+\
                  "'+paste' or their were not captured in a previous\n"+\
                  "example. Or perhaps you do not want capture/paste\n"+\
                  "anything: you want to treat the tags as literals\n"+\
                  "and you forgot '-tags'."

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

        greedy = r'?'  # not greedy
        if not name and endline:
            greedy = r''  # yes, greedy

        rx = rx.format(
            capture=r'?P<%s>' % name.replace('-', '_') if name else r'?:',
            greedy=greedy
        )
        rc = 0
        self.reset_prefix(sync_lost=True)
        return self.emit(charno, rx, rc, False)

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
        return self.emit(charno, rx, rc, False)

    def emit_input(self):
        '''
            An 'input' is a piece of text in the expected string that
            it will be *typed in* by byexample into the current-in-execution
            example.

            When an input is emitted, it must not only emit the text
            to be typed but also the text that should appear
            *before* the typing.

            This text, that we call 'prefix', is a hint that byexample
            will use to know *when* a text must by typed.

            As long as byexample *knows* when to type one or more
            inputs, the need of the prefix is irrelevant.

            In this case we say that we are *in sync*.

            This is the initial state:

            >>> sm.reset()
            >>> sm.push(0, '42')
            >>> sm.emit_input()     # "in sync": prefix empty is allowed
            ('', '42')

            >>> sm.push(0, 'num:')
            >>> sm.emit_literals()  # byexample: +pass
            >>> sm.push(0, '31')
            >>> sm.emit_input()     # still "in sync": short prefix allowd too
            ('num\\:', '31')

            The internal state machine will lose the synchronization
            after a capture tag because byexample will not know
            for sure when to type after an arbitrary amount of text.

            In these cases a minimum amount of prefix is required:

            >>> sm.push(0, '<...>')
            >>> sm.emit_tag('0', False)  # byexample: +pass

            >>> sm.input_prefix_min_len
            6

            >>> sm.push(0, 'user')  # this is a 4-bytes prefix: too short!
            >>> sm.emit_literals()  # byexample: +pass
            >>> sm.push(4, 'john')
            >>> sm.emit_input()
            Traceback<...>
            ValueError: There are too few characters before the input tag at character 4th to proceed

            >>> sm.push(0, 'name:')
            >>> sm.emit_literals()  # byexample: +pass
            >>> sm.push(0, 'john')
            >>> sm.emit_input()
            ('username\\:', 'john')

            Note how the consecutive literals are concatenated to form
            a larger prefix.

            Once that an input is emitted successfully, the internal
            state machine is in sync again:

            >>> sm.push(0, 'last:')
            >>> sm.emit_literals()  # byexample: +pass
            >>> sm.push(0, 'doe')
            >>> sm.emit_input()     # prefix is too short but we are in sync already
            ('last\\:', 'doe')

            The capture tags *do* work as barriers: not only make us to
            loose the synchronization but also prevent
            the concatenation of further "in the past" literals:

            >>> sm.push(0, 'your-')     # before the tag, this will not be used
            >>> sm.emit_literals()                      # byexample: +pass
            >>> sm.push(4, '<...>')
            >>> sm.emit_tag('0', False)                 # byexample: +pass
            >>> sm.push(9, 'email:')
            >>> sm.emit_literals()                      # byexample: +pass
            >>> sm.push(15, 'jdoe@example.com')
            >>> sm.emit_input()
            ('email\\:', 'jdoe@example.com')

            Too long prefixes are not wanted either because larger prefixes
            increases the probability of having a mismatch between them and
            the real output (due a typo in the expected or a bug in the example)
            and it will make byexample to fail.

            Truncating too long prefixes reduces the probability:

            >>> sm.input_prefix_max_len
            12

            >>> sm.push(1, 'What is ')
            >>> sm.emit_literals()     # byexample: +pass
            >>> sm.push(8, 'your real')
            >>> sm.emit_literals()     # byexample: +pass
            >>> sm.push(17, ' name?')
            >>> sm.emit_literals()     # byexample: +pass
            >>> sm.push(22, 'john doe')
            >>> sm.emit_input()
            ('your\\ real\\ name\\?', 'john doe')

            All the inputs emitted are collected in the input_list that you
            can query any time:

            >>> sm.input_list                   # byexample: +norm-ws
            [('', '42'),
             ('num\\:', '31'),
             ('username\\:', 'john'),
             ('last\\:', 'doe'),
             ('email\\:', 'jdoe@example.com'),
             ('your\\ real\\ name\\?', 'john doe')]
            '''

        charno, input = self.pop()
        _, prefix_regex, prefix_rcount = self.get_last_literals_seen()

        if prefix_rcount < self.input_prefix_min_len and not self.in_sync:
            raise ValueError(
                "There are too few characters before the input tag at character %ith to proceed"
                % charno
            )

        res = (prefix_regex, input)
        self.input_list.append(res)
        self.reset_prefix(sync_lost=False)
        return res

    def expected_tokenizer(self, expected_str, tags_enabled, input_enabled):
        ''' Iterate over the interesting tokens of the expected string:
             - newlines   - wspaces   - literals   - tag   - input   - warn

            >>> _tokenizer = partial(sm.expected_tokenizer, tags_enabled=True, input_enabled=True)

            >>> list(_tokenizer(''))
            [(0, 'end', None)]

            Return an iterable of tuples: (<charno>, <token type>, <token val>)
            >>> list(_tokenizer(' '))
            [(0, 'wspaces', ' '), (1, 'end', None)]

            Multiple chars are considered a single 'literals' token
            >>> list(_tokenizer('abc'))
            [(0, 'literals', 'abc'), (3, 'end', None)]

            Each tuple contains the <charno>: the position in the string
            where the token was found
            >>> list(_tokenizer('abc def'))       # byexample: +norm-ws
            [(0, 'literals', 'abc'), (3, 'wspaces', ' '),
             (4, 'literals', 'def'), (7, 'end', None)]

            Multiple spaces are considered a single 'wspaces' token.
            >>> list(_tokenizer(' abc  def\t'))          # byexample: +norm-ws
            [(0, 'wspaces', ' '),  (1, 'literals', 'abc'),
             (4, 'wspaces', '  '), (6, 'literals', 'def'), (9, 'wspaces', '\t'),
             (10, 'end', None)]

            Each tuple contains the string that constitutes the token.
            >>> list(_tokenizer('<foo><bar> \n\n<...> <...>def <...>'))  # byexample: +norm-ws -tags
            [(0,  'tag', '<foo>'),      (5,  'tag', '<bar>'), (10, 'wspaces', ' '),
             (11, 'newlines', '\n\n'),  (13, 'tag', '<...>'),
             (18, 'wspaces', ' '),      (19, 'tag', '<...>'), (24, 'literals', 'def'),
             (27, 'wspaces', ' '),      (28, 'tag', '<...>'), (33, 'end', None)]

            This also includes the inputs. They are similar in structure
            to a tag however they only can appear at the end of the line
            (trailing spaces are ok) and their values are the text input
            without the markers (by default [ and ]):
            >>> list(_tokenizer('user: [john doe]\npass: [123] \nrole:[admin] '))  # byexample: +norm-ws -tags
            [(0, 'literals', 'user:'),  (5, 'wspaces', ' '),
             (6, 'input', 'john doe'),
             (6, 'literals', '[john'),  (11, 'wspaces', ' '),
             (12, 'literals', 'doe]'),
             (16, 'input-end', ''),     (16, 'newlines', '\n'),
             (17, 'literals', 'pass:'), (22, 'wspaces', ' '),
             (23, 'input', '123'),
             (23, 'literals', '[123]'), (28, 'wspaces', ' '),
             (29, 'input-end', ''),     (29, 'newlines', '\n'),
             (30, 'literals', 'role:'), (35, 'input', 'admin'),
             (35, 'literals', '[admin]'),
             (42, 'wspaces', ' '),
             (43, 'input-end', ''),     (43, 'end', None)]

            Note how the inputs [..] appears twice: first as the 'input'
            token and then as one or more literals and whitespaces.

            And also note that after the literals product of the inputs
            appear an 'input-end' that have a null token. Those are to
            mark the end of the literals product of the inputs before
            the newline but after of the optional trailing whitespace.

            The literals+whitespaces follow the same rules
            of tokenization as any other literals/whitespaces, however
            the 'input' tokens are yielded as one single item (like 'john doe')
            despite having a whitespace in the middle.

            The literals from inputs are not merged with the previous or the
            following literals. In the example above the string 'role:[admin]'
            produced two consecutive literals 'role:' and '[admin]' not one.
            (The input token introduces a *break* in the middle)

            If <tags_enabled> is False, the tags are considered literals
            >>> list(_tokenizer('<foo><bar> \n\n<...> <...>def <...>', tags_enabled=False))  # byexample: +norm-ws -tags
            [(0,  'literals', '<foo><bar>'), (10, 'wspaces', ' '),
             (11, 'newlines', '\n\n'),       (13, 'literals', '<...>'),
             (18, 'wspaces', ' '),           (19, 'literals', '<...>def'),
             (27, 'wspaces', ' '),           (28, 'literals', '<...>'), (33, 'end', None)]

            If <input_enabled> is False, the input tags are considered literals
            >>> list(_tokenizer('[foo][bar] \n\n[...] [...]def [...]', input_enabled=False))  # byexample: +norm-ws -tags
            [(0,  'literals', '[foo][bar]'), (10, 'wspaces', ' '),
             (11, 'newlines', '\n\n'),       (13, 'literals', '[...]'),
             (18, 'wspaces', ' '),           (19, 'literals', '[...]def'),
             (27, 'wspaces', ' '),           (28, 'literals', '[...]'), (33, 'end', None)]

            The tokenizer can detect some weird conditions and
            yield warnings as special tokens and proceeding with the parsing
            as usual.

            For example, more than one input is not allowed as well inputs
            that are not at the end of the line. This may be ok or it
            may indicate an error of the user (she may not understand
            how the inputs work thinking that it can be anywhere or
            it just typed something after an input by accident).
            Also, a tag inside an input makes no sense: you cannot capture
            what you are typing. This may be a typo or a failure in the paste
            mode.
            >>> list(_tokenizer('user: [john doe]ups\npass: [123][a<d>min] '))  # byexample: +norm-ws -tags
            [(6, 'warn', 'input-not-at-the-end'),
             (0, 'literals', 'user:'),  (5, 'wspaces', ' '),
             (6, 'literals', '[john'),  (11, 'wspaces', ' '), (12, 'literals', 'doe]ups'),
             (19, 'newlines', '\n'),
             (31, 'warn', 'tag-inside-input'),
             (26, 'warn', 'input-not-at-the-end'),
             (20, 'literals', 'pass:'), (25, 'wspaces', ' '), (26, 'literals', '[123]'),
             (31, 'input', 'a<d>min'),
             (31, 'literals', '[a'),    (33, 'tag', '<d>'),   (36, 'literals', 'min]'),
             (40, 'wspaces', ' '),
             (41, 'input-end', ''),     (41, 'end', None)]

            This last example has several interesting things:
                - the warnings are "out of order": their charno will not
                  follow a monotonic increasing sequence.
                - in the case of 'input-not-at-the-end', literals are *not*
                  removed from the token list and they are returned
                  as literals (like `[john`) but no 'input' token is generated.
                - tags inside inputs like `[a<d>min]` are warnings too
                  with an *approximate* charno; the input and literals
                  are generated including the tag.
        '''

        nl_splitter = self.one_or_more_nl_capture_regex()
        ws_splitter = self.one_or_more_ws_capture_regex()
        tag_splitter = self.capture_tag_split_regex
        input_capture_regex = self.input_capture_regex
        input_check_regex = self.input_check_regex

        # TODO return lineno also to debug easily

        charno = 0
        charno_of_input = -1
        input_match = None
        for k, line_or_newlines in enumerate(nl_splitter.split(expected_str)):
            if k % 2 == 1:
                newlines = line_or_newlines
                if input_match:
                    yield (charno, 'input-end', '')
                    input_match = None

                yield (charno, 'newlines', newlines)
                charno += len(newlines)
                continue

            line = line_or_newlines

            # is the last part of the line an input?
            input_match = input_capture_regex.search(
                line
            ) if input_enabled else None
            if input_match:
                charno_of_input = charno + input_match.start()

                m = tag_splitter.search(input_match.group(1))
                if m:
                    yield (charno_of_input, 'warn', 'tag-inside-input')

            # do we have any piece of the line that looks like an input?
            # using the 'check' regex we should match any [..], not only
            # at the end
            if input_enabled:
                tmp = line[:input_match.start()] if input_match else line
                m = input_check_regex.search(tmp)
                if m:
                    yield (charno + m.start(), 'warn', 'input-not-at-the-end')

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
                        # if the literals contain an input [..], split
                        # the literals in two
                        if charno <= charno_of_input < charno + len(literals):
                            brk = charno_of_input - charno
                            input, _ = input_match.groups()

                            if brk > 0:
                                # yield if not empty (this can happen if
                                # the input starts at the begin of this literals
                                yield (charno, 'literals', literals[:brk])

                            yield (charno + brk, 'input', input)
                            yield (charno + brk, 'literals', literals[brk:])
                        else:
                            yield (charno, 'literals', literals)

                        charno += len(literals)

        if input_match:
            yield (charno, 'input-end', '')
            input_match = None
        yield (charno, 'end', None)

    def parse(self, expected, tags_enabled, input_enabled):
        self.reset()
        tokenizer = self.expected_tokenizer(
            expected, tags_enabled, input_enabled
        )

        while not self.ended():
            charno, ttype, token = next(tokenizer, (None, None, None))
            self.feed(charno, ttype, token)

            assert (ttype == None and self.ended()) or \
                    (ttype != None and not self.ended())

        charnos, regexs, rcounts = zip(*self.results)
        return regexs, charnos, rcounts, self.tags_by_idx, self.input_list


class SM_NormWS(SM):
    def __init__(
        self, capture_tag_regexs, input_regexs, ellipsis_marker,
        input_prefix_len_range
    ):
        SM.__init__(
            self, capture_tag_regexs, input_regexs, ellipsis_marker,
            input_prefix_len_range
        )

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

        return self.emit(charno, rx, rc, True)

    def emit_tag(self, ctx, endline):
        assert ctx in ('l', 'r', 'b', '0')
        return SM.emit_tag(self, ctx, endline)

    def emit_eof(self, ws):
        assert ws == 's'
        return SM.emit_eof(self, ws)

    def feed(self, charno, ttype, token):
        push = self.push
        drop = self.drop

        if ttype == 'input-end':
            self.reset_prefix_at_charno = charno
            return

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
            elif ttype == 'input':
                self.emit_input()
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
                charno, _ = self.pull(
                )  # get the position of the wspaces/newlines
                _, token = self.pull()  # get the end token
                push(charno, token)
                self.state = END  # ignore the first wspaces/newlines token
            elif ttype == 'input':
                self.emit_input()
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
            elif ttype == 'input':
                self.emit_input()
            else:
                assert False

        elif self.state == TAG:
            assert stash_size == 2
            if ttype in tWS:
                self.emit_tag(ctx='r', endline=(ttype == 'newlines'))
                self.state = WS
            elif ttype == 'literals':
                self.emit_tag(ctx='0', endline=False)
                self.state = LIT
            elif ttype == 'tag':
                self.state = TWOTAGS
            elif ttype == 'end':
                self.emit_tag(ctx='r', endline=True)
                self.state = END
            elif ttype == 'input':
                self.emit_input()
            else:
                assert False

        elif self.state == END:
            assert stash_size == 2
            assert ttype is None  # next token doesn't exist: tokenizer exhausted
            drop(last=True)
            self.emit_eof(ws='s')
            self.state = EXHAUSTED
        elif self.state == (WS, TAG):
            assert stash_size == 3
            if ttype in tWS:
                self.emit_ws(just_one=True)
                self.emit_tag(ctx='b', endline=(ttype == 'newlines'))
                self.state = WS
            elif ttype == 'literals':
                self.emit_ws()
                self.emit_tag(ctx='l', endline=False)
                self.state = LIT
            elif ttype == 'tag':
                drop()  # drop the WS, we will not use it
                self.state = TWOTAGS
            elif ttype == 'end':
                self.emit_ws(just_one=True)
                self.emit_tag(ctx='b', endline=True)
                self.state = END
            elif ttype == 'input':
                self.emit_input()
            else:
                assert False

        elif self.state == TWOTAGS:
            assert stash_size == 3
            self.state = ERROR
            drop(last=True)  # don't care what we read next
            drop(last=True)  # don't care the second tag
            charno, _ = self.pull()
            msg = "Two consecutive capture tags were found at %ith character. " +\
                  "This is ambiguous."
            raise ValueError(msg % charno)
        elif self.state in (EXHAUSTED, ERROR):
            assert False
        else:
            assert False

    def parse(self, expected, tags_enabled, input_enabled):
        '''
            >>> _as_regexs = partial(sm_norm_ws.parse, tags_enabled=True, input_enabled=True)

            Parse a given <expected> string and return a list
            of regular expressions that joined matches the original
            string.

            The regexs will ignore the amount of whitespaces in the
            <expected> yielding a '\s+' regex for them (one or more
            whitespaces of any kind).

            >>> r, p, c, _, _ = _as_regexs('a  \n   b  \t\vc')

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
            >>> regexs, p, _, _, _ = _as_regexs(expected)

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
            >>> regexs, p, _, _, _ = _as_regexs(expected)

            >>> regexs               # byexample: -tags
            ('\\A', 'a', '\\s+(?!\\s)', '(?P<foo>.*?)', 'b', '\\s*\\Z')

            >>> p
            (0, 0, 1, 2, 7, 8)

            >>> match(regexs, 'a  \n 123\n\n b').groups()
            ('123\n\n ',)

            >>> expected = 'a<foo> b'
            >>> regexs, p, _, _, _ = _as_regexs(expected)

            >>> regexs               # byexample: -tags
            ('\\A', 'a', '(?P<foo>.*?)(?<!\\s)', '\\s+(?!\\s)', 'b', '\\s*\\Z')

            >>> p
            (0, 0, 1, 6, 7, 8)

            >>> match(regexs, 'a  \n 123\n\n b').groups()
            ('  \n 123',)

            The most complex scenario happens when the tag has whitespaces
            on its left *and* its right.

            >>> expected = 'a\n<foo>\tb'
            >>> regexs, p, _, _, _ = _as_regexs(expected)

            >>> regexs           # byexample: +norm-ws -tags
            ('\\A', 'a', '\\s', '(?:\\s*(?!\\s)(?P<foo>.+?)(?<!\\s))?', '\\s+(?!\\s)', 'b', '\\s*\\Z')

            >>> p
            (0, 0, 1, 2, 7, 8, 9)

            >>> match(regexs, 'a  \n 123\n\n b').groups()
            ('123',)

            >>> match(regexs, 'a  \n \n\n b').groups('')
            ('',)

            Notice how the <expected> requests at least one whitespace on the
            left of the tag *and* at least one whitespace on its right.

            The following with two whitespaces works:
            >>> match(regexs, 'a  b').groups('')
            ('',)

            But this one will not:
            >>> match(regexs, 'a b') is None
            True

            The parse method adds an extra regex at the end to remove any
            trailing whitespace. This must also needs to be taken into
            consideration.

            >>> expected = '<foo>  \n\n'
            >>> regexs, p, _, _, _ = _as_regexs(expected)

            >>> regexs               # byexample: -tags
            ('\\A', '(?P<foo>.*?)(?<!\\s)', '\\s*\\Z')

            >>> p
            (0, 0, 5)

            >>> match(regexs, '   123  \n\n\n\n').groups()
            ('   123',)

            >>> expected = ' <foo>  \n\n'
            >>> regexs, p, _, _, _ = _as_regexs(expected)

            >>> regexs               # byexample: -tags
            ('\\A', '\\s', '(?:\\s*(?!\\s)(?P<foo>.+?)(?<!\\s))?', '\\s*\\Z')

            >>> p
            (0, 0, 1, 6)

            >>> match(regexs, '   123  \n\n\n\n').groups()
            ('123',)

            >>> expected = ' <foo>'
            >>> regexs, p, _, _, _ = _as_regexs(expected)

            >>> regexs               # byexample: -tags
            ('\\A', '\\s', '(?:\\s*(?!\\s)(?P<foo>.+?)(?<!\\s))?', '\\s*\\Z')

            >>> p
            (0, 0, 1, 6)

            >>> match(regexs, '   123  \n\n\n\n').groups()
            ('123',)

            >>> expected = '<foo>'
            >>> regexs, p, _, _, _ = _as_regexs(expected)

            >>> regexs               # byexample: -tags
            ('\\A', '(?P<foo>.*?)(?<!\\s)', '\\s*\\Z')

            >>> p
            (0, 0, 5)

            >>> match(regexs, '   123  \n\n\n\n').groups()
            ('   123',)

            >>> expected = ' '
            >>> regexs, p, _, _, _ = _as_regexs(expected)

            >>> regexs               # byexample: -tags
            ('\\A', '\\s*\\Z')

            >>> p
            (0, 0)

            >>> expected = ''
            >>> regexs, p, _, _, _ = _as_regexs(expected)

            >>> regexs               # byexample: -tags
            ('\\A', '\\s*\\Z')

            >>> p
            (0, 0)

            Last, when the inputs are enabled the function returns the list
            of them. The regexs are not affected as the inputs are also treated
            as literals to be matched. See more about this in the documentation
            of SM_NotNormWS.parse method.

            >>> expected = 'username: [john]\npass: [admin]  \ncomment: [ none ]'
            >>> regexs, charnos, rcounts, _, input_list = _as_regexs(expected)

            >>> regexs              # byexample: +norm-ws
            ('\\A', 'username\\:', '\\s+(?!\\s)', '\\[john\\]', '\\s+(?!\\s)',
             'pass\\:', '\\s+(?!\\s)', '\\[admin\\]', '\\s+(?!\\s)',
             'comment\\:', '\\s+(?!\\s)', '\\[', '\\s+(?!\\s)', 'none', '\\s+(?!\\s)', '\\]',
             '\\s*\\Z')

            >>> charnos
            (0, 0, 9, 10, 16, 17, 22, 23, 30, 33, 41, 42, 43, 44, 48, 49, 50)

            >>> rcounts
            (0, 9, 1, 6, 1, 5, 1, 7, 1, 8, 1, 1, 1, 4, 1, 1, 0)

            >>> input_list
            [('username\\:', 'john'),
             ('\\s+(?!\\s)pass\\:', 'admin'),
             ('comment\\:', ' none ')]

            There is a small difference with respect SM_NotNormWS.parse:
            in our case (SM_NormWS.parse) the prefixes may begin with
            a whitespace regex or not but in the case of SM_NotNormWS.parse,
            the prefixes always begin with a newline regex (except the first).
        '''
        return SM.parse(self, expected, tags_enabled, input_enabled)


class SM_NotNormWS(SM):
    def __init__(
        self, capture_tag_regexs, input_regexs, ellipsis_marker,
        input_prefix_len_range
    ):
        SM.__init__(
            self, capture_tag_regexs, input_regexs, ellipsis_marker,
            input_prefix_len_range
        )

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

        if ttype == 'input-end':
            self.reset_prefix_at_charno = charno
            return

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
            elif ttype == 'input':
                self.emit_input()
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
            elif ttype == 'input':
                self.emit_input()
            else:
                assert False

        elif self.state == TAG:
            assert stash_size == 2
            if ttype in tLIT:
                self.emit_tag(ctx='0', endline=(ttype == 'newlines'))
                self.state = LIT
            elif ttype == 'tag':
                self.state = TWOTAGS
            elif ttype == 'end':
                self.emit_tag(ctx='n', endline=True)
                self.state = END
            elif ttype == 'input':
                self.emit_input()
            else:
                assert False

        elif self.state == END:
            assert stash_size == 2
            assert ttype is None  # next token doesn't exist: tokenizer exhausted
            drop(last=True)
            self.emit_eof(ws='n')
            self.state = EXHAUSTED
        elif self.state == TWOTAGS:
            assert stash_size == 3
            self.state = ERROR
            drop(last=True)  # don't care what we read next
            drop(last=True)  # don't care the second tag
            charno, _ = self.pull()
            msg = "Two consecutive capture tags were found at %ith character. " +\
                  "This is ambiguous."
            raise ValueError(msg % charno)
        elif self.state in (EXHAUSTED, ERROR):
            assert False
        else:
            assert False

    def parse(self, expected, tags_enabled, input_enabled):
        '''
            >>> _as_regexs = partial(sm_lit.parse, tags_enabled=True, input_enabled=True)

            Parse a given <expected> string and return a list
            of regular expressions that joined matches the original
            string.

            >>> expected = 'a<foo>b<b-b>c<...>d'
            >>> regexs, charnos, rcounts, tags_by_idx, input_list = _as_regexs(expected)

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
            >>> regexs, _, rcounts, _, _ = _as_regexs(expected)

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
            >>> _as_regexs('a<foo><bar>c')
            Traceback (most recent call last):
            <...>
            ValueError: <...>

            If tags_enabled is False, all the <...> tags are taken literally.

            >>> r, p, _, i, _ = _as_regexs('a<foo>b<bar>c', tags_enabled=False)
            >>> match(r, 'axxbyyyc') is None # don't matched as <foo> is not xx
            True

            >>> match(r, 'a<foo>b<bar>c') is None # the strings <foo> <bar> are literals
            False

            >>> i
            {}

            The tag names cannot be repeated:

            >>> _as_regexs('a<foo>b<foo>c')
            Traceback (most recent call last):
            <...>
            ValueError: <...>

            Any trailing new line will be ignored

            >>> expected = '<foo>\n\n\n'
            >>> regexs, _, _, _, _ = _as_regexs(expected)

            >>> regexs          # byexample: -tags
            ('\\A', '(?:(?P<foo>.+?)(?<!\\n))?', '\\n*\\Z')

            >>> match(regexs, '   123  \n\n\n\n').groups()
            ('   123  ',)

            >>> expected = '<foo>'
            >>> regexs, _, _, _, _ = _as_regexs(expected)

            >>> regexs          # byexample: -tags
            ('\\A', '(?:(?P<foo>.+?)(?<!\\n))?', '\\n*\\Z')

            >>> match(regexs, '123\n\n\n\n').groups()
            ('123',)

            >>> expected = '\n<foo>'
            >>> regexs, _, _, _, _ = _as_regexs(expected)

            >>> regexs          # byexample: -tags
            ('\\A', '\\\n', '(?:(?P<foo>.+?)(?<!\\n))?', '\\n*\\Z')

            >>> match(regexs, '\n123\n\n\n\n').groups()
            ('123',)

            >>> match(regexs, '\n\n\n\n\n').groups()
            (None,)

            Last, when the inputs are enabled the function returns the list
            of them. The regexs are not affected as the inputs are also treated
            as literals to be matched (we expect that the input is *echoed* back
            so we need to match it too).

            >>> expected = 'username: [john]\npass: [admin]  \ncomment: [ none ]'
            >>> regexs, charnos, rcounts, _, input_list = _as_regexs(expected)

            >>> regexs              # byexample: +norm-ws
            ('\\A', 'username\\:', '\\ ', '\\[john\\]', '\\\n',
             'pass\\:', '\\ ', '\\[admin\\]', '\\ \\ ', '\\\n',
             'comment\\:', '\\ ', '\\[', '\\ ', 'none', '\\ ', '\\]',
             '\\n*\\Z')

            >>> charnos
            (0, 0, 9, 10, 16, 17, 22, 23, 30, 32, 33, 41, 42, 43, 44, 48, 49, 50)

            >>> rcounts
            (0, 9, 1, 6, 1, 5, 1, 7, 2, 1, 8, 1, 1, 1, 4, 1, 1, 0)

            >>> input_list
            [('username\\:', 'john'),
             ('\\\npass\\:', 'admin'),
             ('\\\ncomment\\:', ' none ')]

            Note how the prefixes never include the literals that came from
            previous inputs (it is '\npass', not '[john]\npass:')
            This is very important because byexample will use the prefix to
            'expect' in the *unread* output and the inputs are considered
            'already read' output so they will never match.

            There is a small difference with respect SM_NotNormWS.parse:
            in our case (SM_NotNormWS.parse) the prefixes begin always with
            a newline regex (except the first) but in the case of
            SM_NormWS.parse, the prefixes may begin with a whitespace
            regex or not.
        '''
        expected = self.trailing_newlines_regex().sub('', expected)
        return SM.parse(self, expected, tags_enabled, input_enabled)
