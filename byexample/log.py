from logging import Formatter, Logger, getLogger
import sys, logging
import contextlib

from .common import colored, highlight_syntax, indent
from .log_level import TRACE, DEBUG, CHAT, INFO, NOTE, WARNING, ERROR, CRITICAL


class XFormatter(Formatter):
    def format(self, record):
        self._cur_record = record
        self._cur_logger = getLogger(record.name)
        return Formatter.format(self, record)

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

        return s

    def formatException(self, ei):
        ''' Format the stack of the exception only
            if the log level is INFO or below (eg DEBUG).

            Otherwise, format only the message of the exception
            hidding the stack and the exception class.

            In this case let the user know that if he/she wants
            to see the traceback he/she can see it enabling a
            more verbose log level.
            '''
        if self._cur_logger.isEnabledFor(INFO):
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


_logger_stack = []


def clog():
    return _logger_stack[-1]


def log_context(logger_name):
    global _logger_stack

    def decorator(func):
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
        self.concerns = None

    def emit(self, record):
        if self.concerns is None:
            return logging.StreamHandler.emit(self, record)

        try:
            msg = self.format(record)
            self.concerns.event('log', msg=msg)
        except Exception:
            self.handleError(record)

    def createLock(self):
        self.lock = None

    def acquire(self):
        return

    def release(self):
        return


def init_log_system(level=NOTE, use_colors=False):
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
    rlog.xstream_handler = ch

    # Set up the global logger.
    # Activate and deactivate sub loggers using log_context
    # decorator on the top level functions
    _logger_stack.append(rlog)

    assert level is not None
    assert use_colors is not None
    configure_log_system(default_level=level, use_colors=use_colors)
    rlog.xstream_handler.concerns = None


def configure_log_system(default_level=None, use_colors=None, concerns=None):
    rlog = getLogger(name='byexample')  # root
    if default_level is not None:
        rlog.setLevel(default_level)

    if use_colors is not None:
        rlog.use_colors = use_colors

    if concerns is not None:
        rlog.xstream_handler.concerns = concerns


def setLogLevels(levels):
    prev_lvls = {}
    for name, lvl in levels.items():
        if not name.startswith('byexample.') and name != 'byexample':
            name = 'byexample.' + name

        l = getLogger(name)
        prev_lvls[name] = l.level
        l.setLevel(lvl)

    return prev_lvls
