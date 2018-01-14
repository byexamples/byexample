import collections, re
from .common import log, build_exception_msg, tohuman

Example = collections.namedtuple('Example', ['interpreter',
                                             'filepath',
                                             'start_lineno', 'end_lineno',
                                             'options', 'indentation',
                                             'source',
                                             'expected', 'expected_regexs',
                                             'captures', 'match'])

class ExampleParser(object):
    def __init__(self, verbosity, encoding, **unused):
        self.verbosity = verbosity
        self.encoding = encoding

    def __repr__(self):
        return '%s Parser' % tohuman(self.language)

    def example_options_string_regex(self):
        '''
        Return a regular expressions to extract a string that contains all
        the options of the example.

        This regex will be used once per example and it must have an
        unnamed group.

        Example:
          #  byexample: bla bla
          /* byexample: bla bla
          # ~byexample~ bla bla

        '''
        raise NotImplementedError() # pragma: no cover

    def example_option_regex(self):
        '''
        Return a regular expressions to extract the options from the
        string returned by 'example_options_string_regex' method.

        This regex will be used several times to extract all the
        options from the string.

        It must have two exclusive groups:
         - add: if non empty, the option is meant to be enabled
         - del: if non empty, the option is meant to be disabled
        and an additional mandatory group:
         - name: the name of the option

        An optional group 'val' can be set which matching string will be
        the value of the option, true/false otherwise if the add/del are
        present.
         - val: if non empty, this is the value of the option

        Examples:
          +WS           'add' the 'WS' option
          -CAPTURE      'remove' the 'CAPTURE' option
          +TIMEOUT=10   'set' the 'TIMEOUT' to the 'value' of 10
        '''
        return re.compile(r'''
                (?:(?P<add>\+) | (?P<del>-))   #  + or - followed by
                (?P<name>\w+)                  # the name of the option and
                (?:=(?P<val>\w+))?             # optionally, = and its value

                ''', re.MULTILINE | re.VERBOSE)

    def capture_tag_regex(self):
        '''
        Return a regular expression to match a 'capture tag'.
        The regex must have a named group:
          - name: the name of the tag.
        '''
        return re.compile(r"<(?P<name>(?:\w|-|\.)+)>")

    def whitespace_non_compiled_regex(self):
        return r'\s+'

    def ellipsis_marker(self):
        return '...'

    def source_from_snippet(self, snippet):
        '''
        Remove the prompts from the snippet and any other thing that
        should not be sent to the interpreter.
        The resulting source code must be executable.
        The given snippet is already aligned and with its indentation removed.
        '''
        raise NotImplementedError() # pragma: no cover

    def get_example_from_match(self, options, match, example_str, interpreter, where):
        start_lineno, end_lineno, filepath = where
        indent = match.group('indent')

        # update the example string and the match removin any indentation
        example_str = self.check_and_remove_ident(example_str, indent, where)
        match = self.check_keep_matching(example_str, match, where)

        snippet  = match.group("snippet")
        expected = match.group("expected")

        if not expected:
            expected = ''   # make sure that it is a string

        options.up(self.extract_options(snippet, where))

        norm_ws = options.get('WS', False)

        if norm_ws:
            expected_norm = self.normalize_whitespace(expected)
        else:
            expected_norm = expected

        expected_regexs, captures = self.expected_as_regexs(
                                            expected_norm,
                                            norm_ws,
                                            options.get('CAPTURE', True),
                                            where)

        source = self.source_from_snippet(snippet)
        if not source.endswith('\n'):
            source += '\n'

        example = Example(
                          # the source code to execute and the output
                          # expected.
                          source=source, expected=expected,

                          # expected regex version
                          expected_regexs=expected_regexs,

                          # the names of the capture tags in the expected regex
                          captures=captures,

                          # the options to customize this example
                          options=options.copy(),

                          # full match of this example (without indentation)
                          match=match,

                          # the original indentation of the example
                          indentation=indent,

                          # file from where this example was extracted
                          filepath=filepath,

                          # start / end line numbers (inclusive) in the file
                          start_lineno=start_lineno, end_lineno=end_lineno,

                          # the interpreter for this example
                          interpreter=interpreter)

        options.down()
        return example

    def check_and_remove_ident(self, example_str, indent, where):
        r'''
        Given an example string, remove its indent, including a possible empty
        line at the end.
            >>> from byexample.parser import ExampleParser
            >>> parser = ExampleParser(0, 'utf8'); parser.language = 'python'
            >>> check_and_remove_ident = parser.check_and_remove_ident
            >>> check_and_remove_ident('  >>> 1 + 2\n  3\n ', '  ', (1, 2, 'foo.rst'))
            '>>> 1 + 2\n3'

        If the string contains a line with a lower level of indentation,
        raise an exception.

            >>> check_and_remove_ident('  >>> 1 + 2\n3\n', '  ', (1, 2, 'foo.rst'))
            Traceback (most recent call last):
            <...>
            ValueError: <...>

        '''
        start_lineno, _, filepath = where

        lines = example_str.split('\n')

        if not lines[-1].strip():
            lines = lines[:-1]  # remove last whitespace-only line

        indent_stripped = []
        for lineno, line in enumerate(lines):
            if not line.startswith(indent):
                msg = 'The line %i is misaligned (wrong indentation). ' +\
                      'Expected at least %i spaces.\nOffending line:\n%s\n'

                msg = msg % (start_lineno + lineno, len(indent), line)
                raise ValueError(build_exception_msg(msg, where, self))

            indent_stripped.append(line[len(indent):])

        return '\n'.join(indent_stripped)

    def check_keep_matching(self, example_str, match, where):
        r'''
        Given an example string, try to apply the match again.
        This is a health-check intended to be used after a call to
        'check_and_remove_ident'

            >>> from byexample.parser import ExampleParser
            >>> import re

            >>> parser = ExampleParser(0, 'utf8'); parser.language = 'python'
            >>> check_and_remove_ident = parser.check_and_remove_ident
            >>> check_keep_matching    = parser.check_keep_matching

            >>> code = '  >>> 1 + 2'
            >>> match = re.match(r'[ ]*>>> [^\n]*', code)

            >>> code_i = check_and_remove_ident(code, '  ', (1, 2, 'foo.rst'))
            >>> code_i != code
            True
            >>> new_match = check_keep_matching(code_i, match, (1, 2, 'foo.rst'))

        This should not happen but if for some reason the regex doesn't match
        the full string, raise an exception:

            >>> x_code = 'x' + code_i
            >>> check_keep_matching(x_code, match, (1, 2, 'foo.rst'))
            Traceback (most recent call last):
            <...>
            ValueError: <...>

            >>> code_x = code_i + '\nx'
            >>> check_keep_matching(code_x, match, (1, 2, 'foo.rst'))
            Traceback (most recent call last):
            <...>
            ValueError: <...>

        '''
        start_lineno, _, filepath = where

        new_match = match.re.match(example_str)
        if not new_match:
            msg = 'The regex does not match the example after ' +\
                  'removing the indentation. '

            raise ValueError(build_exception_msg(msg, where, self))

        if new_match.start() != 0 or new_match.end() != len(example_str):
            msg = '%i bytes were left out after removing the indentation. ' +\
                  'Dropped bytes at the %s of example:\n%s\n'

            if new_match.start() != 0:
                dropped = example_str[:new_match.start()]
                at = 'begin'
            else:
                dropped = example_str[new_match.end():]
                at = 'end'

            msg = msg % (len(dropped), at, dropped)
            raise ValueError(build_exception_msg(msg, where, self))

        return new_match

    def normalize_whitespace(self, expected):
        ws_re = self.whitespace_non_compiled_regex()
        return ' '.join(re.split(ws_re, expected))

    def expected_as_regexs(self, expected, normalize_whitespace, capture, where):
        r'''
        From the expected string create a list fo regular expressions that
        joined and with the flags (re.MULTILINE | re.DOTALL) matches
        that string performing the following additional modifications:
         - if normalize_whitespace is true, replace all the consecutive
           whitespaces (except new lines) by a single regular expression that
           matched any amount of whitespaces. The net effect is that regardless of
           the spaces in expected, the regexp will match one ore more.

            >>> from byexample.parser import ExampleParser
            >>> parser = ExampleParser(0, 'utf8'); parser.language = 'python'
            >>> expected_as_regexs = parser.expected_as_regexs

            >>> m, _ = expected_as_regexs('a     b  \t\vc', True, True, (1, 2, 'foo.rst'))
            >>> m = re.compile(''.join(m), re.MULTILINE | re.DOTALL)
            >>> m.match('a b c') is not None
            True

         - if capture is true, replace the literals capture tags by regexs.

            >>> m, _ = expected_as_regexs('a<foo>b<bar>c', False, True, (1, 2, 'foo.rst'))
            >>> m = re.compile(''.join(m), re.MULTILINE | re.DOTALL)
            >>> m.match('axxbyyyc').groups()
            ('xx', 'yyy')

           But if two or more capture tags are consecutive, raise an exception
           as this is ambiguous:

            >>> # but here? foo is 'x' and bar 'xyyy'?, '' and 'xxyyy', or ....
            >>> expected_as_regexs('a<foo><bar>c', False, True, (1, 2, 'foo.rst'))
            Traceback (most recent call last):
            <...>
            ValueError: <...>

         - if the capture flag is False, all the <...> tags are taken literally.

            >>> m, _ = expected_as_regexs('a<foo>b<bar>c', False, False, (1, 2, 'foo.rst'))
            >>> m = re.compile(''.join(m), re.MULTILINE | re.DOTALL)
            >>> m.match('axxbyyyc') is None # don't matched as <foo> is not xx
            True

            >>> m.match('a<foo>b<bar>c') is None # the strings <foo> <bar> are literals
            False

        '''
        start_lineno, _, filepath = where

        charno = 0
        regexs = []
        names_seen = set()

        regexs.append(r"\A") # the begin of the string

        if capture:
            for match in self.capture_tag_regex().finditer(expected):
                if charno == match.start() and charno > 0:
                    msg = "Two consecutive capture tags were found. " +\
                          "This is ambiguous."
                    raise ValueError(build_exception_msg(msg, where, self))

                self._add_as_regex(expected[charno:match.start()], regexs, normalize_whitespace)

                name = match.group("name")
                name = name.replace("-", "_") # uniform the name

                if name == self.ellipsis_marker():
                    # capture anything (non-greedy)
                    regex = r"(.*?)"

                else:
                    if name in names_seen:
                        # matched the same string that a previous
                        # group matched with that name
                        regex = r"(?P=%s)" % name
                    else:
                        # first seen, capture anything (non-greedy)
                        regex = r"(?P<%s>.*?)" % name
                        names_seen.add(name)

                regexs.append(regex)
                charno = match.end()

        self._add_as_regex(expected[charno:], regexs, normalize_whitespace)

        regexs.append(r"\n?")
        regexs.append(r"\Z") # the end of the string

        return regexs, list(names_seen)

    def _add_as_regex(self, literals, regexs, normalize_whitespace):
        ws_re = self.whitespace_non_compiled_regex()

        # Split the literal string into lines.
        # The human tends to write in a line-oriented way and it easier
        # from him/her to spot differences in a line instead
        # of searching the difference in a multiline output.
        # This also is how the different diff algorithms are designed.
        escaped_lines = []
        for line in literals.split('\n'):
            if normalize_whitespace:
                # now split the line by whitespaces (aka words)
                # escape each word and rejoin them witha whitespace regex
                non_ws = re.split(ws_re, line)
                non_ws_escaped = [re.escape(n) for n in non_ws]

                escaped_lines.append(ws_re.join(non_ws_escaped))
            else:
                escaped_lines.append(re.escape(line))

        # add the escaped lines to the regexs list
        regexs.append(escaped_lines[0])
        for el in escaped_lines[1:]:
            if normalize_whitespace:
                # add a whitespace regex in replace of the literal \n
                regexs.append(ws_re)
            else:
                # add the literal \n
                regexs.append(re.escape('\n'))

            regexs.append(el)


    def extract_options(self, snippet, where):
        start_lineno, _, filepath = where
        optstring_re = self.example_options_string_regex()
        opt_re = self.example_option_regex()

        match = optstring_re.search(snippet)
        if not match:
            return {}

        optstring = match.group(1)

        options = {}
        for match in opt_re.finditer(optstring):
            name = match.group("name")

            add  = match.group("add")
            del_ = match.group("del")

            if (add and del_) or (not add and not del_):
                msg = "Ambiguous option: do you expected to add or delete it? " +\
                      "Offending example at line %i in %s: %s"
                msg = msg % (start_lineno, filepath, match.group(0))
                raise ValueError(build_exception_msg(msg, where, self))

            if add:
                val  = match.group("val")
                options[name] = val if val else True
            else:
                options[name] = False    # del

        return options

