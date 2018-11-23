import re

INIT, WS, LIT, TAG, END, TWOTAGS, EXHAUSTED, ERROR = range(8)
tWS = ('wspaces', 'newlines')
tLIT = ('wspaces', 'newlines', 'literals')

class SM_NormWS:
    def __init__(self, parser):
        self.stash = []
        self.results = []
        self.state = INIT
        self.parser = parser
        self.tags_by_idx = {}
        self.names_seen = set()

        self.emit(0, r'\A', 0)

    def ended(self):
        return self.state in (EXHAUSTED, ERROR)

    def pull(self):
        return self.stash.pop(0)

    def drop(self, last=False):
        self.stash.pop(-1 if last else 0)

    def emit(self, charno, regex, rcount):
        self.results.append((charno, regex, rcount))

    def emit_ws(self, just_one=False):
        charno, _ = self.pull()
        if just_one:
            rx = r'\s'
        else:
            rx = r'\s+(?!\s)'
        rc = 1

        self.emit(charno, rx, rc)

    def emit_literals(self):
        charno, l = self.pull()
        rx = re.escape(l)
        rc = len(l)

        self.emit(charno, rx, rc)

    def emit_tag(self, mode):
        assert mode in ('l', 'r', 'b', '0', 'e')
        charno, tag = self.pull()

        name = self.parser.name_of_tag_or_None(tag)
        self.tags_by_idx[len(self.results)] = name

        if name in self.names_seen:
            msg = "The named capture tag '%s' is repeated in " +\
                  "the %ith character."

            raise ValueError(msg % (name, charno))

        if name is not None:
            self.names_seen.add(name)

        if mode in ('l', '0'):
            rx = r'({capture}.*{greedy})'
        elif mode == 'r':
            rx = r'({capture}.*{greedy})(?<!\s)'
        elif mode == 'b':
            rx = r'(?:\s*(?!\s)({capture}.+{greedy})(?<!\s))?'
        elif mode == 'e':
            rx = r'(?:({capture}.+{greedy})(?<!\n))?'
        else:
            assert False

        rx = rx.format(capture=r'?P<%s>' % name.replace('-', '_') if name else r'?:',
                greedy=r'?' if name else '')
        rc = 0
        self.emit(charno, rx, rc)

    def emit_eof(self, ws):
        charno, _ = self.pull()
        rx = r'{ws}*\Z'.format(ws=ws)
        rc = 0
        self.emit(charno, rx, rc)

    def feed(self, charno, ttype, token):
        push = self.stash.append
        drop = self.drop

        push((charno, token))
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
                drop()  # drop the wspaces/newlines
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
                self.emit_tag(mode='r')
                self.state = WS
            elif ttype == 'literals':
                self.emit_tag(mode='0')
                self.state = LIT
            elif ttype == 'tag':
                self.state = TWOTAGS
            elif ttype == 'end':
                self.emit_tag(mode='r')
                self.state = END
            else:
                assert False
        elif self.state == END:
            assert stash_size == 2
            assert ttype is None    # next token doesn't exist: tokenizer exhausted
            drop(last=True)
            self.emit_eof(ws=r'\s')
            self.state = EXHAUSTED
        elif self.state == (WS, TAG):
            assert stash_size == 3
            if ttype in tWS:
                self.emit_ws(just_one=True)
                self.emit_tag(mode='b')
                self.state = WS
            elif ttype == 'literals':
                self.emit_ws()
                self.emit_tag(mode='l')
                self.state = LIT
            elif ttype == 'tag':
                drop() # drop the WS, we will not use it
                self.state = TWOTAGS
            elif ttype == 'end':
                self.emit_ws(just_one=True)
                self.emit_tag(mode='b')
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

class SM(SM_NormWS):
    def feed(self, charno, ttype, token):
        push = self.stash.append
        drop = self.drop

        push((charno, token))
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
                self.emit_tag(mode='0')
                self.state = LIT
            elif ttype == 'tag':
                self.state = TWOTAGS
            elif ttype == 'end':
                self.emit_tag(mode='e')
                self.state = END
            else:
                assert False
        elif self.state == END:
            assert stash_size == 2
            assert ttype is None    # next token doesn't exist: tokenizer exhausted
            drop(last=True)
            self.emit_eof(ws=r'\n')
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
