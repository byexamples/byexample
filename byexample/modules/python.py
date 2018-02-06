"""
Example:
  >>> def hello():
  ...     print("hello bla world")

  >>> hello()
  hello<...>world

  ```python
  
  j = 2
  for i in range(4):
      j += i
  
  j + 3
  
  out:
  11
  ```

"""

import re, pexpect, sys, time
from byexample.common import log, build_exception_msg
from byexample.parser import ExampleParser
from byexample.finder import MatchFinder
from byexample.interpreter import Interpreter, PexepctMixin

class PythonPromptFinder(MatchFinder):
    target = 'python-prompt'

    def example_regex(self):
        return re.compile(r'''
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
            ''', re.MULTILINE | re.VERBOSE)

    def get_language_of(self, *args, **kargs):
        return 'python'

class PythonParser(ExampleParser):
    language = 'python'

    def example_options_string_regex(self):
        # anything of the form:
        #   #  byexample:  +FOO -BAR +ZAZ=42
        if self.compatibility_mode:
            keyword = r'(?:doctest|byexample)'
        else:
            keyword = r'byexample'

        return re.compile(r'#\s*%s:\s*([^\n\'"]*)$' % keyword,
                                                    re.MULTILINE)

    def extend_option_parser(self, parser):
        '''
        Add a few extra options and if self.compatibility_mode is True,
        add all the Python doctest's options.
        '''
        parser.add_flag("py-doctest", help="enable the compatibility with doctest.")
        parser.add_flag("py-pretty-print", help="enable the pretty print enhancement.")

        if self.compatibility_mode:
            parser.add_flag("NORMALIZE_WHITESPACE", help="[doctest] alias for +norm-ws.")
            parser.add_flag("SKIP", help="[doctest] alias for +skip.")
            parser.add_flag("ELLIPSIS", help="[doctest] enables the ... capture.")
            parser.add_flag("DONT_ACCEPT_BLANKLINE", help="[doctest] take <blankline> as literal.")
            parser.add_flag("DONT_ACCEPT_TRUE_FOR_1", help="[doctest] ignored.")
            parser.add_flag("IGNORE_EXCEPTION_DETAIL", help="[doctest] ignored.")

        return parser

    def _map_doctest_opts_to_byexample_opts(self):
        '''
        In compatibility mode, take all the Python doctest's options and flags
        and map them to a byexample option if possible.
        Otherwise log a message.

        Also, in compatibility mode, disable any "capture" unless the ELLIPSIS
        flag is present.

        Return a dictionary with the mapped flags; self.options is unchanged.
        '''
        options = self.options
        options.mask_default(False)
        mapped = {}
        if options['py_doctest']:
            # map the following doctest's options to byexample's ones
            if options['NORMALIZE_WHITESPACE']:
                mapped['norm_ws'] = True

            if options['SKIP']:
                mapped['skip'] = True

            if options['ELLIPSIS']:
                # enable the capture if ELLIPSIS but see also expected_from_match
                # as this byexample's option is not equivalent to doctest's one
                mapped['capture'] = True

            # the following are not supported: ignore them and print a note
            # somewhere
            if options['DONT_ACCEPT_TRUE_FOR_1']:
                log(build_exception_msg("[Note] DONT_ACCEPT_TRUE_FOR_1 flag is not supported.", where, self),
                        self.verbosity-2)

            if options['IGNORE_EXCEPTION_DETAIL']:
                log(build_exception_msg("[Note] IGNORE_EXCEPTION_DETAIL flag is not supported.", where, self),
                        self.verbosity-2)

        # in compatibility mode, do not capture by default [force this]
        if self.options['py_doctest'] and 'capture' not in mapped:
            mapped['capture'] = False

        options.unmask_default()
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

        if self.options.get('py_doctest', False):
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
        return self._double_parse(ExampleParser.extract_cmdline_options,
                                    args=(self, opts_from_cmdline),
                                    kwargs={})


    def extract_options(self, snippet, where):
        return self._double_parse(ExampleParser.extract_options,
                                    args=(self, snippet, where),
                                    kwargs={})

    def expected_from_match(self, match):
        expected_str = ExampleParser.expected_from_match(self, match)

        options = self.options
        options.mask_default(False)
        if options['py_doctest']:
            if not options['DONT_ACCEPT_BLANKLINE']:
                expected_str = re.sub(r'^<blankline>$', '', expected_str,
                                        flags=re.MULTILINE|re.DOTALL)

            if options['ELLIPSIS']:
                if self.capture_tag_regex().search(expected_str):
                    log(build_exception_msg("[Warn] The expected strings has <label> strings that will not be considered literal but as capture tags.", where, self),
                            self.verbosity)

                ellipsis_tag = '<%s>' % self.ellipsis_marker()
                expected_str = expected_str.replace('...', ellipsis_tag)

        options.unmask_default()
        return expected_str

    def source_from_snippet(self, snippet):
        lines = snippet.split("\n")
        if lines and lines[0].startswith(">>> "):
            return '\n'.join(line[4:] for line in lines)

        return snippet

class PythonInterpreter(Interpreter, PexepctMixin):
    language = 'python'

    def __init__(self, verbosity, encoding, **unused):
        self.encoding = encoding

        self._PS1 = r'/byexample/py/ps1> '
        self._PS2 = r'/byexample/py/ps2> '

        PexepctMixin.__init__(self,
                                cmd=None, # patchme later
                                PS1_re = self._PS1,
                                any_PS_re = r'/byexample/py/ps\d> ')

    def _get_cmd(self, pretty_print):
        change_prompts = r'''
import sys
import pprint as _byexample_pprint

# change the prompts
sys.ps1="%s"
sys.ps2="%s"

# patch the pprint _safe_repr function
def patch_pprint_safe_repr():
    import re
    ub_marker_re = re.compile(r"^[uUbB]([rR]?[" + "\\" + chr(39) + r"\"])", re.UNICODE)
    orig_repr = _byexample_pprint._safe_repr
    def patched_repr(object, *args, **kargs):
        orepr, readable, recursive = orig_repr(object, *args, **kargs)

        _repr = ub_marker_re.sub(r"\1", orepr)
        readable = False if _repr != orepr else readable

        return _repr, readable, recursive
    _byexample_pprint._safe_repr = patched_repr

if %s:
    patch_pprint_safe_repr() # patch!

    # change the displayhook to use pprint instead of repr
    sys.displayhook = lambda s: (
                    None if s is None
                    else _byexample_pprint.PrettyPrinter(indent=1, width=80, depth=None).pprint(s))

# remove introduced symbols
del sys
del patch_pprint_safe_repr
''' % (self._PS1, self._PS2, pretty_print)

        return "/usr/bin/env python -i -c '%s'" % change_prompts

    def run(self, example, flags):
        return self._exec_and_wait(example.source,
                                    timeout=int(flags['timeout']))

    def interact(self, example, options):
        PexepctMixin.interact(self)

    def initialize(self, examples, options):
        py_doctest = options.get('py_doctest', False)
        py_pretty_print = options.get('py_pretty_print', False)
        pretty_print = (py_doctest and py_pretty_print) \
                        or not py_doctest

        # set the final command
        self.cmd = self._get_cmd(pretty_print)

        # run!
        self._spawn_interpreter()

    def shutdown(self):
        self._shutdown_interpreter()
