import collections, re
from .common import log, build_exception_msg

Where = collections.namedtuple('Where', ['start_lineno',
                                         'end_lineno',
                                         'filepath'])

class ExampleFinder(object):
    def __init__(self, verbosity, example_match_finders):
        self.verbosity = verbosity
        self.finders = example_match_finders

    def get_examples_from_file(self, options, filepath, encoding):
        with open(filepath, 'rtU') as f:
            string = f.read()

        return self.get_examples_from_string(options, string, filepath)

    def get_examples_from_string(self, options, string, filepath='<string>'):
        all_examples = []
        for finder in self.finders:
            examples = self.get_examples_using(finder, options, string, filepath)
            all_examples.extend(examples)

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

    def get_examples_using(self, finder, options, string, filepath='<string>'):
        charno = 0
        start_lineno = 1  # humans tend to count from 1
        examples = []
        for match in finder.get_example_matches(string):
            example_str = string[match.start():match.end()]

            # start_lineno and end_lineno are inclusive
            start_lineno += string[charno:match.start()].count('\n')
            end_lineno = start_lineno + example_str.count('\n') - 1

            # update charno here
            charno = match.start()

            # where we are, used for the messages of the exceptions
            where = Where(start_lineno, end_lineno, filepath)

            parser = finder.get_parser_for(options, match, where)
            example = parser.get_example_from_match(options, match, example_str, where)

            if example:
                if self.verbosity >= 2:
                    print_example(example)

                examples.append(example)
            else:
                log(build_exception_msg("Dropped example", where, self),
                    self.verbosity-2)

            options.down()

        log("File '%s': %i examples [Finder %s]" % (filepath, len(examples), str(finder)),
                                            self.verbosity-1)

        return examples

class ExampleMatchFinder(object):
    def example_regex(self):
        raise NotImplementedError() # pragma: no cover

    def get_example_matches(self, string):
        return self.example_regex().finditer(string)

    def get_parser_for(self, options, match, where):
        raise NotImplementedError() # pragma: no cover

