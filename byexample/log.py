from logging import (Formatter, Logger,
                     DEBUG, INFO, WARNING, ERROR, CRITICAL,
                     getLogger)
import sys
import byexample.common

CHAT = INFO-1
class XFormatter(Formatter):
    def formatMessage(self, record):
        s = Formatter.formatMessage(self, record)

        name = record.name
        lvlno = record.levelno

        color = {
                DEBUG: 'none',
                CHAT:  'cyan',
                INFO:  'cyan',
                WARNING:  'yellow',
                ERROR:    'red',
                CRITICAL: 'red',
                }[lvlno]

        if getLogger(name).isEnabledFor(DEBUG):
            marker = {
                    DEBUG: 'dgb',
                    CHAT:  'chat',
                    INFO:  'info',
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
                    WARNING:  '[w]',
                    ERROR:    '[!]',
                    CRITICAL: '[!]',
                    }[lvlno]

        tag = "%s" % marker
        tag = byexample.common.colored(tag, color, use_colors=True)

        return "%s %s" % (tag, s)

class XLogger(Logger):
    def __init__(self, name, *args, **kargs):
        Logger.__init__(self, name, *args, **kargs)

    def chat(self, msg, *args, **kargs):
        return Logger.log(self, CHAT, msg, *args, **kargs)

    def human_exception(self, ex, where_default, advice, *args, **kargs):
        where = getattr(ex, 'where', where_default)
        fmt = "{where}\n{cls}: "

        if self.isEnabledFor(CHAT):
            m = traceback.format_exc()
            fmt += "{m}"
        else:
            m = "Rerun with -v to get a full stack trace."
            fmt += "{ex}\n\n{m}"

        cls = str(ex.__class__.__name__)
        msg = fmt.format(where=where, m=m, cls=cls, ex=str(ex))

        tmp = Logger.error(self, msg)
        if advice:
            Logger.info(self, advice, *args, **kargs)
        return tmp

def init_log_system():
    import logging
    logging.setLoggerClass(XLogger)

    logging.CHAT = CHAT
    logging.addLevelName(CHAT, 'CHAT')

    rlog = getLogger(name='root') # root

    ch = logging.StreamHandler(stream=sys.stdout)
    fmtter = XFormatter('%(message)s')

    ch.setFormatter(fmtter)
    rlog.addHandler(ch)
    rlog.setLevel(INFO)

    #rlog.setLevel(DEBUG)

    if True:
        rlog.critical("hey!!\nasasas")
        rlog.error("hey!!\nasasas")
        rlog.warning("hey!!\nasasas")
        rlog.info("hey!!\nasasas")
        rlog.chat("hey!!\nasasas")
        rlog.debug('fooo\nasasas')

