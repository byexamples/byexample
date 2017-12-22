
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

try:
    import pygments
    import pygments.lexers
    import pygments.formatters
    import pygments.formatters.terminal
    import pygments.formatters.terminal256

    def highlight_syntax(example, use_colors):
        if not use_colors:
            return example.source

        try:
            # we want to use colors, let's try to find a valid lexer
            language = example.interpreter.language
            lexer = pygments.lexers.get_lexer_by_name(language)

            # we want the output to be valid for a terminal...
            # pygments supports:
            #  - terminal.TerminalFormatter
            #  - terminal256.Terminal256Formatter
            #  - terminal256.TerminalTrueColorFormatter
            #
            # should we allow the user to change this?
            formatter = pygments.formatters.terminal.TerminalFormatter()

            return pygments.highlight(example.source, lexer, formatter)
        except:
            pass

        # if something fails, just keep going: the highlight syntax is
        # nice to have but not a must to have.
        return example.source

except ImportError:
    # do not use any highlight syntax
    def highlight_syntax(example, use_colors):
        return example.source

def tohuman(s):
    s = s.replace("-", " ").replace("_", " ")
    s = ' '.join(w.capitalize() for w in s.split())

    return s

def print_example(example, use_colors):
    print("*" * 70)
    for i, field in enumerate(example._fields):
        if field in ('expected_re', 'match'):
            continue

        if field == 'indentation':
            print("%s: |%s| (%i bytes)" % (field, example[i],
                                            len(example[i])))
            continue

        sep = '\n' if field in ('source', 'expected') else ' '
        if field == 'source':
            print("%s:%s%s" % (field, sep, highlight_syntax(example, use_colors)))
        else:
            print("%s:%s%s" % (field, sep, example[i]))

    print('\n')

