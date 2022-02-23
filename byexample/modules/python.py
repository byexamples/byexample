"""
Example:
  >>> def hello():
  ...     print("hello bla world")

  >>> hello()               # byexample: +norm-ws
  hello   <...>   world

  >>> j = 2
  >>> for i in range(4):
  ...    j += i

  >>> j + 3
  11

  >>> print('''this
  ... is a multiline
  ... string''')
  this
  is a multiline
  string

  >>> input("num: ")   # byexample: +type
  num: [42]
  '42'

  >>> input()   # byexample: +type
  [it works!]
  'it works!'
"""

from __future__ import unicode_literals
import pexpect, sys, time
import byexample.regex as re
from byexample.common import constant
from byexample.log import clog
from byexample.parser import ExampleParser, ExtendOptionParserMixin
from byexample.finder import ExampleFinder
from byexample.runner import ExampleRunner, PexpectMixin, ShebangTemplate

stability = 'stable'


class PythonPromptFinder(ExampleFinder):
    target = 'python-prompt'

    @constant
    def example_regex(self):
        return re.compile(
            r'''
            # Snippet consists of a PS1 line >>>
            # followed by zero or more PS2 lines.
            (?P<snippet>
                (?:^(?P<indent> [ ]*) >>>[ ]     .*)    # PS1 line
                (?:\n           [ ]*  \.\.\.   .*)*)    # PS2 lines
            \n?
            # The expected output consists of any non-blank lines
            # that do not start with PS1
            (?P<expected> (?:(?![ ]*$)     # Not a blank line
                          (?![ ]*>>>)      # Not a line starting with PS1
                         .+$\n?            # But any other line
                      )*)
            ''', re.MULTILINE | re.VERBOSE
        )

    def get_language_of(self, *args, **kargs):
        return 'python'

    def get_snippet_and_expected(self, match, where):
        snippet, expected = ExampleFinder.get_snippet_and_expected(
            self, match, where
        )

        snippet = self._remove_prompts(snippet)
        return snippet, expected

    def _remove_prompts(self, snippet):
        lines = snippet.split("\n")

        # all the lines starts with a prompt
        ok = all(l.startswith(">>>") or l.startswith("...") for l in lines)
        if not ok:
            raise ValueError("Incorrect prompts")

        # a space follows a prompt except when the line is just a prompt
        ok = all(l[3] == ' ' for l in lines if len(l) >= 4)
        if not ok:
            raise ValueError("Missing space after the prompt")

        # remove the prompts
        lines = (l[4:] for l in lines)

        return '\n'.join(lines)


###############################################################################
# : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : #
###############################################################################
#
# The following is an extract of the doctest.py module from Python 2.7.
#
# I copied some parts verbatim as they are as private members of the doctest
# module.
# The code was released to the public domain by Tim Peters.
#
# I don't claim any right over this copied piece of code, it is copied
# for convenience
#
# I copied the license too for the records.

# Module doctest.
# Released to the public domain 16-Jan-2001, by Tim Peters (tim@python.org).
# Major enhancements and refactoring by:
#     Jim Fulton
#     Edward Loper

# Provided as-is; use at your own risk; no warranty; no promises; enjoy!

# A regular expression for handling `want` strings that contain
# expected exceptions.  It divides `want` into three pieces:
#    - the traceback header line (`hdr`)
#    - the traceback stack (`stack`)
#    - the exception message (`msg`), as generated by
#      traceback.format_exception_only()
# `msg` may have multiple lines.  We assume/require that the
# exception message is the first non-indented line starting with a word
# character following the traceback header line.
_EXCEPTION_RE = re.compile(
    r"""
    # Grab the traceback header.  Different versions of Python have
    # said different things on the first traceback line.
    ^(?P<hdr> Traceback\ \(
        (?: most\ recent\ call\ last
        |   innermost\ last
        ) \) :
    )
    \s* $                # toss trailing whitespace on the header.
    (?P<stack> .*?)      # don't blink: absorb stuff until...
    ^ (?P<msg> \w+ .*)   #     a line *starts* with alphanum.
    """, re.VERBOSE | re.MULTILINE | re.DOTALL
)

#
#
# This is the end of the verbatim copy of some pieces of code from doctest.py
#
###############################################################################
# : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : : #
###############################################################################


def _example_options_string_regex_for(compatibility_mode):
    # anything of the form:
    if compatibility_mode:
        #   #  doctest:  +FOO -BAR +ZAZ=42
        # or
        #   #  byexample:  +FOO -BAR +ZAZ=42
        keyword = r'(?:doctest|byexample)'
    else:
        #   #  byexample:  +FOO -BAR +ZAZ=42
        keyword = r'byexample'

    return re.compile(r'#\s*%s:\s*([^\n\'"]*)$' % keyword, re.MULTILINE)


