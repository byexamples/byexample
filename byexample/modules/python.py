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
        parser.add_flag("pydoctest", default=False)

        if self.compatibility_mode:
            parser.add_flag("NORMALIZE_WHITESPACE", default=False)
            parser.add_flag("SKIP", default=False)
            parser.add_flag("ELLIPSIS", default=False)
            parser.add_flag("DONT_ACCEPT_BLANKLINE", default=False)
            parser.add_flag("DONT_ACCEPT_TRUE_FOR_1", default=False)
            parser.add_flag("IGNORE_EXCEPTION_DETAIL", default=False)

        return parser

    def _map_doctest_opts_to_byexample_opts(self, options):
        if options['pydoctest']:
            # map the following doctest's options to byexample's ones
            if options['NORMALIZE_WHITESPACE']:
                options['norm_ws'] = True

            if options['SKIP']:
                options['skip'] = True

            # do not capture by default, force this
            options['capture'] = False
            if options['ELLIPSIS']:
                # enable it if ELLIPSIS but see also expected_from_match
                # as this byexample's option is not equivalent to doctest's one
                options['capture'] = True

            # the following are not supported: ignore them and print a note
            # somewhere
            if options['DONT_ACCEPT_TRUE_FOR_1']:
                log(build_exception_msg("[Note] DONT_ACCEPT_TRUE_FOR_1 flag is not supported.", where, self),
                        self.verbosity-2)

            if options['IGNORE_EXCEPTION_DETAIL']:
                log(build_exception_msg("[Note] IGNORE_EXCEPTION_DETAIL flag is not supported.", where, self),
                        self.verbosity-2)

        else:
            # no doctest's flags are allowed (this should never happen)
            assert all(f not in options for f in ('SKIP', 'ELLIPSIS',
                        'IGNORE_EXCEPTION_DETAIL', 'DONT_ACCEPT_TRUE_FOR_1',
                        'DONT_ACCEPT_BLANKLINE', 'NORMALIZE_WHITESPACE'))

    def _double_parse(self, parse_method, args, kwargs):
        # let's force a compatibility mode before parsing,
        # the compatibility mode uses a parser that it is a superset of the
        # parser in non-compatibility mode so we should be safe
        self.compatibility_mode = True
        options = parse_method(*args, **kwargs)

        if options['pydoctest']:
            # okay, the user really wanted to be in compatibility mode
            pass
        else:
            # ups, the user don't want this mode, re parse the options
            # in non-compatibility mode
            self.compatibility_mode = False
            options = parse_method(*args, **kwargs)

        self._map_doctest_opts_to_byexample_opts(options)
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
        if options['pydoctest']:
            if not options['DONT_ACCEPT_BLANKLINE']:
                expected_str = re.sub(r'^<blankline>$', '', expected_str,
                                        flags=re.MULTILINE|re.DOTALL)

            if options['ELLIPSIS']:
                if self.capture_tag_regex().search(expected_str):
                    log(build_exception_msg("[Warn] The expected strings has <label> strings that will not be considered literal but as capture tags.", where, self),
                            self.verbosity)

                ellipsis_tag = '<%s>' % self.ellipsis_marker()
                expected_str = expected_str.replace('...', ellipsis_tag)

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

        PS1 = r'/byexample/py/ps1> '
        PS2 = r'/byexample/py/ps2> '

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

patch_pprint_safe_repr() # patch!

# change the displayhook to use pprint instead of repr
sys.displayhook = lambda s: (
                    None if s is None
                    else _byexample_pprint.PrettyPrinter(indent=1, width=80, depth=None).pprint(s))

# remove introduced symbols
del sys
del patch_pprint_safe_repr
''' % (PS1, PS2)

        PexepctMixin.__init__(self,
                                cmd="/usr/bin/env python -i -c '%s'" % change_prompts,
                                PS1_re = PS1,
                                any_PS_re = r'/byexample/py/ps\d> ')


    def run(self, example, flags):
        return self._exec_and_wait(example.source,
                                    timeout=int(flags['timeout']))

    def interact(self, example, options):
        PexepctMixin.interact(self)

    def initialize(self, examples, options):
        self._spawn_interpreter()

    def shutdown(self):
        self._shutdown_interpreter()
