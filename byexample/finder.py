import collections, re
from .common import log, build_where_msg, tohuman, print_example, \
                    enhance_exceptions

Where = collections.namedtuple('Where', ['start_lineno',
                                         'end_lineno',
                                         'filepath'])

class ExampleHarvest(object):
    '''
          Finding process    Parsing process         Run process
    ----------\                           example
    | foo     |     example match    ............ . . .
    |         |      -----------     : > 1 + 2 } snippet  =>  1 + 2 ----> runner
    | > 1 + 2 |      | > 1 + 2 |     :                                      |
    | 3       |  =>  | 3       |  => : 3 } expected       =>  3 == ?? <-- output
    |         |      -----------     :.......... .. . .       compare
    | bar     |      -----------                           done by checker
    | > 1 + 3 |  =>  | > 1 + 3 |                                |
    | 4       |      | 4       |                                |--> PASS/FAIL
    :         :      -----------                                      report
                                                                  done by reporter
    '''
    def __init__(self, allowed_languages, registry, verbosity,
                        options, **unused):
        self.allowed_languages = allowed_languages
        self.verbosity = verbosity
        self.available_finders = registry['finders'].values()

        self.parser_by_language = registry['parsers']
        self.runner_by_language = registry['runners']

        self.options = options

    def get_examples_from_file(self, filepath):
        with open(filepath, 'rtU') as f:
            string = f.read()

        return self.get_examples_from_string(string, filepath)

    def get_examples_from_string(self, string, filepath='<string>'):
        all_examples = []
        for finder in self.available_finders:
            examples = self.get_examples_using(finder, string, filepath)
            all_examples.extend(examples)

        # sort the examples in the same order
        # that they were found in the file/string.
        all_examples.sort(key=lambda this: this.start_lineno)

        return self.check_example_overlap(all_examples, filepath)

    def check_example_overlap(self, examples, filepath):
        r'''
        It may be possible that two or more examples found by different
        finders overlap: their source lines are actually the same.

        The examples parameter must be a list of examples sorted by their
        start_lineno attribute. In case of two examples with the same
        start_lineno, they must be sorted in reverse order by their end_lineno

        Before going deeper, let's create a helper function to build examples:

            >>> # helper function to create examples
            >>> from byexample.parser import Example
            >>> def build_example(source, expected, language, start_lineno, specific=False):
            ...    class R: pass    # <- fake runner instance
            ...    R.language = language # <- language of the example
            ...
            ...    class F: pass    # <- fake finder instance
            ...    F.specific = specific # <- is finder specific?
            ...
            ...    end_lineno = start_lineno
            ...    end_lineno += (source + '\n' + expected).count('\n') + 1
            ...    return Example(R,
            ...                   None, F,
            ...                   start_lineno, end_lineno,
            ...                   None, None,
            ...                   source, expected)

        And we create a harvester to play with it:

            >>> from byexample.finder import ExampleHarvest
            >>> f = ExampleHarvest([], dict((k, {}) for k in \
            ...                   ('parsers', 'finders', 'runners')), 0, None)

        Okay, back to the check_example_overlap documentation,
        given the examples sorted in that way, a collision is detected if
        the span lines of one example intersect with the span lines of other.

                  Collision 1            Collision 2         Collision 3

              1...........5.....7       1...........5       1...........5
              |  example  |             |  example  |       |  example  |
              |     example     |           |  ex  |        |  example  |
                 |   example    |       1..2......4         1...........5
              1..2..............7

        What do we do will depend of the content of the examples, not only of
        the type of collision:

         - if both examples have the same language and one example is contained
           inside the other (Collision 2 or Collision 3), we drop the example
           found by a generic finder.

           This scenario can happen when a generic finder like FencedMatchFinder
           finds a interpreter-session-like for the same language.
           For example, the following FencedMatchFinder example collides with
           example found by PythonPromptFinder.
                ```python
                >>> 1 + 2
                3

                ```
           So we remove the example of the generic finder (FencedMatchFinder) as
           we assume that it may have more precise information (the correct
           source code and the correct expected string)

           >>> A = build_example('>>> 1 + 2', '3', 'python', start_lineno=1)
           >>> B = build_example('1 + 2', '3', 'python', start_lineno=1, specific=True)

           >>> examples = f.check_example_overlap([A, B], 'foo.rst')
           >>> len(examples)
           1

           >>> examples
           [Example(<...> source='1 + 2', <...>)]


         - if both examples have the same source code, expected string and
           language, those both examples are equivalent, even if the span
           lines are not the same (like in Collision 1 or Collision 2).
           Therefore we will drop the second found

           >>> A = build_example('1 + 2', '3', 'python', start_lineno=1)
           >>> B = build_example('1 + 2', '3', 'python', start_lineno=2)

           >>> examples = f.check_example_overlap([A, B], 'foo.rst')
           >>> len(examples)
           1

           >>> examples
           [Example(<...>start_lineno=1, end_lineno=3<...>)]

         - if the example A has a source code that contains the example B's
           source code and all the B's code is inside in A's one, we will
           assume that the example A is the correct and B was a false positive
           of the finder.

           The idea is that it is hard to find an example's source by mistake,
           given A and B, it is harder to find A's code therefore it is more
           unlikely to be a false positive.

           For example, when a Python comment that starts with # is confused
           with a Shell root session that also starts with #.

           >>> A = build_example('# python comment\n1 + 2', '3', 'python', start_lineno=1)
           >>> B = build_example('# python comment', '1 + 2\n3', 'shell', start_lineno=1)

           >>> examples = f.check_example_overlap([A, B], 'foo.rst')
           >>> len(examples)
           1

           >>> examples
           [Example(<...> source='# python comment\n1 + 2', <...>)]

           The border case is when both examples have the same source code but
           are examples of two different languages.
           It is too ambiguo so we fail

           >>> A = build_example('# python comment', '', 'python', start_lineno=1)
           >>> B = build_example('# python comment', '', 'shell', start_lineno=1)

           >>> examples = f.check_example_overlap([A, B], 'foo.rst')
           Traceback<...>
           ValueError: In foo.rst, examples at line 1 (found by <...>) and at line 1 (found by <...>) overlap each other.

        - in any other case, we fail too

          For a Collision 1:

           >>> A = build_example('a\nb\nc', '', 'sh', start_lineno=1)   # span 3
           >>> B = build_example('d\ne', '', 'sh', start_lineno=1)      # span 2

           >>> examples = f.check_example_overlap([A, B], 'foo.rst')
           Traceback<...>
           ValueError: In foo.rst, examples at line 1 (found by <...>) and at line 1 (found by <...>) overlap each other.

           >>> A = build_example('a\nb', '', 'sh', start_lineno=1)      # span 2
           >>> B = build_example('b\nc', '', 'sh', start_lineno=2)      # span 2

           >>> examples = f.check_example_overlap([A, B], 'foo.rst')
           Traceback<...>
           ValueError: In foo.rst, examples at line 2 (found by <...>) and at line 1 (found by <...>) overlap each other.

          For a Collision 2:

           >>> A = build_example('a\nb\nc', '', 'sh', start_lineno=1)   # span 3
           >>> B = build_example('d', '', 'sh', start_lineno=2)         # span 1

           >>> examples = f.check_example_overlap([A, B], 'foo.rst')
           Traceback<...>
           ValueError: In foo.rst, examples at line 2 (found by <...>) and at line 1 (found by <...>) overlap each other.

          For a Collision 3:

           >>> A = build_example('a\nb', '', 'sh1', start_lineno=1)     # span 2
           >>> B = build_example('a\nb', '', 'sh2', start_lineno=1)     # span 2

           >>> examples = f.check_example_overlap([A, B], 'foo.rst')
           Traceback<...>
           ValueError: In foo.rst, examples at line 1 (found by <...>) and at line 1 (found by <...>) overlap each other.

        '''

        collision_free = False
        while not collision_free:
            collision_free = True
            if not examples:
                return examples # pragma: no cover

            prev = examples[0]
            for i, example in enumerate(examples[1:], 1):
                collision_type_1 = prev.end_lineno >= example.start_lineno
                collision_type_3 = prev.end_lineno == example.end_lineno and \
                                    prev.start_lineno == example.start_lineno
                collision_type_2 = (collision_type_1 and \
                                    example.end_lineno <= prev.end_lineno and \
                                    not collision_type_3)

                any_collision = collision_type_1 or collision_type_2 or collision_type_3

                if not any_collision:
                    prev = example
                    continue

                collision_free = not any_collision
                same_language = example.runner.language == prev.runner.language
                curr_where = Where(example.start_lineno, example.end_lineno, filepath)
                prev_where = Where(prev.start_lineno, prev.end_lineno, filepath)

                if same_language:
                    if collision_type_2 or collision_type_3:
                        if example.finder.specific != prev.finder.specific:
                            if example.finder.specific:
                                del examples[i-1]
                                _where = prev_where
                            else:
                                del examples[i]
                                _where = curr_where

                            self._log_drop("generic/specific overlap", _where)
                            break

                    if example.source == prev.source and \
                            example.expected == prev.expected:

                        del examples[i]
                        self._log_drop("duplicated examples", curr_where)
                        break

                else:
                    if example.source == prev.source:
                        pass # too ambiguous

                    elif example.source in prev.source:
                        del examples[i]
                        self._log_drop("inner example", curr_where)
                        break

                    elif prev.source in example.source:
                        del examples[i-1]
                        self._log_drop("inner example", prev_where)
                        break

                msg = "In %s, examples at line %i (found by %s) and " +\
                      "at line %i (found by %s) overlap each other."
                msg = msg % (filepath, example.start_lineno,
                             example.finder, prev.start_lineno,
                             prev.finder)
                raise ValueError(msg)

        return examples

    def _log_drop(self, reason, where):
        log(build_where_msg(where, self, "Dropped example: " + reason),
                self.verbosity-2)

    def get_examples_using(self, finder, string, filepath='<string>'):
        charno = 0
        start_lineno = 1  # humans tend to count from 1
        examples = []

        for match in finder.get_matches(string):
            example_str = string[match.start():match.end()]

            # start_lineno and end_lineno are inclusive
            start_lineno += string[charno:match.start()].count('\n')
            end_lineno = start_lineno + example_str.count('\n') - 1

            # update charno here
            charno = match.start()

            # where we are, used for the messages of the exceptions
            where = Where(start_lineno, end_lineno, filepath)

            with enhance_exceptions(where, finder):
                # let's find what language is about
                language = finder.get_language_of(self.options, match, where)

                if not language:
                    self._log_drop('language undefined', where)
                    continue

                if language not in self.allowed_languages:
                    self._log_drop('language %s not allowed' % language, where)
                    continue

                # who can parse it?
                parser = self.parser_by_language.get(language)
                if not parser:
                    self._log_drop('no parser found for %s language' % language, where)
                    continue # TODO should be an error?

                # who can execute it?
                runner = self.runner_by_language.get(language)
                if not runner:
                    self._log_drop('no runner found for %s language' % language, where)
                    continue # TODO should be an error?

                # save the indentation here
                indent = match.group('indent')

                # then, get the snippet (runneable code) and the expected (the string)
                # from the example_str
                snippet, expected = finder.get_snippet_and_expected(match, where)

            with enhance_exceptions(where, parser):
                # perfect, we have everything to build an example
                example = parser.build_example(snippet, expected, indent,
                                                        runner, finder, where)

                examples.append(example)


        log("File '%s': %i examples [%s]" % (filepath, len(examples), str(finder)),
                                            self.verbosity-1)

        return examples