class PythonParser(ExampleParser):
    language = 'python'

    # make this to cache the regexs
    _blankline_tag_re = re.compile(r'^<BLANKLINE>$', re.MULTILINE | re.DOTALL)
    _opts_re_for_noncomp = _example_options_string_regex_for(False)
    _opts_re_for_comp = _example_options_string_regex_for(True)

    def __init__(self, *args, **kw):
        ExampleParser.__init__(self, *args, **kw)
        self._optparser_extended_by_comp_mode_cache = None

    def example_options_string_regex(self):
        return self._opts_re_for_comp if self.compatibility_mode \
                else self._opts_re_for_noncomp

    def extend_option_parser(self, parser):
        '''
        Add a few extra options and if self.compatibility_mode is True,
        add all the Python doctest's options.
        '''
        parser.add_flag(
            "py-doctest",
            default=False,
            help="enable the compatibility with doctest."
        )
        parser.add_flag(
            "py-pretty-print",
            default=True,
            help="enable the pretty print enhancement."
        )
        parser.add_flag(
            "py-remove-empty-lines",
            default=True,
            help="enable the deletion of empty lines (enabled by default)."
        )

        if getattr(self, 'compatibility_mode', True):
            parser.add_flag(
                "NORMALIZE_WHITESPACE",
                default=False,
                help="[doctest] alias for +norm-ws."
            )
            parser.add_flag(
                "SKIP", default=False, help="[doctest] alias for +skip."
            )
            parser.add_flag(
                "ELLIPSIS",
                default=False,
                help="[doctest] enables the ... wildcard."
            )
            parser.add_flag(
                "DONT_ACCEPT_BLANKLINE",
                default=False,
                help="[doctest] take <BLANKLINE> as literal."
            )
            parser.add_flag(
                "DONT_ACCEPT_TRUE_FOR_1",
                default=False,
                help="[doctest] ignored."
            )
            parser.add_flag(
                "IGNORE_EXCEPTION_DETAIL",
                default=False,
                help="[doctest] ignore the exception details."
            )
            parser.add_flag(
                "REPORT_UDIFF",
                default=False,
                help="[doctest] alias for +diff unified."
            )
            parser.add_flag(
                "REPORT_CDIFF",
                default=False,
                help="[doctest] alias for +diff context."
            )
            parser.add_flag(
                "REPORT_NDIFF",
                default=False,
                help="[doctest] alias for +diff ndiff."
            )
            parser.add_flag(
                "FAIL_FAST",
                default=False,
                help="[doctest] alias for +fail-fast."
            )
            parser.add_flag(
                "REPORT_ONLY_FIRST_FAILURE",
                default=False,
                help="[doctest] alias for +show-failures 1."
            )

        return parser

    def get_extended_option_parser(self, parent_parser, **kw):
        original_compatibility_mode = getattr(self, 'compatibility_mode', None)

        # compatibility mode: True if it wasn't explicitly set
        compatibility_mode = True if original_compatibility_mode == None \
                                  else original_compatibility_mode

        tmp = {}

        # fake the two compatibility mode (True and False)
        # and build an extended parser for each mode
        self.compatibility_mode = True
        tmp[self.compatibility_mode
            ] = ExtendOptionParserMixin.get_extended_option_parser(
                self, parent_parser, **kw
            )

        self.compatibility_mode = False
        tmp[self.compatibility_mode
            ] = ExtendOptionParserMixin.get_extended_option_parser(
                self, parent_parser, **kw
            )

        # restore the compatibility mode (even if it was unset)
        if original_compatibility_mode == None:
            del self.compatibility_mode
        else:
            self.compatibility_mode = original_compatibility_mode

        return tmp[compatibility_mode]

    def _map_doctest_opts_to_byexample_opts(self):
        '''
        In compatibility mode, take all the Python doctest's options and flags
        and map them to a byexample option if possible.
        Otherwise log a message.

        Also, in compatibility mode, disable any "tags" unless the ELLIPSIS
        flag is present.

        Return a dictionary with the mapped flags; self.options is unchanged.
        '''
        options = self.options
        mapped = {}
        if options['py_doctest']:
            # map the following doctest's options to byexample's ones
            if options['NORMALIZE_WHITESPACE']:
                mapped['norm_ws'] = True

            if options['SKIP']:
                mapped['skip'] = True

            if options['ELLIPSIS']:
                # enable the 'tags' if ELLIPSIS but see also expected_from_match
                # as this byexample's option is not equivalent to doctest's one
                mapped['tags'] = True

            if options['REPORT_UDIFF']:
                mapped['diff'] = 'unified'

            if options['REPORT_CDIFF']:
                mapped['diff'] = 'context'

            if options['REPORT_NDIFF']:
                mapped['diff'] = 'ndiff'

            if options['FAIL_FAST']:
                mapped['fail_fast'] = True

            if options["REPORT_ONLY_FIRST_FAILURE"]:
                mapped['show_failures'] = 1

            # the following are not supported: ignore them and print a note
            # somewhere
            if options['DONT_ACCEPT_TRUE_FOR_1']:
                clog().warn("DONT_ACCEPT_TRUE_FOR_1 flag is not supported.")

        # in compatibility mode, do not interpret <...> by default [force this]
        if self.options['py_doctest'] and 'tags' not in mapped:
            mapped['tags'] = False

        return mapped

    def _double_parse(self, parse_method, args, kwargs):
        '''
        Call parse_method at most twice.
        The first call is under compatibility mode.

        If the options parsed (in union with the options before) say that
        the compatibility mode is not ON, parse them again under
        non-compatibility mode.

        Finally, map any doctest option to a byexample option.

        Return the options parsed and mapped; self.options is unchanged.
        '''
        # let's force a compatibility mode before parsing,
        # the compatibility mode uses a parser that it is a superset of the
        # parser in non-compatibility mode so we should be safe
        self.compatibility_mode = True
        options = parse_method(*args, **kwargs)

        # temporally, merge the new options found (options) with the
        # the obtained previously (self.options)
        self.options.up(options)

        if self.options['py_doctest']:
            # okay, the user really wanted to be in compatibility mode
            pass
        else:
            # ups, the user don't want this mode, re parse the options
            # in non-compatibility mode
            self.compatibility_mode = False
            options = parse_method(*args, **kwargs)

        # take the self.options and see if there are doctest flags
        # to be mapped to byexample's options
        mapped = self._map_doctest_opts_to_byexample_opts()

        # revert the merge
        self.options.down()

        # take the original options parsed, update them with the mapped options,
        # and return them
        options.update(mapped)
        return options

    def extract_cmdline_options(self, opts_from_cmdline):
        return self._double_parse(
            ExampleParser.extract_cmdline_options,
            args=(self, opts_from_cmdline),
            kwargs={}
        )

    def extract_options(self, snippet):
        return self._double_parse(
            ExampleParser.extract_options, args=(self, snippet), kwargs={}
        )

    def process_snippet_and_expected(self, snippet, expected):
        snippet, expected = ExampleParser.process_snippet_and_expected(
            self, snippet, expected
        )

        expected = self._mutate_expected_based_on_doctest_flags(expected)
        snippet = self._remove_empty_line_if_enabled(snippet)

        return snippet, expected

    def _mutate_expected_based_on_doctest_flags(self, expected_str):
        options = self.options
        if options['py_doctest']:
            if not options['DONT_ACCEPT_BLANKLINE']:
                expected_str = self._blankline_tag_re.sub('', expected_str)

            m = _EXCEPTION_RE.match(expected_str)
            if options['ELLIPSIS'] or m:
                # we will enable the capture mode, check and warn if the example
                # contains strings like <label> that may confuse byexample and
                # or the user
                if self.tag_regexs().for_capture.search(expected_str):
                    clog().warn(
                        "The expected strings has '<label>' strings that will not be considered literal but as capture tags."
                    )

            if options['ELLIPSIS']:
                ellipsis_tag = '<%s>' % self.ellipsis_marker()
                expected_str = expected_str.replace('...', ellipsis_tag)

            # yes, again, we modified the expected_str in the step before
            m = _EXCEPTION_RE.match(expected_str)
            if m:
                # make an expected string ignoring the stack trace
                # and the traceback header like doctest does.
                ellipsis_tag = '<%s>' % self.ellipsis_marker()

                msg = m.group('msg')
                if options['IGNORE_EXCEPTION_DETAIL']:
                    # we assume, like doctest does, that the first : is at
                    # the end of the class name of the exception.
                    full_class_name = msg.split(":", 1)[0]
                    class_name = full_class_name.rsplit(".", 1)[-1]
                    msg = class_name + ":"

                expected_str = '\n'.join([
                                    # a Traceback header
                                    'Traceback ' + ellipsis_tag,

                                    # the stack trace (ignored)
                                    ellipsis_tag,

                                    # the "relaxed" exception message
                                    # in Python 2.x this starts with a class
                                    # name while in Python 3.x starts with
                                    # a full name (module dot class name)
                                    #
                                    # this breaks almost all the exception
                                    # checks in doctest so this should be a nice
                                    # improvement.
                                    ellipsis_tag + msg + \
                                        (ellipsis_tag if options['IGNORE_EXCEPTION_DETAIL'] else ""),
                                    ])

                # enable the capture, this should affect to this example only
                options['tags'] = True

        return expected_str

    def _remove_empty_line_if_enabled(self, snippet):
        if self.options['py_remove_empty_lines']:
            # remove the empty lines if they are followed by indented lines
            # if they are followed by non-indented lines, the empty lines means
            # "end the block" of code and they should not be removed or we will
            # have SyntaxError
            filtered = []
            lines = snippet.split("\n")
            for i, line in enumerate(lines[:-1]):
                if line or (not lines[i + 1].startswith(" ") and lines[i + 1]):
                    filtered.append(line)

            filtered.append(lines[-1])
            lines = filtered

            return '\n'.join(lines)
        return snippet


