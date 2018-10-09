import re
from byexample.finder import ExampleFinder

stability = 'stable'

class FencedMatchFinder(ExampleFinder):
    target = 'markdown-fenced-code'
    specific = False

    def example_regex(self):
        return re.compile(r'''
            # Begin with a markdown fenced-code marker, followed by the
            # language
            ^[ ]*```[ ]*  (?P<language>\w+) .*\n

            # then, grab everything until the first end marker or expected marker
            (?P<snippet>
                (?: [ ]*\n )*                         # ignore any empty line
                (?:^(?P<indent> [ ]*)[^ ] .*)         # first line
                (?:\n                           # the rest of the line that
                        (?![ ]*out:[ ]*\n)      # don't start with the expected marker
                        (?![ ]*```)             # don't start with the end marker
                .*)*)                           # anything else is welcome

            \n?

            # the expected output, optional
            (?: [ ]* out:[ ]*\n
                # Followed by the expected output consists of any non-blank
                # lines that do not start with the end marker
                (?P<expected> (?:(?![ ]*$)     # Not a blank line
                              (?![ ]*```)      # Not a line starting with end marker
                             .+$\n?            # But any other line
                          )*)
            )?

            (?: [ ]*\n )*                         # ignore any empty line

            # finally, the end marker
            ^[ ]*```[ ]*$\n?
            ''', re.MULTILINE | re.VERBOSE)

    def get_language_of(self, options, match, where):
        return match.group("language")

    def spurious_endings(self):
        endings = ExampleFinder.spurious_endings(self)
        return endings - {'```', '~~~'}
