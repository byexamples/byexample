from __future__ import unicode_literals
import pprint, traceback, contextlib, os, string, shlex, logging, time
from . import regex as re
'''
>>> from byexample.common import tohuman, short_string
>>> import time

'''


def indent(s, indent=4):
    ''' Indent the given text.
        See doctest._indent for the code that inspired this.
        '''
    return re.compile('(?m)^(?!$)').sub(indent * ' ', s)


def short_string(s, max=14, sep='..'):
    ''' Return a shorter version of the string if its too large.

        Short string are returned as they are.
        >>> short_string('hello')
        'hello'

        But longer are truncated returning only the first and the last
        part of them using '..' as glue.
        >>> short_string('hello world my friend')
        'hello ..friend'

        You can change the separator but larger ones consume
        more of your data
        >>> short_string('hello world my friend', sep='::::')
        'hello::::riend'

        Changing the maximum size is allowed too of course (rounded
        to the lower even number)

        >>> short_string('hello world my friend', max=9)
        'hel..end'

    '''
    assert len(sep) >= 1 and max > 4

    n = (max - len(sep)) // 2
    assert n >= 2

    if len(s) > max:
        return s[:n] + sep + s[-n:]
    return s


def build_where_msg(where, owner, msg=None, use_colors=False):
    tmp = []
    try:
        tmp.append('File "%s", line %i' % (where.filepath, where.start_lineno))
    except:
        if where:
            tmp.append(str(where))

    if owner:
        owner = "[%s]" % str(owner)
        tmp.append((', ' + owner) if tmp else owner)

    try:
        tmp.append('\n' + indent(highlight_syntax(where, use_colors)))
    except Exception as e:
        pass

    if msg:
        tmp.append('\n' + msg)

    return ''.join(tmp)


def colored(s, color, use_colors):
    if use_colors:
        if color == 'none':
            return s
        c = {'green': 32, 'red': 31, 'yellow': 33, 'cyan': 36}[color]
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
        snippet = example.snippet
        if not use_colors:
            return snippet

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

            return pygments.highlight(snippet, lexer, formatter)
        except:
            pass

        # if something fails, just keep going: the highlight syntax is
        # nice to have but not a must to have.
        return snippet

except ImportError:
    # do not use any highlight syntax
    def highlight_syntax(example, use_colors):
        return example.snippet


def tohuman(s):
    ''' Simple but quite human representation of <s>.

        >>> tohuman("hi")
        'Hi'

        >>> tohuman("HiJimmy-Whats_up?")
        'Hijimmy Whats Up?'

        >>> tohuman(["hello", "world"])
        'Hello, World'

        >>> tohuman(tohuman)
        'Function*'
    '''
    if isinstance(s, (list, tuple, set)):
        if isinstance(s, set):
            s = sorted(list(s))
        s = ', '.join(s)
    elif not isinstance(s, str):
        s = s.__class__.__name__
        s += "*"
    s = s.replace("-", " ").replace("_", " ")
    s = ' '.join(w.capitalize() for w in s.split())

    return s


def constant(method):
    ''' Cache the result of calling the method in the first call
        and save the result in <self>.

        The method must always return the same results and the result
        itself must be an immutable object so it is safe to cache the
        result and share it among different threads.

        Further calls to the method will yield the same result even
        if the arguments or <self> differ.

        If you want to cache the different values returned under different
        arguments, see functools.lru_cache. However, byexample may not be
        able to preserve correctness and thread-safety for it. (consider
        that as a "TODO").
        '''
    placeholder = '_saved_constant_result_of_%s' % method.__name__

    def wrapped(self, *args, **kargs):
        try:
            return getattr(self, placeholder)
        except AttributeError:
            val = method(self, *args, **kargs)
            setattr(self, placeholder, val)
            return val

    return wrapped


def transfer_constants(src, dst):
    ''' Transfer the cached results from one object to another.

        See common.constant().
        '''
    for name, val in src.__dict__.items():
        if name.startswith('_saved_constant_result_of_'):
            setattr(dst, name, val)


@contextlib.contextmanager
def human_exceptions(where_default):
    ''' Print to stdout the message of the exception (if any)
        in a human-understandable way.

        To enhance the message, print the <where> attribute of the
        exception (if it has one) or the <where_default>.

        If the captured exception is a SystemExit, do not print anything.

        This allows to use SystemExit as a abort mechanism without printing
        anything to the console.

        If the captured exception is a KeyboardInterrupt, assume that
        the user want to 'abort' the execution, so it will print
        just a message saying that.

        No exception will be propagated out of this context manager.

        The context manager will yield a dictionary with the
        key 'exc' set to the exception caught if any or it will
        remain empty if no exception is caught.
    '''
    o = {}
    try:
        yield o
    except KeyboardInterrupt as e:
        rlog = logging.getLogger(name='byexample')
        rlog.user_aborted()

        o['exc'] = e
    except SystemExit as e:
        o['exc'] = e
    except BaseException as e:
        rlog = logging.getLogger(name='byexample')
        rlog.exception(msg=None, where=where_default)
        o['exc'] = e


@contextlib.contextmanager
def enhance_exceptions(where, owner, use_colors=False):
    try:
        yield
    except BaseException as e:
        if not hasattr(e, 'where'):
            e.where = build_where_msg(where, owner, use_colors=use_colors)
        raise e


def abspath(*args):
    ''' Return the absolute path from the join of <args>.
        The first item of <args> can be a filename which it will
        be stripped off to keep just its dirname.
        '''
    base = os.path.dirname(args[0])
    path = os.path.join(base, *args[1:])
    return os.path.abspath(path)