class PythonInterpreter(ExampleRunner, PexpectMixin):
    language = 'python'
    flavors = {'python3', 'python'}

    def __init__(self, verbosity, encoding, selected_languages, **unused):
        self.encoding = encoding

        self._PS1 = r'/byexample/py/ps1> '
        self._PS2 = r'/byexample/py/ps2> '

        supported_by_us = (self.flavors & selected_languages)
        self._python_flavor = self.language if not supported_by_us else supported_by_us.pop(
        )

        PexpectMixin.__init__(
            self, PS1_re=self._PS1, any_PS_re=r'/byexample/py/ps\d> '
        )

    def get_default_cmd(self, *args, **kargs):
        p = self._python_flavor
        return "%e %p %a", {
            'e': "/usr/bin/env",
            'p': p,
            'a': [
                "-i",  # mean interactive, even if we run a script
            ]
        }

    def get_default_version_cmd(self, *args, **kargs):
        p = self._python_flavor
        return "%e %p %a", {
            'e': "/usr/bin/env",
            'p': p,
            'a': [
                "--version",
            ]
        }

    @constant
    def get_version(self, options):
        return self._get_version(options)

    def conf_pretty_print(self, columns, options):
        # Important: do not use a single quote ' in the following python code
        # it will break it in real hard ways to debug.
        # Also, code all this without any empty line: we are sending raw input
        # to Python without processing it with PythonParser so we must be
        # careful
        change_prompts = r'''
import sys as _byexample_sys
import pprint as _byexample_pprint
if True:
    class __ByexamplePrettyPrint(_byexample_pprint.PrettyPrinter):
        def __init__(self, *args, **kargs):
            s = _byexample_pprint.PrettyPrinter
            s.__init__(self, *args, **kargs)
        def update_width(self, width):
            self._width = int(width)
    __byexample_pretty_print = __ByexamplePrettyPrint(indent=1, width=%i, depth=None)
    del __ByexamplePrettyPrint
    # change the displayhook to use pprint instead of repr
    _byexample_sys.displayhook = lambda s: (
                    None if s is None
                    else __byexample_pretty_print.pprint(s))
''' % (columns)

        self._exec_and_wait(
            change_prompts, options, timeout=options['x']['dfl_timeout']
        )

    def run(self, example, options):
        return PexpectMixin._run(self, example, options)

    def _run_impl(self, example, options):
        return self._exec_and_wait(
            example.source, options, from_example=example
        )

    def _change_terminal_geometry(self, rows, cols, options):
        # update the pretty printer with the new columns value
        source = '__byexample_pretty_print.update_width(%i)' % cols
        self._exec_and_wait(
            source, options, timeout=options['x']['dfl_timeout']
        )
        PexpectMixin._change_terminal_geometry(self, rows, cols, options)

    def interact(self, example, options):
        PexpectMixin.interact(self)

    def initialize(self, options):
        py_doctest = options['py_doctest']
        py_pretty_print = options['py_pretty_print']
        pretty_print = (py_doctest and py_pretty_print) \
                        or not py_doctest

        cmd = self.build_cmd(options, *self.get_default_cmd())

        # run!
        self._spawn_interpreter(cmd, options, initial_prompt=r'>>> ')

        # change the prompts in the first line so by the moment that we
        # wait for its completion we will be waiting for PS1 and PS2, the
        # new prompts
        self._exec_and_wait(
            r'import sys; sys.ps1="%s" ; sys.ps2="%s"; del sys' %
            (self._PS1, self._PS2),
            options,
            timeout=options['x']['dfl_timeout']
        )

        if pretty_print:
            self.conf_pretty_print(options['geometry'][1], options)

    def shutdown(self):
        self._shutdown_interpreter()

    def cancel(self, example, options):
        return self._abort(example, options)
