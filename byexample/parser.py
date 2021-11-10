from __future__ import unicode_literals
import shlex, argparse, bisect, collections
from . import regex as re
from .common import tohuman, constant
from .options import OptionParser, UnrecognizedOption, ExtendOptionParserMixin
from .expected import _LinearExpected, _RegexExpected
from .parser_sm import SM_NormWS, SM_NotNormWS
from .prof import profile, profile_ctx
'''
>>> from byexample.log import init_log_system
>>> init_log_system()
'''


def tag_name_as_regex_name(name):
    return name.replace('-', '_')


TagRegexs = collections.namedtuple('TagRegexs', ['for_split', 'for_capture'])
InputRegexs = collections.namedtuple(
    'InputRegexs', ['for_check', 'for_capture']
)


class ExampleParser(ExtendOptionParserMixin):
    flavors = set()

    def __init__(self, verbosity, encoding, options, **unused):
        ExtendOptionParserMixin.__init__(self)
        self.verbosity = verbosity
        self.encoding = encoding
        self.options = options

        self._optparser_extended_cache = None
        self._opts_cache = {}

    def __repr__(self):
        return '%s Parser' % tohuman(self.language if self.language else self)

    def example_options_string_regex(self):
        r'''
        Return a regular expressions to extract a string that contains all
        the options of the example.

        This regex will be used once per example and it must have an
        unnamed group.

        Example:
          #  byexample: bla bla
          /* byexample: bla bla
          # ~byexample~ bla bla

        '''
        raise NotImplementedError()  # pragma: no cover

    def example_options_as_list(self, string):
        r'''
        Return a list of tokens from the string that was captured by
        the regex of example_options_string_regex.

        For example:
         '-foo a +bar "1 2 3"' should yield [-foo, a, +bar, "1 2 3"]
        '''
        return shlex.split(string)

    def extend_option_parser(self, parser):
        r'''
        See options.ExtendOptionParserMixin.

        By default do not add any new flag.
        '''
        return parser

    @constant
    def tag_regexs(self):
        r'''
        Return a set of regular expressions to match a 'capture tag'
        (<foo>) and a 'non-capturing tag' (<...>), known as named
        and unnamed tags too.

        Due implementation details the underscore character '_'
        *cannot* be used as a valid character in the name.
        Instead you should use minus '-'.

        The returned regex can be used for splitting a string
        or for capturing the name or the ellipsis.
        '''
        open, close = map(re.escape, '<>')

        name_re = r'[A-Za-z.][A-Za-z0-9:.-]*'
        return TagRegexs(
            for_split=re.compile(r"(%s%s%s)" % (open, name_re, close)),
            for_capture=re.compile(
                r"%s(?P<name>%s)%s" % (open, name_re, close)
            )
        )

    @constant
    def non_capturing_tag_regexs(self):
        r'''
        Return a set of regular expressions to match a
        'non-capturing tag' (<...>), known as unnamed tags.

        In contrast with tag_regexs() method, this one ignores
        the capture tags (named tags).

        The returned regex can be used for splitting a string
        or for capturing the name or the ellipsis.
        '''
        open, close = map(re.escape, '<>')

        name_re = re.escape(self.ellipsis_marker())
        return TagRegexs(
            for_split=re.compile(r"(%s%s%s)" % (open, name_re, close)),
            for_capture=re.compile(
                r"%s(?P<name>%s)%s" % (open, name_re, close)
            )
        )

    @constant
    def input_regexs(self):
        open, close = map(re.escape, '[]')
        input_re = r'''
            %s          # open marker
            (?P<input>
            [^%s\\]*    # neither a close marker or a slash
            (?:\\.[^%s\\]*)*    # a "escaped" char followed by
                                # 0 or more "neither a close marker or a slash"
            )
            %s          # a close marker
            ''' % (open, close, close, close)

        input_re_at_end = r'''
            %s          # the input regex
            (?P<trailing>
                [ ]*$   # followed by some optional space and a end of line
            )
            ''' % (input_re)

        return InputRegexs(
            for_check=re.compile(input_re, re.VERBOSE | re.MULTILINE),
            for_capture=re.compile(input_re_at_end, re.VERBOSE | re.MULTILINE)
        )

    def ellipsis_marker(self):
        return '...'

    def process_snippet_and_expected(self, snippet, expected):
        r'''
        Process the snippet code and the expected output.

        Take this opportunity to do any processing after the parsing of
        the example (in particular, after the extraction of the options)

        By default, the snippet will end with a new line: most of the
        runners use this to flush and execute the code.
        '''

        if not expected:
            expected = ''  # make sure that it is an empty string

        if not snippet.endswith('\n'):
            snippet += '\n'  # make sure that we end the code with a newline
            # most of the runners use this to flush and
            # execute the code

        return snippet, expected

    @profile
    def parse(self, example, concerns):
        options = self.options

        with profile_ctx("extract_options"):
            local_options = self.extract_options(example.snippet)

        options.up(local_options)

        with profile_ctx("process_snippet_and_expected"):
            example.source, example.expected_str = self.process_snippet_and_expected(
                example.snippet, example.expected_str
            )

        # the options to customize this example
        example.options = local_options

        if concerns:
            concerns.before_build_regex(example, options)

        for x in options['rm']:
            example.expected_str = example.expected_str.replace(x, '')

        input_prefix_len_range = options['input_prefix_range']
        expected_regexs, charnos, rcounts, tags_by_idx, input_list = self.expected_as_regexs(
            example.expected_str, options['tags'], options['capture'],
            options['type'], options['norm_ws'], input_prefix_len_range
        )

        ExpectedClass = _LinearExpected

        expected = ExpectedClass(
            # the output expected
            expected_str=example.expected_str,

            # expected regex version
            regexs=list(expected_regexs),

            # where each regex comes from
            charnos=list(charnos),

            # the 'real count' of literals
            rcounts=list(rcounts),

            # all the regexs that are not literal (tags) indexed
            # by their position in the regex list.
            # we don't save the regex (use 'regexs' for that),
            # instead save the name of the tag or None if it's
            # unnamed
            tags_by_idx=tags_by_idx,
        )

        # the source code to execute and the expected
        example.expected = expected

        # the things that we need to type when we run the example
        example.input_list = input_list

        options.down()
        return example

    @profile
    def expected_as_regexs(
        self, expected, tags_enabled, capture_enabled, input_enabled,
        normalize_whitespace, input_prefix_len_range
    ):
        r'''
        From the expected string create a list of regular expressions that
        joined with the flags re.MULTILINE | re.DOTALL, matches
        that string.

        This method returns four things:
            - a list of regexs: for literals, captures, wildcards, ...
            - a list with the character numbers, the positions in the expected
              string from where it was created each regex
            - a list of rcounts (see below)
            - a dict of non-literal 'regexs' names (capturing and non-capturing)
              also know as "tags" indexed by position.
              For non-capturing the name will be None.
            - a list of (<prefix>, <input>) tuples that describe, in order, the
              text to type (input) and the text to wait for before the
              typing (prefix)

            >>> from byexample.parser import ExampleParser
            >>> from functools import partial
            >>> import byexample.regex as re

            >>> parser = ExampleParser(0, 'utf8', None); parser.language = 'python'
            >>> _as_regexs = partial(parser.expected_as_regexs, tags_enabled=True, capture_enabled=True, input_enabled=True, normalize_whitespace=False, input_prefix_len_range=(6,12))

            >>> expected = 'a<foo>b<bar>c'
            >>> regexs, charnos, rcounts, tags_by_idx, input_list = _as_regexs(expected)

        We return the regexs

            >>> regexs
            ('\\A', 'a', '(?P<foo>.*?)', 'b', '(?P<bar>.*?)', 'c', '\\n*\\Z')

            >>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
            >>> m.match('axxbyyyc').groups()
            ('xx', 'yyy')

        And we can see the charnos or the position in the original expected
        string from where each regex was built

            >>> charnos
            (0, 0, 1, 6, 7, 12, 13)

            >>> len(expected) == charnos[-1]
            True

        And the rcount of each regex. A rcount or 'real count' count how many
        literals are. See _as_safe_regexs for more information about this but
        in a nutshell, rcount == len(line) if normalize_whitespace is False;
        if not, it is the len(line) but counting the secuence of whitespaces as
        +1.

        And we can see the positions of the tags in the regex list
        of all the non-literal regexs or "tags". The value of each
        item is the name of tag or None if it is unnamed

            >>> tags_by_idx
            {2: 'foo', 4: 'bar'}

        The following example shows what happen when we use a non-capturing tag
        (ellipsis tag) also known as unnamed tag and what happen when we use
        a tag name with a - (Python regexs don't support this character) and
        we enable the normalization of the whitespace:

            >>> expected = 'a<...> <foo-bar>c'
            >>> regexs, _, _, tags_by_idx, _ = _as_regexs(expected, normalize_whitespace=True)

            >>> regexs          # byexample: +norm-ws
            ('\\A', 'a', '(?:.*?)(?<!\\s)', '\\s+(?!\\s)', '(?P<foo_bar>.*?)', 'c', '\\s*\\Z')

            >>> tags_by_idx
            {2: None, 4: 'foo-bar'}

        When capture_enabled is False but tags_enabled is True, the capture tags
        (the ones that have a name) are considered literals but
        the non-capturing tags (the ellipsis) will still be tags.

            >>> _as_regexs = partial(parser.expected_as_regexs, tags_enabled=True, capture_enabled=False, input_enabled=True, normalize_whitespace=False, input_prefix_len_range=(6,12))

            >>> expected = 'a<foo>b<bar>c'
            >>> regexs, _, _, tags_by_idx, _ = _as_regexs(expected)

            >>> regexs
            ('\\A', 'a<foo>b<bar>c', '\\n*\\Z')

            >>> tags_by_idx
            {}

            >>> expected = 'a<...>b<bar>c'
            >>> regexs, _, _, tags_by_idx, _ = _as_regexs(expected)

            >>> regexs
            ('\\A', 'a', '(?:.*?)', 'b<bar>c', '\\n*\\Z')

            >>> tags_by_idx
            {2: None}

        '''
        if capture_enabled:
            tag_regexs = self.tag_regexs()
        else:
            tag_regexs = self.non_capturing_tag_regexs()

        if normalize_whitespace:
            sm = SM_NormWS(
                tag_regexs, self.input_regexs(), self.ellipsis_marker(),
                input_prefix_len_range
            )
        else:
            sm = SM_NotNormWS(
                tag_regexs, self.input_regexs(), self.ellipsis_marker(),
                input_prefix_len_range
            )

        return sm.parse(expected, tags_enabled, input_enabled)

    @profile
    def extract_cmdline_options(self, opts_from_cmdline):
        # now we can re-parse this argument 'options' from the command line
        # this will enable the user to set some options for a specific language
        #
        # we parse this non-strictly because the 'options' string from the
        # command line may contain language-specific options for other
        # languages than this parser (self) is targeting.
        optparser = self.options['optparser']
        optparser_extended = self.get_extended_option_parser(optparser)
        return optparser_extended.parse(opts_from_cmdline, strict=False)

    @profile
    def extract_options(self, snippet):
        optstring_match = self.example_options_string_regex().search(snippet)

        if not optstring_match:
            optlist = []

        else:
            optlist = self.example_options_as_list(optstring_match.group(1))

        if not isinstance(optlist, list):
            raise ValueError(
                "The option list returned by the parser is not a list!. This probably means that there is a bug in the parser %s."
                % str(self)
            )

        return self._extend_parser_and_parse_options_strictly_and_cache(
            optlist
        )

    def _extend_parser_and_parse_options_strictly(self, optlist):
        # we parse the example's options
        # in this case, at difference with extract_cmdline_options,
        # we parse it strictly because the example's options
        # must contain options standard of byexample and/or standard of this
        # parser (self)
        # any other options is an error
        optparser = self.options['optparser']
        optparser_extended = self.get_extended_option_parser(optparser)
        try:
            opts = optparser_extended.parse(optlist, strict=True)
        except UnrecognizedOption as e:
            raise ValueError(str(e))

        return opts

    def _extend_parser_and_parse_options_strictly_and_cache(self, optlist):
        r'''
            This is a thin wrapper around _extend_parser_and_parse_options_strictly
            to cache its results based on the optlist.

            Note that two different lists may represent the same options set
            like:
                l1 = [-foo, a, +bar, "1 2 3"]   => -foo=1 and +bar="1 2 3"
                l2 = [+bar, "1 2 3", -foo, a]   => -foo=1 and +bar="1 2 3"

            This cache system is very naive and will save two entries for
            those.

            And it works under the assumption that if a given example's options
            were parsed by X extended parser, the *same* options of another
            example *would* be parsed by the same *X parser* and it *would*
            yield the *same* result.

            If the parser object or its behaviour changes in runtime, you
            will need to override this method and change or disable the cache.
            '''
        try:
            return self._opts_cache[tuple(optlist)]
        except KeyError:
            val = self._extend_parser_and_parse_options_strictly(optlist)
            self._opts_cache[tuple(optlist)] = val
            return val


# Extra tests
r'''
>>> _as_regexs = partial(parser.expected_as_regexs, tags_enabled=True, capture_enabled=True, input_enabled=True, normalize_whitespace=False, input_prefix_len_range=(6,12))

>>> expected = 'ex <...>\nu<...>'
>>> regexs, _, _, _, _ = _as_regexs(expected, normalize_whitespace=True)

>>> regexs
('\\A',
 'ex',
 '\\s',
 '(?:\\s*(?!\\s)(?:.+)(?<!\\s))?',
 '\\s+(?!\\s)',
 'u',
 '(?:.*)(?<!\\s)',
 '\\s*\\Z')

>>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
>>> m.match('ex  x\n  u  \n').groups()
()

>>> expected = 'ex <foo>\nu<bar>'
>>> regexs, _, _, _, _ = _as_regexs(expected, normalize_whitespace=True)

>>> regexs
('\\A',
 'ex',
 '\\s',
 '(?:\\s*(?!\\s)(?P<foo>.+?)(?<!\\s))?',
 '\\s+(?!\\s)',
 'u',
 '(?P<bar>.*?)(?<!\\s)',
 '\\s*\\Z')

>>> m = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
>>> m.match('ex  x\n  u  \n').groups()
('x', '')

'''