try:
    from shlex import quote as shlex_quote
except ImportError:
    from pipes import quote as shlex_quote


class ShebangTemplate(string.Template):
    delimiter = '%'

    def quote_and_substitute(self, tokens, joined=True):
        r'''
        Quote each token to be suitable for shell expansion and then
        perform a substitution in the template.

        >>> from byexample.runner import ShebangTemplate
        >>> tokens = {'a': ['-i', "-c", 'blue = "1"'],
        ...           'e': '/usr/bin/env', 'p': 'python'}

        The basic case is a simple template where each token
        is quoted except the lists: each item is quoted but not the
        whole list as a single unit.

        >>> shebang = '%e %p %a'
        >>> print(ShebangTemplate(shebang).quote_and_substitute(tokens))
        /usr/bin/env python -i -c 'blue = "1"'

        This works even if the token in the template are already quoted
        >>> shebang = '/bin/sh -c \'%e %p %a >/dev/null\''
        >>> print(ShebangTemplate(shebang).quote_and_substitute(tokens))
        /bin/sh -c '/usr/bin/env python -i -c '"'"'blue = "1"'"'"' >/dev/null'

        Here is another pair of examples:
        >>> tokens = {'a': ['-i', "-c", 'blue = \'1\''],
        ...           'e': '/usr/bin/env', 'p': 'py\'thon'}

        >>> shebang = '%e %p %a'
        >>> print(ShebangTemplate(shebang).quote_and_substitute(tokens))
        /usr/bin/env 'py'"'"'thon' -i -c 'blue = '"'"'1'"'"''

        >>> shebang = '/bin/sh -c \'%e %p %a >/dev/null\''
        >>> print(ShebangTemplate(shebang).quote_and_substitute(tokens))
        /bin/sh -c '/usr/bin/env '"'"'py'"'"'"'"'"'"'"'"'thon'"'"' -i -c '"'"'blue = '"'"'"'"'"'"'"'"'1'"'"'"'"'"'"'"'"''"'"' >/dev/null'

        As seen, by default ShebangTemplate returns a string, a "joined"
        version of all the elements expanded.

        If you need it, you can skip that (suitable for calling
        subprocess.call or similar without using a shell):
        >>> shebang = '%e %p %a'
        >>> l = ShebangTemplate(shebang).quote_and_substitute(tokens, joined=False)
        >>> print(" --- ".join(l))
        /usr/bin/env --- py'thon --- -i --- -c --- blue = '1'
        '''

        self._tokens = {}
        self._not_quote_them = []
        for k, v in tokens.items():
            if isinstance(v, (list, tuple)):
                self._tokens[k] = ' '.join(shlex_quote(i) for i in v)
            else:
                self._tokens[k] = shlex_quote(v)

        cmd = []
        for x in shlex.split(self.template):
            # *before* the expansion, will this require quote? (will yield
            # more than a single item?)
            should_quote = len(shlex.split(x)) > 1

            # perform the expansion
            x = ShebangTemplate(x).substitute(self._tokens)

            # was needed to quote this *before* the expansion?
            if should_quote:
                x = shlex_quote(x)

            cmd.append(x)

        cmd = ' '.join(cmd)
        return cmd if joined else shlex.split(cmd)


class Countdown:
    ''' Keep track of how much time left in seconds.

        >>> from byexample.common import Countdown
        >>> cdown = Countdown(left=0.5)
        >>> cdown
        Countdown(left=0.5, is_running=False)

        To start counting down use `start` and `stop`:

        >>> cdown.start()
        >>> time.sleep(0.1)
        >>> cdown.is_running()
        True
        >>> cdown.stop()
        Countdown<...>

        Then you can check how much time left and if it
        did run out of time or not:

        >>> 0.2 < cdown.left() < 0.4     # approx, avoid float issues
        True
        >>> cdown.did_run_out()
        False

        >>> cdown.is_running()
        False

        Starting when the counter is running is an error:

        >>> cdown.start()
        >>> cdown.start()
        Traceback<...>
        ValueError: The counter is already running

        The same if we want to check how much time left:
        >>> cdown.left()
        Traceback<...>
        ValueError: The counter is running

        And of course we have the same problem if we want to
        stop the counter when it is not running:

        >>> cdown.stop()
        Countdown<...>
        >>> cdown.stop()
        Traceback<...>
        ValueError: The counter is not running

        Consuming more time than the configured is possible:

        >>> cdown.start()
        >>> time.sleep(0.5)
        >>> cdown.stop()
        Countdown<...>

        The counter will say that left zero, even if we consumed
        more than the possible:

        >>> cdown.left()
        0
        >>> cdown.did_run_out()
        True

        '''
    def __init__(self, left):
        self._left = left
        self._start_mark = None

    def __repr__(self):
        return "Countdown(left={}, is_running={})".format(
            self.left(), self.is_running()
        )

    def start(self):
        if self.is_running():
            raise ValueError("The counter is already running")
        self._start_mark = self._now()

    def stop(self):
        if not self.is_running():
            raise ValueError("The counter is not running")
        elapsed = self._now() - self._start_mark
        self._left = max(self._left - elapsed, 0)
        self._start_mark = None

        return self

    def left(self):
        if self.is_running():
            raise ValueError("The counter is running")
        return self._left

    def did_run_out(self):
        return self.left() == 0

    def is_running(self):
        return self._start_mark is not None

    def _now(self):
        return time.perf_counter()
