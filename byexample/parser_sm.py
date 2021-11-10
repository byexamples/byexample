from . import regex as re
from .common import constant, short_string
from .log import clog, log_context, DEBUG
import pprint

INIT, WS, LIT, TAG, END, TWOTAGS, EXHAUSTED, ERROR = range(8)
tWS = ('wspaces', 'newlines')
tLIT = ('wspaces', 'newlines', 'literals')
r'''
>>> from byexample.log import init_log_system
>>> init_log_system()

>>> from byexample.parser_sm import SM, SM_NormWS, SM_NotNormWS
>>> from byexample.parser import ExampleParser
>>> import byexample.regex as re
>>> from functools import partial

>>> parser = ExampleParser(0, 'utf8', None); parser.language = 'python'

>>> tag_regexs = parser.tag_regexs()
>>> inp_regexs = parser.input_regexs()

>>> ellipsis_marker = parser.ellipsis_marker()

>>> input_prefix_len_range = (6, 12)

>>> sm = SM(tag_regexs, inp_regexs, ellipsis_marker, input_prefix_len_range)
>>> sm_norm_ws = SM_NormWS(tag_regexs, inp_regexs, ellipsis_marker, input_prefix_len_range)
>>> sm_lit = SM_NotNormWS(tag_regexs, inp_regexs, ellipsis_marker, input_prefix_len_range)

>>> def match(regexs, string):
...     r = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
...     return r.match(string)
'''


