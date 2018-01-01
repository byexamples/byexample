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
    def __init__(self, allowed_languages, registry, verbosity, use_colors, **unused):
        self.allowed_languages = allowed_languages
        self.verbosity = verbosity
        self.use_colors = use_colors
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

        if self.verbosity >= 2:
            for e in all_examples:
                print_example(e, self.use_colors)

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
                                                    interpreter, where)

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

