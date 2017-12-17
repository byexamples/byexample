
def build_exception_msg(msg, where, parser=None):
    start_lineno, _, filepath = where
    who = "" if parser is None else (", [%s]" % str(parser))
    return 'File "%s", line %i%s\n%s' % (filepath, start_lineno, who, msg)


def log(msg, x):
    if x >= 0:
        print(msg)

def colored(s, color, use_colors):
    if use_colors:
        c = {'green': 32, 'red': 31, 'yellow': 33}[color]
        return "\033[%sm%s\033[0m" % (c, s)
    else:
        return s

def tohuman(s):
    s = s.replace("-", " ").replace("_", " ")
    s = ' '.join(w.capitalize() for w in s.split())

    return s

def print_example(example):
    print("*" * 70)
    for i, field in enumerate(example._fields):
        if field in ('expected_re', 'match'):
            continue

        if field == 'indentation':
            print("%s: |%s| (%i bytes)" % (field, example[i],
                                            len(example[i])))
            continue

        sep = '\n' if field in ('source', 'expected') else ' '
        print("%s:%s%s" % (field, sep, example[i]))

    print('\n')