class SM(object):
    def __init__(
        self, tag_regexs, input_regexs, ellipsis_marker, input_prefix_len_range
    ):
        self.tag_regex = tag_regexs.for_capture
        self.tag_split_regex = tag_regexs.for_split
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
        self.input_events = []

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

    def record_input_event(self, charno, ttype, *args):
        self.input_events.append((charno, ttype, args))

    def emit(self, charno, regex, rcount):
        item = (charno, regex, rcount)
        self.results.append(item)
        clog().debug("emit: %06i (rc %06i): %s" % (charno, rcount, regex))
        return item

    def emit_literals(self):
        r'''
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

        self.record_input_event(charno, 'prefix', l, rx, rc)
        return self.emit(charno, rx, rc)

    def name_of_tag_or_None(self, tag):
        name = self.tag_regex.match(tag).group('name')
        if name == self.ellipsis_marker:
            name = None

        return name

    def emit_tag(self, ctx, endline):
        r'''
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
            and you forgot '-tags' or '-capture'.

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
                  "and you forgot '-tags' or '-capture'."

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
        self.record_input_event(charno, 'reset')
        self.record_input_event(charno, 'sync_lost')
        return self.emit(charno, rx, rc)

    def emit_eof(self, ws):
        r'''
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

    def expected_tokenizer(self, expected_str, tags_enabled, input_enabled):
        r''' Iterate over the interesting tokens of the expected string:
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
            [(6, 'warn', ('input-not-at-the-end', '[john doe]')),
             (0, 'literals', 'user:'),  (5, 'wspaces', ' '),
             (6, 'literals', '[john'),  (11, 'wspaces', ' '), (12, 'literals', 'doe]ups'),
             (19, 'newlines', '\n'),
             (31, 'warn', ('tag-inside-input', '<d>')),
             (26, 'warn', ('input-not-at-the-end', '[123]')),
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
        tag_splitter = self.tag_split_regex
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
                    yield (
                        charno_of_input, 'warn',
                        ('tag-inside-input', m.group(0))
                    )

            # do we have any piece of the line that looks like an input?
            # using the 'check' regex we should match any [..], not only
            # at the end
            if input_enabled:
                tmp = line[:input_match.start()] if input_match else line
                m = input_check_regex.search(tmp)
                if m:
                    yield (
                        charno + m.start(), 'warn',
                        ('input-not-at-the-end', m.group(0))
                    )

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

    @log_context('byexample.parser')
    def parse(self, expected, tags_enabled, input_enabled):
        self.reset()
        self.emit(0, r'\A', 0)

        tokenizer = self.expected_tokenizer(
            expected, tags_enabled, input_enabled
        )

        if clog().isEnabledFor(DEBUG):
            clog().chat(
                "Parsing: tags enabled? %s; input enabled? %s", tags_enabled,
                input_enabled
            )

        while not self.ended():
            charno, ttype, token = next(tokenizer, (None, None, None))
            if charno is not None:
                clog().debug("tokn: %06i [% 9s]: %s" % (charno, ttype, token))

            if ttype == 'input':
                self.record_input_event(charno, 'input', token)
            elif ttype == 'input-end':
                self.record_input_event(charno, 'reset')
            elif ttype == 'warn':
                self.warn(charno, ttype, token)
            else:
                self.feed(charno, ttype, token)

            assert (ttype == None and self.ended()) or \
                    (ttype != None and not self.ended())

        charnos, regexs, rcounts = zip(*self.results)
        input_list = self.build_input_list()
        return regexs, charnos, rcounts, self.tags_by_idx, input_list

    def warn(self, charno, ttype, token):
        what, args = token
        if what == 'tag-inside-input':
            tagname = args
            clog().warn(
                "The tag %s was found inside of an input tag around the character %s.\n" + \
                "Perhaps you tried to paste something\n" + \
                "but you forgot '+paste' or the tag has a typo.\n" + \
                "You could also disable this warning disabling the tags with '-tags'.",
                short_string(tagname), charno)

        elif what == 'input-not-at-the-end':
            input = args
            clog().warn(
                "The input tag %s around the character %s is not at the end of a line.\n" + \
                "The input will not be typed.\n" + \
                "If you do not want to type anything, disable it with '-input'\n" + \
                "otherwise the tag must be at the end of the line.",
                short_string(input), charno)
        else:
            assert False

    def build_input_list(self):
        r'''
            Build a list of (<prefix>, <prefix regex>, <input>) tuples.

            The <input> part is a piece of text in the expected string that
            it will be *typed in* by byexample into the current-in-execution
            example.

            Because byexample needs to know *when* the text must be typed,
            the <prefix regex> part is a regex that byexample should match
            with the output from the example *before* the typing.

            <prefix> is the literal text from where the regex was built.

            When the input is set at the begin of the example the "prefix"
            can be arbitrary small:

            >>> parse = partial(sm_lit.parse, tags_enabled=True, input_enabled=True)

            >>> parse('[42]')[-1]
            [('', '', '42')]

            >>> parse('num [42]')[-1]
            [('num ', 'num\\ ', '42')]

            Internally we say the the state machine is *in sync* with
            the output.

            The internal state machine will lose the synchronization
            after a capture tag because byexample will not know
            for sure when to type after an arbitrary amount of text.

            In these cases a minimum amount of prefix is required:

            >>> parse('your name <...>[john]')[-1]
            Traceback<...>
            ValueError: There are too few characters (0) before the input tag at character 15th to proceed

            >>> parse('your nam<...>e [john]')[-1]
            Traceback<...>
            ValueError: There are too few characters (2) before the input tag at character 15th to proceed

            >>> parse('your<...> name [john]')[-1]
            [(' name ', '\\ name\\ ', 'john')]

            >>> sm.input_prefix_min_len
            6

            Once that an input is emitted successfully, the internal
            state machine is in sync again:

            >>> parse('your<...> name [john]\nn [42]')[-1]
            [(' name ', '\\ name\\ ', 'john'), ('n ', 'n\\ ', '42')]

            Note how the prefix of the second input does not include
            anything before the first input.

            Here is another example where there are several lines
            in the prefix:

            >>> parse('name [john]\nnice to meet you\npass [admin]')[-1]
            [('name ', 'name\\ ', 'john'),
             ('meet you\npass ', 'meet\\ you\\\npass\\ ', 'admin')]

            Note how the prefix of the second input is not arbitrary large.

            Too long prefixes are not wanted because larger prefixes
            increases the probability of having a mismatch between them and
            the real output (due a typo in the expected or a bug in the example)
            and it will make byexample to fail.

            Truncating too long prefixes reduces the probability:

            >>> sm.input_prefix_max_len
            12

            '''
        input_list = []
        partial_prefixes = []
        sync_lost = False

        for charno, ttype, args in sorted(self.input_events):
            if ttype == 'prefix':
                literals, regex, rcount = args
                partial_prefixes.append((charno, literals, regex, rcount))

            elif ttype == 'reset':
                assert len(args) == 0
                partial_prefixes.clear()

            elif ttype == 'sync_lost':
                assert len(args) == 0
                assert len(partial_prefixes) == 0
                sync_lost = True

            elif ttype == 'input':
                text, = args
                _, prefix, prefix_regex, prefix_rcount = self.build_prefix(
                    partial_prefixes
                )

                if prefix_rcount < self.input_prefix_min_len and sync_lost:
                    raise ValueError(
                        "There are too few characters (%i) before the input tag at character %ith to proceed"
                        % (prefix_rcount, charno)
                    )

                res = (prefix, prefix_regex, text)
                input_list.append(res)
                sync_lost = False
            else:
                assert False

        return input_list

    def build_prefix(self, partial_prefixes):
        if not partial_prefixes:
            return (None, '', '', 0)

        rc = 0
        ix = 0
        for _, _, _, rcount in reversed(partial_prefixes):
            rc += rcount
            ix += 1

            if rc >= self.input_prefix_max_len:
                break

        charno = partial_prefixes[-ix][0]
        rx = ''.join(regex for _, _, regex, _ in partial_prefixes[-ix:])
        literals = ''.join(lit for _, lit, _, _ in partial_prefixes[-ix:])

        return charno, literals, rx, rc


class SM_NormWS(SM):
    def __init__(
        self, tag_regexs, input_regexs, ellipsis_marker, input_prefix_len_range
    ):
        SM.__init__(
            self, tag_regexs, input_regexs, ellipsis_marker,
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

        self.record_input_event(charno, 'prefix', ' ', rx, rc)
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
                charno, _ = self.pull(
                )  # get the position of the wspaces/newlines
                _, token = self.pull()  # get the end token
                push(charno, token)
                self.state = END  # ignore the first wspaces/newlines token
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
        r'''
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

            >>> expected = 'username [john]\npass [admin]  \ncomment [ none ]'
            >>> regexs, charnos, rcounts, _, input_list = _as_regexs(expected)

            >>> regexs              # byexample: +norm-ws
            ('\\A', 'username', '\\s+(?!\\s)', '\\[john\\]', '\\s+(?!\\s)',
             'pass', '\\s+(?!\\s)', '\\[admin\\]', '\\s+(?!\\s)',
             'comment', '\\s+(?!\\s)', '\\[', '\\s+(?!\\s)', 'none', '\\s+(?!\\s)', '\\]',
             '\\s*\\Z')

            >>> charnos
            (0, 0, 8, 9, 15, 16, 20, 21, 28, 31, 38, 39, 40, 41, 45, 46, 47)

            >>> rcounts
            (0, 8, 1, 6, 1, 4, 1, 7, 1, 7, 1, 1, 1, 4, 1, 1, 0)

            >>> input_list
            [('username ', 'username\\s+(?!\\s)', 'john'),
             ('pass ', 'pass\\s+(?!\\s)', 'admin'),
             ('comment ', 'comment\\s+(?!\\s)', ' none ')]
        '''
        return SM.parse(self, expected, tags_enabled, input_enabled)


class SM_NotNormWS(SM):
    def __init__(
        self, tag_regexs, input_regexs, ellipsis_marker, input_prefix_len_range
    ):
        SM.__init__(
            self, tag_regexs, input_regexs, ellipsis_marker,
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
                self.emit_tag(ctx='0', endline=(ttype == 'newlines'))
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
            msg = "Two consecutive tags were found at %ith character. " +\
                  "This is ambiguous."
            raise ValueError(msg % charno)
        elif self.state in (EXHAUSTED, ERROR):
            assert False
        else:
            assert False

    def parse(self, expected, tags_enabled, input_enabled):
        r'''
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

            >>> expected = 'username [john]\npass [admin]  \ncomment [ none ]'
            >>> regexs, charnos, rcounts, _, input_list = _as_regexs(expected)

            >>> regexs              # byexample: +norm-ws
            ('\\A', 'username', '\\ ', '\\[john\\]', '\\\n',
             'pass', '\\ ', '\\[admin\\]', '\\ \\ ', '\\\n',
             'comment', '\\ ', '\\[', '\\ ', 'none', '\\ ', '\\]',
             '\\n*\\Z')

            >>> charnos
            (0, 0, 8, 9, 15, 16, 20, 21, 28, 30, 31, 38, 39, 40, 41, 45, 46, 47)

            >>> rcounts
            (0, 8, 1, 6, 1, 4, 1, 7, 2, 1, 7, 1, 1, 1, 4, 1, 1, 0)

            >>> input_list
            [('username ', 'username\\ ', 'john'),
             ('pass ', 'pass\\ ', 'admin'),
             ('comment ', 'comment\\ ', ' none ')]

            Note how the prefixes never include the literals that came from
            previous inputs (it is 'pass:', not '[john]\npass:')
            This is very important because byexample will use the prefix to
            'expect' in the *unread* output and the inputs are considered
            'already read' output so they will never match.
        '''
        expected = self.trailing_newlines_regex().sub('', expected)
        return SM.parse(self, expected, tags_enabled, input_enabled)
