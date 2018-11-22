INIT, WS, WSz, LIT, TAG, EOF, DUPTAG = range(7)

tWS = ('wspaces', 'newlines')

def emit_ws(n):
    assert n in (0, 1)
    rx = (r'\s+(?!\s)') if n == 1 else (r'\s*(?!\s)')
    rc = n

def emit_literals(l, w=None):
    rx = re.escape(l)
    rc = len(l)

    if w:
        rx += w
        rc += 1

def emit_tag(t, not_end_in_ws=False):
    if not_end_in_ws:
        rx = r'(?:(?P<foo>.+?)(?<!\s))?'
        rc = 0
    else:
        rx = r'(?P<foo>.*?)'
        rc = 0

def emit_eof():
    rx = r'\s*\Z'
    rc = 0

def f():
    if state == INIT:
        if ttype in tWS:
            state = WS
        elif ttype == 'literals':
            state = LIT
        elif ttype == 'tag':
            save(token)
            state = TAG
        elif ttype = 'eof':
            state = EOF
        else:
            assert False
    elif state == WS:
        if ttype in tWS:
            state = WS  # ignore the last wspaces/newlines token
        elif ttype == 'literals':
            emit_ws(1)
            save(token)
            state = LIT
        elif ttype == 'tag':
            save(token)
            state = (WS, TAG)
        elif ttype = 'eof':
            state = EOF # ignore the first wspaces/newlines token
        else:
            assert False
    elif state == LIT:
        if ttype in tWS:
            state = (LIT, WS)
        elif ttype in ('literals', 'tag'):
            literals, = load()
            emit_literals(literals)
            save(token)
            state = LIT
        elif ttype = 'eof':
            literals, = load()
            emit_literals(literals)
            state = EOF
        else:
            assert False
    elif state == TAG:
        if ttype in tWS:
            tag, = load()
            emit_tag(tag, True)
            state = WS
        elif ttype == 'literals':
            tag, = load()
            emit_tag(tag)
            state = LIT
        elif ttype == 'tag':
            save(token)
            state = DUPTAG
        elif ttype = 'eof':
            tag, = load()
            emit_tag(tag, True)
            state = EOF
        else:
            assert False
    elif state == EOF:
        assert ttype is None    # next token doesn't exist: tokenizer exahusted
        assert not load()   # nothing "on hold"
        emit_eof()
        break
    elif state == (WS, TAG):
        if ttype in tWS:
            tag, = load()
            emit_ws(1)
            emit_tag(tag, True)
            state = WSz
        elif ttype == 'literals':
            tag, = load()
            emit_ws(1)
            emit_tag(tag)
            state = LIT
        elif ttype == 'tag':
            save(token)
            state = DUPTAG
        elif ttype = 'eof':
            tag, = load()
            emit_ws(1)
            emit_tag(tag, True)
            state = EOF
        else:
            assert False
    elif state == WSz:
        if ttype in tWS:
            state = WSz # ignore the next wspaces/newlines
        elif ttype == 'literals':
            emit_ws(0)
            save(token)
            state = LIT
        elif ttype == 'tag':
            save(token)
            state = (WSz, TAG)
        elif ttype = 'eof':
            state = EOF # ignore the first wspaces/newlines
        else:
            assert False
    elif state == (WSz, TAG):
        if ttype in tWS:
            # TODO XXX XXX XXX
            tag, = load()
            emit_ws(0)
            emit_tag(tag, True)
            state = WSz
        elif ttype == 'literals':
            tag, = load()
            emit_ws(0)
            emit_tag(tag)
            save(token)
            state = LIT
        elif ttype == 'tag':
            save(token)
            state = DUPTAG
        elif ttype = 'eof':
            tag, = load()
            emit_ws(0)
            emit_tag(tag, True)
            state = EOF
        else:
            assert False
    elif state == (LIT, WS):
        if ttype in tWS:
            state = (LIT, WS)   # ignore the next wspaces/newlines
        elif ttype == 'literals':
            literals, = load()
            emit_literals(literals, r'\s+(?!\s)')
            save(token)
            state = LIT
        elif ttype == 'tag':
            literals, = load()
            emit_literals(literals, r'\s+(?!\s)')
            save(token)
            state = TAG
        elif ttype = 'eof':
            literals, = load()
            emit_literals(literals)
            state = EOF
        else:
            assert False
    elif state == DUPTAG:
        print("error")
        break
    else:
        assert False

