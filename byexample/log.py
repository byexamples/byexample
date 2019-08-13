from logging import (Formatter, Logger,
                     DEBUG, INFO, WARNING, ERROR, CRITICAL,
                     getLogger)
import sys, logging
from byexample.common import colored

NOTE = INFO+1
CHAT = INFO-1
class XFormatter(Formatter):
    def format(self, record):
        self._cur_record = record
        self._cur_logger = getLogger(record.name)
        return Formatter.format(self, record)

    def formatMessage(self, record):
        s = Formatter.formatMessage(self, record)

        name = record.name
        lvlno = record.levelno

        color = {
                DEBUG: 'none',
                CHAT:  'cyan',
                INFO:  'cyan',
                NOTE:  'cyan',
                WARNING:  'yellow',
                ERROR:    'red',
                CRITICAL: 'red',
                }[lvlno]

        if getLogger(name).isEnabledFor(DEBUG):
            marker = {
                    DEBUG: 'dgb',
                    CHAT:  'chat',
                    INFO:  'info',
                    NOTE:  'note',
                    WARNING:  'warn',
                    ERROR:    'error',
                    CRITICAL: 'crit',
                    }[lvlno]
            marker = "%s:%s" % (marker, name)
        else:
            marker = {
                    DEBUG: '-',
                    CHAT:  '[i]',
                    INFO:  '[i]',
                    NOTE:  '[i]',
                    WARNING:  '[w]',
                    ERROR:    '[!]',
                    CRITICAL: '[!]',
                    }[lvlno]

        tag = "%s" % marker
        tag = colored(tag, color, use_colors=logging.use_colors_in_logs)

        return "%s %s" % (tag, s)

    def formatException(self, ei):
        ''' Format the stack of the exception only
            if the log level is CHAT or below (eg DEBUG).

            Otherwise, format only the message of the exception
            hidding the stack and the exception class.

            In this case let the user know that if he/she wants
            to see the traceback he/she can see it enabling a
            more verbose log level.
            '''
        if self._cur_logger.isEnabledFor(CHAT):
            return Formatter.formatException(self, ei)
        else:
            return '%s\n\n%s' % (str(ei[1]),
                                "Rerun with -v to get a full stack trace."
                                )


class XLogger(Logger):
    def __init__(self, name, *args, **kargs):
        Logger.__init__(self, name, *args, **kargs)

    def chat(self, msg, *args, **kargs):
        return Logger.log(self, CHAT, msg, *args, **kargs)

    def note(self, msg, *args, **kargs):
        return Logger.log(self, NOTE, msg, *args, **kargs)

    def user_aborted(self):
        ''' Message (info) to notify that the execution was
            aborted (aka Ctrl-C)
            '''
        return self.note('Execution aborted by the user.')

    def exception(self, msg, *args, exc_info=True, **kwargs):
        ''' Log the current caught exception with a twist:
            if <msg> is None, create a default 'human readable'
            message, augmented by kwargs['where'] and exception.where
            attributes (contextual messages).

            If <msg> is not None, run as usual (logging.Logger.exception)
            '''
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
            msg = msg.format(where_default=where_default,
                             where=where)

            return self.error(msg, exc_info=True, **kwargs)
        else:
            return Logger.exception(self, msg, *args, exc_info=exc_info, **kwargs)

_logger_stack = []
def clog():
    return _logger_stack[-1]

def log_context(logger_name):
    global _logger_stack

    assert _logger_stack
    current = getLogger(name=logger_name)

    def decorator(func):
        def wrapped(*args, **kargs):
            try:
                _logger_stack.append(current)
                return func(*args, **kargs)
            finally:
                _logger_stack.pop()
        return wrapped
    return decorator

class XStreamHandler(logging.StreamHandler):
    def __init__(self, *args, **kargs):
        logging.StreamHandler.__init__(self, *args, **kargs)

def init_log_system():
    global _logger_stack

    # Convenient global variable to control
    # if we should put some color or not in
    # the logs.
    # Its use is intended for the logging
    # system only
    logging.use_colors_in_logs = False

    logging.setLoggerClass(XLogger)

    logging.CHAT = CHAT
    logging.addLevelName(CHAT, 'CHAT')

    logging.NOTE = NOTE
    logging.addLevelName(NOTE, 'NOTE')

    rlog = getLogger(name='byexample') # root

    ch = XStreamHandler(stream=sys.stdout)

    fmtter = XFormatter('%(message)s')
    ch.setFormatter(fmtter)

    rlog.addHandler(ch)

    rlog.setLevel(NOTE)

    # Set up the global logger.
    # Activate and deactivate sub loggers using log_context
    # decorator on the top level functions
    _logger_stack.append(rlog)

    rlog.setLevel(CHAT)

    logging.use_colors_in_logs = True
    if True:
        rlog.critical("hey!!\nasasas")
        rlog.error("hey!!\nasasas")
        rlog.warning("hey!!\nasasas")
        rlog.info("hey!!\nasasas")
        rlog.chat("hey!!\nasasas")
        rlog.debug('fooo\nasasas')

