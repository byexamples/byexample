import pprint, traceback, contextlib, sys

def build_where_msg(where, owner, msg=None):
    try:
        where = 'File "%s", line %i' % (where.filepath, where.start_lineno)
    except:
        if where:
            where = str(where)

    if owner:
        owner = "[%s]" % str(owner)
        where = ', '.join([where, owner]) if where else owner

    if msg:
        where += '\n' + msg

    return where


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
            language = example.runner.language
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

def print_example(example, use_colors, x):
    if x < 0:
        return

    print("::[Example]" + ":" * 59)
    print("  Found in: %s by: %s" % (example.filepath, example.finder))
    print("  Lines from: %s to: %s" % (example.start_lineno, example.end_lineno))
    print("  Indentation: |%s| (%i bytes)" % (example.indentation,
                                                len(example.indentation)))
    print("  Capture Tags: %s" % pprint.pformat(example.expected.captures, width=50))

    opts_repr = pprint.pformat(example.options.as_dict(), width=50)
    lines = opts_repr.split('\n')
    if len(lines) > 1:
        opts_repr = '\n    ' + ('\n    '.join(lines))
    print("  Options: %s" % opts_repr)

    print("..[Source]" + "." * 60)
    print(highlight_syntax(example, use_colors))

    print("..[Expected]" + "." * 58)
    _l = 0
    for e in example.expected.str.split('\n'):
        print("% 4i: %s" % (_l, e))
        _l += len(e) + 1

    print("..[Regexs]" + "." * 60)
    if len(example.expected.regexs) != len(example.expected.positions):
        print("Error: inconsistent regexs")
        print("  Regexs: %s" % example.expected.regexs)
        print("  Positions: %s" % example.expected.positions)

    for p, r in zip(example.expected.positions, example.expected.regexs):
        print("% 4i: %s" % (p, repr(r)))

    print("..[Run]" + "." * 63)
    print("  Runner: %s" % example.runner)

def print_execution(example, got, x):
    if x < 0:
        return

    print("..[Got]" + "." * 63)
    print(got)
    print(("." * 70) + '\n')

def constant(argumentless_method):
    placeholder = '_saved_constant_result_of_%s' % argumentless_method.__name__
    def wrapped(self):
        try:
            return getattr(self, placeholder)
        except AttributeError:
            val = argumentless_method(self)
            setattr(self, placeholder, val)
            return val

    return wrapped


@contextlib.contextmanager
def human_exceptions(where_default, verbosity, quiet, exitcode):
    ''' Print to stdout the message of the exception (if any)
        suppressing its traceback.
         - if verbosity is greather than zero, print the traceback.
         - if quiet is True, do not print anything.

        To enhance the print, print the 'where' attribute of the
        exception (if it has one) or the 'where_default'.

        Finally, exit the process with exitcode.
    '''
    try:
        yield
    except Exception as e:
        if quiet:
            pass
        else:
            where = getattr(e, 'where', where_default)
            msg = str(e)
            if verbosity >= 1:
                msg = traceback.format_exc()

            print("{where}\n{msg}".format(where=where, msg=msg))
        sys.exit(exitcode)

@contextlib.contextmanager
def enhance_exceptions(where, owner):
    where = build_where_msg(where, owner)
    try:
        yield
    except Exception as e:
        if not hasattr(e, 'where'):
            e.where = where
        raise e

