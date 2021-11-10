from __future__ import unicode_literals
from .common import highlight_syntax

from .log import clog, DEBUG, getLogger
import pprint
'''
>>> from byexample.log import init_log_system
>>> init_log_system()
'''


class Where(object):
    def __init__(self, start_lineno, end_lineno, filepath, zdelimiter):
        self.start_lineno = start_lineno
        self.end_lineno = end_lineno
        self.filepath = filepath
        self.zdelimiter = zdelimiter

    def as_tuple(self):
        return (
            self.start_lineno, self.end_lineno, self.filepath, self.zdelimiter
        )

    def __iter__(self):
        return iter(self.as_tuple())

    def __repr__(self):
        return repr(self.as_tuple())


class Zone(object):
    def __init__(self, zdelimiter, zone_str, where):
        self.zdelimiter = zdelimiter
        self.str = zone_str
        self.where = where


class Example(object):
    r'''
    The unit work of byexample: the example.

    It represents a example found in <where> by the <finder> that should be
    parsed by the <parser> and executed later by the <runnner>.

    The piece of text found is given by <snippet> and <extracted_str>:
    the code the be executed and the expected output.

    These two are *incomplete* and further processing is need by <parser>

    >>> from byexample.finder import _build_fake_example

    >>> example = _build_fake_example('f()', '42', fully_parsed=False)
    >>> example
    Example (not parsed yet) [python] in file file.md, lines 0-2

    The example is incomplete or not fully parsed because the <snippet> may
    not be the code in its final state; the expected regex doesn't exist nor
    the options.

    >>> example.source
    <...>
    AttributeError: 'Example' object has no attribute 'source'

    >>> example.expected
    <...>
    AttributeError: 'Example' object has no attribute 'expected'

    >>> example.options
    <...>
    AttributeError: 'Example' object has no attribute 'options'

    After the completion those attributes should be defined

    >>> example.parse_yourself()
    Example [python] in file file.md, lines 0-2

    >>> example.source
    'f()\n'

    >>> example.expected.str
    '42'

    >>> example.options
    {'capture': True,
     'input_prefix_range': (6, 12),
     'norm_ws': False,
     'rm': [],
     'tags': True,
     'type': False}

    The example will have a reference to the current options
    which are the combination (stack) of all the options from the
    command line and the example's option.

    This is set only during the execution (see FileExecutor) so
    it is undefined even after "parsing yourself" and because it is
    a temporal setting, it will be undefined after the execution
    (the example should not have a reference for too much time)

    >>> example.current_options
    <...>
    AttributeError: 'Example' object has no attribute 'current_options'

    '''
    def __init__(
        self, finder, runner, parser, snippet, expected_str, indent, where
    ):
        self.finder, self.runner, self.parser = finder, runner, parser
        self.snippet, self.expected_str, self.indentation = snippet, expected_str, indent

        self.start_lineno, self.end_lineno, self.filepath, self.zdelimiter = where

        self.fully_parsed = False

    def parse_yourself(self, concerns=None):
        if self.fully_parsed:
            raise ValueError("You cannot parse/build an example twice: " + \
                             repr(self))

        where = Where(
            self.start_lineno, self.end_lineno, self.filepath, self.zdelimiter
        )
        self.parser.parse(self, concerns)
        self.fully_parsed = True

        return self

    def __repr__(self):
        f = "" if self.fully_parsed else "(not parsed yet) "
        return "Example %s[%s] in file %s, lines %i-%i" % (
            f, self.runner.language, self.filepath, self.start_lineno,
            self.end_lineno
        )

    def pretty_print(self):
        log = clog()

        # header
        log.chat(
            '%s (lines %s-%s:%s) [%s|%s]%s', self.filepath, self.start_lineno,
            self.end_lineno, self.runner.language, self.finder, self.runner,
            "" if self.fully_parsed else " (not parsed yet)"
        )

        # source
        use_colors = getLogger('byexample').use_colors
        log.chat(highlight_syntax(self, use_colors), extra={'no_marker': True})

        if log.isEnabledFor(DEBUG):
            tmp = [' len: expected line']
            _l = 0
            for e in self.expected_str.split('\n'):
                tmp.append("% 4i: %s" % (_l, e))
                _l += len(e) + 1

            tmp = '\n'.join(tmp)
            log.debug(tmp, extra={'no_marker': True})
        else:
            log.chat(self.expected_str, extra={'no_marker': True})

        if not self.fully_parsed:
            return

        log.debug(
            'Indentation: |%s| (%i bytes)', self.indentation,
            len(self.indentation)
        )

        capture_tag_names = list(
            sorted(n for n in self.expected.tags_by_idx.values() if n != None)
        )
        log.chat(
            'Capture tags: %s', pprint.pformat(capture_tag_names, width=50)
        )

        inputs = []
        for prefix, inp in self.input_list:
            n = len(inp)
            if n > 14:  # 12 max bytes plus 2 dots
                inp = inp[:6] + '..' + inp[-6:]
            inputs.append((prefix, inp, n))

        if log.isEnabledFor(DEBUG):
            log.debug('Inputs: ')
            for prefix, inp, sz in inputs:
                log.debug(' "%s" %s (%i bytes)' % (prefix, inp, sz))
        else:
            inputs = [inp for _, inp, sz in inputs]
            log.chat('Inputs: %s', pprint.pformat(inputs, width=50))

        opts = pprint.pformat(self.options.as_dict(), width=50)
        log.chat('Options: %s', opts)

        if len(self.expected.regexs) != len(self.expected.charnos):
            log.warn(
                'Inconsistent regexs: %i regexs versus %i char-numbers',
                len(self.expected.regexs), len(self.expected.charnos)
            )

        tmp = []
        tmp.append("Regexs:")
        for p, r in zip(self.expected.charnos, self.expected.regexs):
            tmp.append("% 4i: %s" % (p, repr(r)))

        log.debug('\n'.join(tmp), extra={'no_marker': True})
