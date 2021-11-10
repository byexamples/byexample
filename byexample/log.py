from logging import Formatter, Logger, getLogger
import sys, logging
import contextlib

from .common import colored, highlight_syntax, indent
from .log_level import TRACE, DEBUG, CHAT, INFO, NOTE, WARNING, ERROR, CRITICAL
import functools, threading
from .prof import profile
r'''

Byexample's logging system:

                                     all messages   |  messages enabled only
                                    (must be fast)  |    (can be slow)
                                                    |
                                                    |        (none) XFormatter
                                                    |    filter :     : format
          log                    log       propagate            :     :
  Thread 1 --> _logger_stack[top] --> XLogger --> XLogger --> XStreamHandler
                                        (A)    |  (root)        |     |
                                               |                |     V emit
  Thread 2 --> _logger_stack[top] --> XLogger -/    |           |   Stream
                                        (B)         |           |   Handler
                                                    |           | (no concerns)
                                                    |      emit V
                                                    |        Concern
                                                    |   (thread specific)

The _logger_stack, XLogger objects, the filter (none), the XFormatter and the
XStreamHandler objects are *shared* among the threads and therefore they *must*
be thread-safe.

'Concern' is a thread-specific object so it is *not* shared. If the one o more
concern objects access to a shared object by themselves, it is up to them to
make the access thread-safe. See byexample.concern.

StreamHandler is the default handler when the Concern system was not loaded
yet. It is thread-safe because we use an explicit RLock.
This should not be a performance problem because we expect to call StreamHandler
*only* in early stages of byexample bootstrap, when there is a single thread
anyways.
'''


class XFormatter(Formatter):
    def shorter_name(self, name):
        t = 'byexample.'
        if name.startswith(t):
            return name[len(t):]
        else:
            return name

    def formatMessage(self, record):
        s = Formatter.formatMessage(self, record)

        name = record.name
        lvlno = record.levelno
        logger = getLogger(name)

        color = {
            DEBUG: 'none',
            CHAT: 'cyan',
            INFO: 'cyan',
            NOTE: 'cyan',
            WARNING: 'yellow',
            ERROR: 'red',
            CRITICAL: 'red',
        }[lvlno]

        if lvlno == DEBUG or getattr(record, 'no_marker', False):
            marker = ''
        elif logger.isEnabledFor(DEBUG):
            marker = {
                DEBUG: '',
                CHAT: 'chat',
                INFO: 'info',
                NOTE: 'note',
                WARNING: 'warn',
                ERROR: 'error',
                CRITICAL: 'crit',
            }[lvlno]
            marker = "%s:%s" % (marker, self.shorter_name(name))
        elif logger.isEnabledFor(CHAT):
            marker = {
                DEBUG: '',
                CHAT: '[i:%s]',
                INFO: '[i:%s]',
                NOTE: '[i:%s]',
                WARNING: '[w:%s]',
                ERROR: '[!:%s]',
                CRITICAL: '[!:%s]',
            }[lvlno]
            marker = marker % self.shorter_name(name)
        else:
            marker = {
                DEBUG: '',
                CHAT: '[i]',
                INFO: '[i]',
                NOTE: '[i]',
                WARNING: '[w]',
                ERROR: '[!]',
                CRITICAL: '[!]',
            }[lvlno]

        use_colors = getLogger('byexample').use_colors
        if marker and not getattr(record, 'disable_prefix', False):
            marker = colored(marker, color, use_colors=use_colors)
            s = "%s %s" % (marker, s)

        ex = getattr(record, 'example', None)
        if ex is not None:
            if logger.isEnabledFor(DEBUG):
                ex.pretty_print()
            else:
                s += '\n' + indent(highlight_syntax(ex, use_colors))

        # Precompute the message for the exception (if any).
        # Record's exc_text will be added to the format message by
        # the parent class Formatter
        if record.exc_info and not record.exc_text:
            record.exc_text = self.formatException(
                record.exc_info, logger.isEnabledFor(INFO)
            )

        return s

    def formatException(self, ei, enabled_for_info_or_below=False):
        ''' Format the stack of the exception only
            if the log level is INFO or below (eg DEBUG).

            Otherwise, format only the message of the exception
            hidding the stack and the exception class.

            In this case let the user know that if he/she wants
            to see the traceback he/she can see it enabling a
            more verbose log level.
            '''
        if enabled_for_info_or_below:
            return Formatter.formatException(self, ei)
        else:
            return '%s\n\n%s' % (
                str(ei[1]), "Rerun with -vvv to get a full stack trace."
            )


