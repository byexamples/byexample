import collections, re
from .common import log, build_exception_msg

Example = collections.namedtuple('Example', ['interpreter',
                                             'filepath',
                                             'start_lineno', 'end_lineno',
                                             'options', 'indentation',
                                             'source',
                                             'expected', 'expected_re',
                                             'captures', 'match'])

def print_example(example):
    print("*" * 70)
    for i, field in enumerate(example._fields):
        if field in ('expected_re', 'match'):
            continue

        if field == 'indentation':
            print("%s: |%s| (%i bytes)" % (field, example[i],
                                            len(example[i])))
            continue

        sep = '\n' if field in ('source', 'expected') else ' '
        print("%s:%s%s" % (field, sep, example[i]))

    print('\n')

class ExampleParser(object):
    def __init__(self, verbosity, encoding):
        self.verbosity = verbosity
        self.encoding = encoding

    def example_regex(self):
        '''
        Return a regular expression to match an example with at
        least three groups:
         - indent: to capture the indentation of the example (first line)
         - snippet: the code to execute including the prompts and the indentation
         - expected: the expected output
        '''
        raise NotImplementedError() # pragma: no cover

    def example_options_regex(self):
        '''
        Return two regular expressions to match the options of an example
        if any.
        The first must extract a string, the options-string, and the
        second will extract from that string the options.

        The first regex will be used once per example. The second will be
        used several times to extract all the options from the string.

        The first regex must have an unnamed group. The second must have
        two exclusive groups:
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
        raise NotImplementedError() # pragma: no cover

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

    def get_examples_from_file(self, options, filepath, encoding):
        with open(filepath, 'rtU') as f:
            string = f.read()

        return self.get_examples_from_string(options, string, filepath)

    def get_examples_from_string(self, options, string, filepath='<string>'):
        charno = 0
        start_lineno = 1  # humans tend to count from 1
        examples = []
        for match in self.example_regex().finditer(string):
            example_str = string[match.start():match.end()]

            # start_lineno and end_lineno are inclusive
            start_lineno += string[charno:match.start()].count('\n')
            end_lineno = start_lineno + example_str.count('\n') - 1

            # update charno here
            charno = match.start()

            # where we are, used for the messages of the exceptions
            where = (start_lineno, filepath)

            indent = match.group('indent')

            # update the example string and the match removin any indentation
            example_str = self.check_and_remove_ident(example_str, indent, where)
            match = self.check_keep_matching(example_str, match, where)

            snippet   = match.group("snippet")
            expected = match.group("expected")

            options.up(self.extract_options(snippet, where))

            norm_ws = options.get('WS', False)

            if norm_ws:
                expected_norm = self.normalize_whitespace(expected)
            else:
                expected_norm = expected

            expected_re, captures = self.expected_as_regex(expected_norm, norm_ws, where)

            source = self.source_from_snippet(snippet)
            if not source.endswith('\n'):
                source += '\n'

            example = Example(
                              # the source code to execute and the output
                              # expected.
                              source=source, expected=expected,

                              # expected regex version
                              expected_re=expected_re,

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
                              interpreter=self)

            if self.verbosity >= 2:
                print_example(example)

            examples.append(example)
            options.down()

        log("File '%s': %i examples [%s]" % (filepath, len(examples), str(self)),
                                            self.verbosity-1)

        return examples

    def check_and_remove_ident(self, example_str, indent, where):
        r'''
        Given an example string, remove its indent, including a possible empty
        line at the end.
            >>> from byexample.parser import ExampleParser
            >>> check_and_remove_ident = ExampleParser(0, None).check_and_remove_ident
            >>> check_and_remove_ident('  >>> 1 + 2\n  3\n ', '  ', (1, 'foo.rst'))
            '>>> 1 + 2\n3'

        If the string contains a line with a lower level of indentation,
        raise an exception.

            >>> check_and_remove_ident('  >>> 1 + 2\n3\n', '  ', (1, 'foo.rst'))
            Traceback (most recent call last):
            <...>
            ValueError: <...>

        '''
        start_lineno, filepath = where

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

            >>> check_and_remove_ident = ExampleParser(0, None).check_and_remove_ident
            >>> check_keep_matching    = ExampleParser(0, None).check_keep_matching

            >>> code = '  >>> 1 + 2'
            >>> match = re.match(r'[ ]*>>> [^\n]*', code)

            >>> code_i = check_and_remove_ident(code, '  ', (1, 'foo.rst'))
            >>> code_i != code
            True
            >>> new_match = check_keep_matching(code_i, match, (1, 'foo.rst'))

        This should not happen but if for some reason the regex doesn't match
        the full string, raise an exception:

            >>> x_code = 'x' + code_i
            >>> check_keep_matching(x_code, match, (1, 'foo.rst'))
            Traceback (most recent call last):
            <...>
            ValueError: <...>

            >>> code_x = code_i + '\nx'
            >>> check_keep_matching(code_x, match, (1, 'foo.rst'))
            Traceback (most recent call last):
            <...>
            ValueError: <...>

        '''
        start_lineno, filepath = where

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

    def expected_as_regex(self, expected, normalize_whitespace, where):
        r'''
        From the expected string create a regular expression that matches
        that string performing the following modifications:
         - if normalize_whitespace is true, replace all the consecutive
           whitespaces by a single regular expression that matched any
           amount of whitespaces. The net effect is that regardless of
           the spaces in expected, the regexp will match one ore more.
         - replace the literals capture tags by regexs. If two or more
           capture tags are consecutive, raise an exception as this is
           ambiguous:

            >>> from byexample.parser import ExampleParser
            >>> expected_as_regex = ExampleParser(0, None).expected_as_regex

            >>> m, _ = expected_as_regex('a<foo>b<bar>c', False, (1, 'foo.rst'))
            >>> # there is not ambiguity here: a----b---c
            >>> m.match('axxbyyyc').groups()
            ('xx', 'yyy')

            >>> # but here? foo is 'x' and bar 'xyyy'?, '' and 'xxyyy', or ....
            >>> expected_as_regex('a<foo><bar>c', False, (1, 'foo.rst'))
            Traceback (most recent call last):
            <...>
            ValueError: <...>

        '''
        start_lineno, filepath = where

        charno = 0
        regexs = []
        names_seen = set()

        regexs.append(r"\A") # the begin of the string
        for match in self.capture_tag_regex().finditer(expected):
            if charno == match.start() and charno > 0:
                msg = "Two consecutive capture tags were found. " +\
                      "This is ambiguous."
                raise ValueError(build_exception_msg(msg, where, self))

            self._add_as_regex(expected[charno:match.start()], regexs, normalize_whitespace)

            name = match.group("name")
            name = name.replace("-", "_") # uniform the name

            if name == self.ellipsis_marker():
                # capture anything (non-greed) but don't
                # capture it
                regex = r"(?:.*?)"

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

        expected_re = re.compile(''.join(regexs), re.MULTILINE | re.DOTALL)
        return expected_re, list(names_seen)

    def _add_as_regex(self, literals, regexs, normalize_whitespace):
        ws_re = self.whitespace_non_compiled_regex()
        if normalize_whitespace:
            non_ws = re.split(ws_re, literals)
            non_ws_escaped = [re.escape(n) for n in non_ws]

            regexs.extend(ws_re.join(non_ws_escaped))
        else:
            regexs.append(re.escape(literals))

    def extract_options(self, snippet, where):
        start_lineno, filepath = where
        optstring_re, opt_re = self.example_options_regex()

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

class ExampleMultiParser(ExampleParser):
    def __init__(self, interpreters, verbosity=0):
        ExampleParser.__init__(self, verbosity, None)
        self.interpreters = interpreters

    def get_examples_from_string(self, options, string, filepath='<string>'):
        all_examples = [i.get_examples_from_string(options, string, filepath) for i in self.interpreters]
        all_examples = sum(all_examples, []) # flatten

        # sort the examples in the same order
        # that they were found in the file/string.
        all_examples.sort(key=lambda this: this.start_lineno)

        self.check_example_overlap(all_examples, filepath)

        return all_examples

    def check_example_overlap(self, examples, filepath):
        if not examples:
            return  # pragma: no cover

        prev = examples[0]
        for example in examples[1:]:
            if prev.end_lineno >= example.start_lineno:
                msg = "In %s, examples at line %i of %s and " +\
                      "at line %i of %s collides."
                msg = msg % (example.filepath, example.start_lineno,
                             example.interpreter, prev.start_lineno,
                             prev.interpreter)
                raise ValueError(msg)

            prev = example

