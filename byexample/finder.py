import collections, re
from .common import log, build_exception_msg, tohuman, print_example

Where = collections.namedtuple('Where', ['start_lineno',
                                         'end_lineno',
                                         'filepath'])

class ExampleFinder(object):
    '''
          Finding process    Parsing process         Run process
    ----------\                           example
    | foo     |     example match    ............ . . .
    |         |      -----------     : > 1 + 2 } snippet  =>  1 + 2 --> interpreter
    | > 1 + 2 |      | > 1 + 2 |     :                                      |
    | 3       |  =>  | 3       |  => : 3 } expected       =>  3 == ?? <-- output
    |         |      -----------     :.......... .. . .       compare
    | bar     |      -----------                           done by checker
    | > 1 + 3 |  =>  | > 1 + 3 |                                |
    | 4       |      | 4       |                                |--> PASS/FAIL
    :         :      -----------                                      report
                                                                  done by reporter
    '''
    def __init__(self, allowed_languages, registry, verbosity, **unused):
        self.allowed_languages = allowed_languages
        self.verbosity = verbosity
        self.available_finders = registry['finders'].values()

        self.parser_by_language = registry['parsers']
        self.interpreter_by_language = registry['interpreters']

    def get_examples_from_file(self, options, filepath):
        with open(filepath, 'rtU') as f:
            string = f.read()

        return self.get_examples_from_string(options, string, filepath)

    def get_examples_from_string(self, options, string, filepath='<string>'):
        all_examples = []
        for finder in self.available_finders:
            examples = self.get_examples_using(finder, options, string, filepath)
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

        Given that precondition, there are three possible collisions or
        overlaps:

                  Collision 1            Collision 2         Collision 3

              1...........5.....7       1...........5       1...........5
              |    ex1    |             |    ex1    |       |    ex1    |
              |        ex4      |           |  ex2 |        |    ex5    |
                 |      ex2     |       1..2......4         1...........5
              1..2..............7

              A intersect B > 0         A contains B           A == B
              A not contains B

            >>> range1 = (1, 5)
            >>> range2 = (2, 7)
            >>> range3 = (2, 4)
            >>> range4 = (1, 7) # same start_lineno than ex1
            >>> range5 = (1, 5) # same start_lineno and end_lineno than ex1

        Before going into those cases, let's create a helper function to
        build examples:

            >>> # helper function to create examples
            >>> from byexample.parser import Example
            >>> def build_example(language, start_lineno, end_lineno):
            ...    class I: pass    # <- fake interpreter instance
            ...    I.language = language # <- language of the example
            ...    return Example(I,
            ...                   None, None, # <- dummy values
            ...                   start_lineno, end_lineno,
            ...                   *[None]*5)  # <- dummy values

        For the first case (range1 against range2 or range4) it is
        obvious that those pair of examples overlaps and it is not possible
        to distinguish which is correct.

            >>> from byexample.finder import ExampleFinder

            >>> ex1 = build_example('python', *range1)
            >>> ex2 = build_example('python', *range2)

            >>> f = ExampleFinder([], dict((k, {}) for k in \
            ...                   ('parsers', 'finders', 'interpreters')), 0)

            >>> f.check_example_overlap([ex1, ex2], 'foo.rst')
            Traceback<...>
            ValueError: In foo.rst, examples at line 2 (found by <...>) and at line 1 (found by <...>) overlap each other.

            >>> # the same happen with ex4 (checking the 'lt'/'le' condition)
            >>> ex4 = build_example('python', *range4)
            >>> f.check_example_overlap([ex1, ex4], 'foo.rst')
            Traceback<...>
            ValueError: In foo.rst, examples at line 1 (found by <...>) and at line 1 (found by <...>) overlap each other.

        The other possible overlap (collision 2) is when one example is
        inside the other.

        We *assume* that the outer example is the correct and the inner
        example can be discarded correctly.

            >>> ex1 = build_example('python', *range1)
            >>> ex3 = build_example('ruby',   *range3)

            >>> f.check_example_overlap([ex1, ex3], 'foo.rst')
            [Example(<...>start_lineno=1, end_lineno=5<...>)]


        In the third case, both examples are sharing the same spot.
        If the two examples have different we cannot know which is correct:

            >>> ex1 = build_example('python', *range1)
            >>> ex5 = build_example('ruby',   *range5)
            >>> f.check_example_overlap([ex1, ex5], 'foo.rst')
            Traceback<...>
            ValueError: In foo.rst, examples at line 1 (found by <...>) and at line 1 (found by <...>) overlap each other.

        But if both examples have the same language we *assume* that this is not
        an error but two finders found 'the same' example.

        For example, this could happen for the FencedMatchFinder, based on
        the Markdown syntax (```), and PythonFinder, based on the interpreter
        syntax (>>>).
        In this case, the following example will be found by both finders
        for the same Python language:
          ```python
          >>> i = 1
          
          ```

            >>> ex1 = build_example('python', *range1)
            >>> ex5 = build_example('python', *range5)

            >>> f.check_example_overlap([ex1, ex5], 'foo.rst')
            [Example(<...>start_lineno=1, end_lineno=5<...>)]

        '''

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

            same_language = example.interpreter.language == prev.interpreter.language

            if collision_type_2 or (collision_type_3 and same_language):
                # If we have an example inside another example or
                # both example are of the same length and both
                # are about the same language, assume that the outer
                # example is the correct
                where = Where(example.start_lineno, example.end_lineno, filepath)
                self._log_drop("Inner example detected.", where)

                examples[i] = None # to be removed later

            elif collision_type_1 or collision_type_2 or collision_type_3:
                msg = "In %s, examples at line %i (found by %s) and " +\
                      "at line %i (found by %s) overlap each other."
                msg = msg % (filepath, example.start_lineno,
                             example.interpreter, prev.start_lineno,
                             prev.interpreter)
                raise ValueError(msg)

            prev = example

        return list(filter(None, examples))

    def _log_drop(self, reason, where):
        log(build_exception_msg("Dropped example: " + reason, where, self),
                self.verbosity-2)

    def get_examples_using(self, finder, options, string, filepath='<string>'):
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

            # let's find what language is about
            language = finder.get_language_of(options, match, where)
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
            interpreter = self.interpreter_by_language.get(language)
            if not interpreter:
                self._log_drop('no interpreter found for %s language' % language, where)
                continue # TODO should be an error?

            # perfect, we have everything to build an example
            example = parser.get_example_from_match(options, match, example_str,
                                                    interpreter, self, where)

            examples.append(example)


        log("File '%s': %i examples [%s]" % (filepath, len(examples), str(finder)),
                                            self.verbosity-1)

        return examples

class MatchFinder(object):
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