class XLogger(Logger):
    def __init__(self, name, *args, **kargs):
        Logger.__init__(self, name, *args, **kargs)

    def trace(self, msg, *args, **kargs):
        return self.log(TRACE, msg, *args, **kargs)

    def debug(self, msg, *args, **kargs):
        return self.log(DEBUG, msg, *args, **kargs)

    def info(self, msg, *args, **kargs):
        return self.log(INFO, msg, *args, **kargs)

    def chat(self, msg, *args, **kargs):
        return self.log(CHAT, msg, *args, **kargs)

    def note(self, msg, *args, **kargs):
        return self.log(NOTE, msg, *args, **kargs)

    def warning(self, msg, *args, **kargs):
        return self.log(WARNING, msg, *args, **kargs)

    def error(self, msg, *args, **kargs):
        return self.log(ERROR, msg, *args, **kargs)

    def critical(self, msg, *args, **kargs):
        return self.log(CRITICAL, msg, *args, **kargs)

    # valid, non-deprecated alias
    warn = warning
    err = error
    crit = critical

    def log(self, level, msg, *args, **kargs):
        extra = kargs.pop('extra', {})
        if 'example' in kargs:
            extra['example'] = kargs.pop('example')
        if 'disable_prefix' in kargs:
            extra['disable_prefix'] = kargs.pop('disable_prefix')

        return Logger.log(self, level, msg, *args, extra=extra, **kargs)

    def user_aborted(self):
        ''' Message (info) to notify that the execution was
            aborted (aka Ctrl-C)
            '''
        return self.note('Execution aborted by the user.')

    def exception(self, msg, *args, **kwargs):
        ''' Log the current caught exception with a twist:
            if <msg> is None, create a default 'human readable'
            message, augmented by kwargs['where'] and exception.where
            attributes (contextual messages).

            If <msg> is not None, run as usual (logging.Logger.exception)
            '''
        exc_info = kwargs.pop('exc_info', True)
        where_default = kwargs.pop('where', None)
        if not msg:
            msg = 'Something went wrong'

            if where_default:
                msg += ' {where_default}'

            ex = sys.exc_info()[1]
            where = getattr(ex, 'where', None)
            if where:
                msg += ', {where}'

            msg += ':'
            msg = msg.format(where_default=where_default, where=where)

            return self.error(msg, exc_info=True, **kwargs)
        else:
            return Logger.exception(
                self, msg, *args, exc_info=exc_info, **kwargs
            )


class _LoggerLocalStack(threading.local):
    def __init__(self):
        self.stack = []
        self.concerns = None

    def __len__(self):
        return len(self.stack)

    def append(self, item):
        return self.stack.append(item)

    def pop(self):
        return self.stack.pop()

    def __getitem__(self, ix):
        return self.stack[ix]

    def __setitem__(self, ix, v):
        self.stack[ix] = v

    def __delitem__(self, ix):
        del self.stack[ix]


_logger_stack = _LoggerLocalStack()


def clog():
    return _logger_stack[-1]


def log_context(logger_name):
    global _logger_stack

    def decorator(func):
        @functools.wraps(func)
        def wrapped(*args, **kargs):
            assert _logger_stack
            current = getLogger(name=logger_name)

            try:
                _logger_stack.append(current)
                return func(*args, **kargs)
            finally:
                _logger_stack.pop()

        return wrapped

    return decorator


@contextlib.contextmanager
def log_with(logger_name, child=True):
    global _logger_stack
    assert _logger_stack
    if child:
        current = _logger_stack[-1].getChild(logger_name)
    else:
        current = getLogger(name=logger_name)

    try:
        _logger_stack.append(current)
        yield current
    finally:
        _logger_stack.pop()