class ExampleFinder(object):
    specific = True

    def __init__(self, verbosity, encoding, **unused):
        self.verbosity = verbosity
        self.encoding = encoding

    def example_regex(self):
        raise NotImplementedError() # pragma: no cover

    def get_matches(self, string):
        return self.example_regex().finditer(string)

    def get_language_of(self, options, match, where):
        raise NotImplementedError() # pragma: no cover

    def __repr__(self):
        return '%s Finder' % tohuman(self.target)

    def check_and_remove_indent(self, example_str, indent, where):
        r'''
        Given an example string, remove its indentation

            >>> from byexample.finder import ExampleFinder
            >>> mfinder = ExampleFinder(0, 'utf8'); mfinder.target = 'python-prompt'
            >>> check_and_remove_indent = mfinder.check_and_remove_indent
            >>> check_and_remove_indent('  >>> 1 + 2\n  3', '  ', (1, 2, 'foo.rst'))
            '>>> 1 + 2\n3'

        If the string contains a line with a lower level of indentation,
        raise an exception.

            >>> check_and_remove_indent('  >>> 1 + 2\n3', '  ', (1, 2, 'foo.rst'))
            Traceback (most recent call last):
            <...>
            ValueError: The line 2 is misaligned (wrong indentation). Expected at least 2 spaces.
            001   >>> 1 + 2
            002 3

        The only exception to this are the empty lines
            >>> check_and_remove_indent('  >>> 1 + 2\n\n  3', '  ', (1, 2, 'foo.rst'))
            '>>> 1 + 2\n\n3'

        '''
        start_lineno, _, _ = where

        lines = example_str.split('\n')

        indent_stripped = []
        for lineno, line in enumerate(lines):
            if not line.startswith(indent) and line:
                msg = 'The line %i is misaligned (wrong indentation). ' +\
                      'Expected at least %i spaces.\n%s'

                radio = 2
                context = lines[max(lineno-radio, 0):lineno+radio+1]
                context = [("%03i " % (i + start_lineno)) + l
                            for i, l in enumerate(context, max(lineno-radio, 0))]

                msg = msg % (start_lineno + lineno,
                                len(indent),
                                '\n'.join(context))
                raise ValueError(msg)

            indent_stripped.append(line[len(indent):])

        return '\n'.join(indent_stripped)

    def check_keep_matching(self, example_str, match):
        r'''
        Given an example string, try to apply the match again.
        This is a health-check intended to be used after a call to
        'check_and_remove_indent'

            >>> from byexample.finder import ExampleFinder
            >>> import re

            >>> mfinder = ExampleFinder(0, 'utf8'); mfinder.target = 'python-prompt'
            >>> check_and_remove_indent = mfinder.check_and_remove_indent
            >>> check_keep_matching     = mfinder.check_keep_matching

            >>> code = '  >>> 1 + 2'
            >>> match = re.match(r'[ ]*>>> [^\n]*', code)

            >>> code_i = check_and_remove_indent(code, '  ', (1, 2, 'foo.rst'))
            >>> code_i != code
            True
            >>> new_match = check_keep_matching(code_i, match)

        This should not happen but if for some reason the regex doesn't match
        the full string, raise an exception:

            >>> x_code = 'x' + code_i
            >>> check_keep_matching(x_code, match)
            Traceback (most recent call last):
            <...>
            ValueError: <...>

            >>> code_x = code_i + '\nx'
            >>> check_keep_matching(code_x, match)
            Traceback (most recent call last):
            <...>
            ValueError: <...>

        '''
        new_match = match.re.match(example_str)
        if not new_match:
            msg = 'The regex does not match the example after ' +\
                  'removing the indentation (check_and_remove_indent). '

            raise ValueError(msg)

        if new_match.start() != 0 or new_match.end() != len(example_str):
            msg = '%i bytes were left out after removing the indentation (check_and_remove_indent). ' +\
                  'Dropped bytes at the %s of example:\n%s\n'

            if new_match.start() != 0:
                dropped = example_str[:new_match.start()]
                at = 'begin'
            else:
                dropped = example_str[new_match.end():]
                at = 'end'

            msg = msg % (len(dropped), at, dropped)
            raise ValueError(msg)

        return new_match

    def get_snippet_and_expected(self, match, where):
        r'''
        Given the match object, retrieve the snippet code to be executed
        and the expected output to compare against it.

        Take this opportunity to clean up the snippet and the expected
        before the parsing phase takes place.
        '''

        indent = match.group('indent')
        example_str = match.group(0)

        # update the example_str removing any indentation;
        example_str = self.check_and_remove_indent(example_str, indent, where)

        # check that we still can find the example
        # (allow to generate a new match)
        match = self.check_keep_matching(example_str, match)

        # finally, return the updated snippet and expected strings
        return match.group('snippet'), match.group('expected')