class XStreamHandler(logging.StreamHandler):
    def __init__(self, *args, **kargs):
        logging.StreamHandler.__init__(self, *args, **kargs)

        # We have this lock only to protect our parent
        # StreamHandler's emit call.
        # We don't relay on self.createLock/self.acquire/self.release
        # which are called more times than the needed so they are disabled
        self._stream_handler_lck = threading.RLock()

    @profile
    def emit(self, record):
        # XStreamHandler will be called from different threads
        # so we need to send the messages to the corrensponding
        # 'concerns' set for the current thread.
        concerns = _logger_stack.concerns

        # If None, it means that we are not running un multithreading
        # mode and the concerns system is not up.
        if concerns is None:
            with self._stream_handler_lck:
                return logging.StreamHandler.emit(self, record)

        # format() and handleError() "are" thread safe. See XFormatter
        try:
            msg = self.format(record)
            concerns.event('log', msg=msg)
        except Exception:
            self.handleError(record)

    def createLock(self):
        self.lock = None

    def acquire(self):
        return

    def release(self):
        return


def init_log_system(level=NOTE, use_colors=False):
    ''' Initialize the log system.

        The log system has 4 stages:

         - not initialized:
            you can log things but what will happen is undefined
         - initialized but basic configuration only:
            things will be logged to stderr, not thread safe;
            logs should come from the main thread only
         - fully configured globally but not per thread
            the messages will be forwarded to the concerns' emit()
            hooks, it is up to them what to do with the messages;
            logs should come from the main thread only
         - thread specific configured (per thread)
            enable the thread to interact with the logging system
            in a thread-safe way

        To move from one stage to the other call:

         - init_log_system (in the main thread)
         - configure_log_system (in the main thread)
         - init_thread_specific_log_system (in each thread)

        At the end of the program execution the program should
        call to shutdown_log_system.
    '''
    global _logger_stack

    logging.setLoggerClass(XLogger)

    logging.CHAT = CHAT
    logging.addLevelName(CHAT, 'CHAT')

    logging.NOTE = NOTE
    logging.addLevelName(NOTE, 'NOTE')

    logging.TRACE = TRACE
    logging.addLevelName(TRACE, 'TRACE')

    rlog = getLogger(name='byexample')  # root

    ch = XStreamHandler(stream=sys.stdout)

    fmtter = XFormatter('%(message)s')
    ch.setFormatter(fmtter)

    rlog.addHandler(ch)

    # Set up the global logger (for this thread).
    # Activate and deactivate sub loggers using log_context
    # decorator on the top level functions
    #
    # Other threads will have to call the public version of this
    # function too with a non-None 'concerns' parameter
    _internal_init_thread_specific_log_system(None)

    assert level is not None
    assert use_colors is not None

    # The main thead will have to call the public version of this
    # function with a non-None 'concerns' parameter.
    _internal_configure_log_system(
        concerns=None, default_level=level, use_colors=use_colors
    )


def _internal_init_thread_specific_log_system(concerns):
    global _logger_stack

    rlog = getLogger(name='byexample')  # root
    _logger_stack.append(rlog)
    _logger_stack.concerns = concerns


def init_thread_specific_log_system(concerns):
    assert concerns is not None
    _internal_init_thread_specific_log_system(concerns)


def _internal_configure_log_system(concerns, default_level, use_colors):
    global _logger_stack
    rlog = getLogger(name='byexample')  # root
    if default_level is not None:
        rlog.setLevel(default_level)

    if use_colors is not None:
        rlog.use_colors = use_colors

    if concerns is not None:
        _logger_stack.concerns = concerns


def configure_log_system(default_level=None, use_colors=None, concerns=None):
    assert concerns is not None
    _internal_configure_log_system(
        default_level=default_level, use_colors=use_colors, concerns=concerns
    )


def setLogLevels(levels):
    prev_lvls = {}
    for name, lvl in levels.items():
        if not name.startswith('byexample.') and name != 'byexample':
            name = 'byexample.' + name

        l = getLogger(name)
        prev_lvls[name] = l.level
        l.setLevel(lvl)

    return prev_lvls


def shutdown_log_system():
    rlog = getLogger(name='byexample')  # root
