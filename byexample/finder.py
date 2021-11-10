from __future__ import unicode_literals
import os
from . import regex as re
from .common import build_where_msg, tohuman, \
                    enhance_exceptions

from .parser import ExampleParser
from .options import Options
from .log import clog, log_context, DEBUG, CHAT, log_with

from .prof import profile

from .example import Where, Zone, Example
'''
>>> from byexample.log import init_log_system
>>> init_log_system()
'''


def _build_fake_example(
    snippet,
    expected,
    language='python',
    start_lineno=0,
    fully_parsed=True,
    opts=None
):
    class R:
        pass  # <- fake runner instance

    R.language = language  # <- language of the example

    class F:
        pass  # <- fake finder instance

    # fake a parser
    parser = ExampleParser(0, 'utf8', Options())
    parser.language = language

    # fake the options parsed by the parser
    if opts == None:
        opts = Options(
            {
                'norm_ws': False,
                'tags': True,
                'capture': True,
                'rm': [],
                'type': False,
                'input_prefix_range': (6, 12)
            }
        )
    parser.extract_options = lambda x: opts

    # fake the start-end lines where the example "was found"
    end_lineno = start_lineno
    end_lineno += (snippet + '\n' + expected).count('\n') + 1
    where = Where(start_lineno, end_lineno, 'file.md', None)

    # create it
    e = Example(F, R, parser, snippet, expected, "", where)

    # parse it (fake, of course)
    if fully_parsed:
        e = e.parse_yourself(concerns=None)

    return e


class ExampleHarvest(object):
    r'''
                  Finding process             Parsing process
    ----------\                      example                 example (parsed)
    | foo     |      a match       (not parsed)         ............ . . .
    |         |    -----------    -----------           : 1 + 2 } source
    | > 1 + 2 |    | > 1 + 2 |    | 1 + 2 } snippet  => :
    | 3       | => | 3       | => | 3 } expected_str    : 3 } expected (regex)
    |         |    -----------    -----------           :
    | bar     |    -----------                          : options extracted too
    | > 1 + 3 | => | > 1 + 3 |                          :.......... .. . .
    | 4       |    | 4       |                               |         |
    :         :    -----------          /                    V         |
                                       /        executed { 1 + 2       |
                                      /         by runner    |         |
                                     |                  . .  V . . . . V . . .
                              Run    |    compare done  :  output   output   :
                            process  |    by expected   :   got    expected  :
                                     |      object      : .  . . . . . . . . :
                                     |                            |
                                     |                            V
                                     |     report done by     PASS/FAIL
                                     \     differ and by
                                      \       reporter
                                       \         .
    '''
    def __init__(
        self, registry, allowed_languages, verbosity, options, use_colors,
        encoding, **unused
    ):
        self.allowed_languages = allowed_languages
        self.verbosity = verbosity
        self.use_colors = use_colors
        self.available_finders = registry['finders'].values()
        self.encoding = encoding

        self.parser_by_language = registry['parsers']
        self.runner_by_language = registry['runners']
        self.zdelimiter_by_file_extension = registry['zdelimiters']

        self.options = options

    @log_context('byexample.close')
    def close(self):
        pass

    def __repr__(self):
        return 'Example Harvester'

    @log_context('byexample.find')
    def get_examples_from_file(self, filepath):
        f = open(filepath, 'rt', encoding=self.encoding)

        with f as f:
            try:
                string = f.read()
            except UnicodeDecodeError as err:
                msg1 = "Reading the file '%s' using the '%s' encoding failed due decoding errors." % (
                    filepath, self.encoding
                )

                msg2 = msg1 + '\nTry a different encoding with \'--encoding\' from the command line.\n'

                clog().exception(msg2)
                raise SystemExit(msg1)

        return self.get_examples_from_string(string, filepath)

    @log_context('byexample.zones')
    def _get_zones(self, string, filepath='<string>'):
        _, ext = os.path.splitext(filepath)

        zdelimiter = self.zdelimiter_by_file_extension.get(
            ext, self.zdelimiter_by_file_extension['no-delimiter']
        )
        zones = self.get_zones_using(
            zdelimiter, string, filepath, start_lineno=1
        )

        clog().chat(
            "File '%s': %i zones [%s]", filepath, len(zones), str(zdelimiter)
        )

        if clog().isEnabledFor(DEBUG):
            for zone in zones:
                clog().debug("Zone %s", zone.where)

        return zones

    @log_context('byexample.find')
    def get_examples_from_string(self, string, filepath='<string>'):
        all_examples = []
        zones = self._get_zones(string, filepath)

        for finder in self.available_finders:
            nexamples = 0
            for zone in zones:
                examples = self.get_examples_using(
                    finder, zone.str, zone.where.filepath,
                    zone.where.start_lineno
                )
                all_examples.extend(examples)
                nexamples += len(examples)

            clog().chat(
                "File '%s': %i examples [%s]", filepath, nexamples,
                str(finder)
            )

        # sort the examples in the same order
        # that they were found in the file/string;
        # see check_example_overlap
        all_examples.sort(
            key=lambda this: (this.start_lineno, -this.end_lineno)
        )

        all_examples = self.check_example_overlap(all_examples, filepath)

        tmp = set(e.runner.language for e in all_examples)
        clog().chat(
            "Findings in file '%s': %i examples written in %i different languages in %i zones were found.",
            filepath, len(all_examples), len(tmp), len(zones)
        )
        return all_examples

    @profile
    def check_example_overlap(self, examples, filepath):
        r'''
        It may be possible that two or more examples found by different
        finders overlap: their source lines are actually the same.

        The examples parameter must be a list of examples sorted by their
        start_lineno attribute. In case of two examples with the same
        start_lineno, they must be sorted in reverse order by their end_lineno

        Before going deeper, let's use a helper function to build examples:

            >>> from byexample.finder import _build_fake_example as build_example

        And create a harvester to play with it:

            >>> from byexample.finder import ExampleHarvest
            >>> f = ExampleHarvest(dict((k, {}) for k in \
            ...                   ('parsers', 'finders', 'runners', 'zdelimiters')),
            ...                    [], 0, 0, None, 'utf-8')

        Okay, back to the check_example_overlap documentation,
        given the examples sorted in that way, a collision is detected if
        the span lines of one example intersect with the span lines of other.

                  Collision 1            Collision 2          Collision 3

              1...........3.....4     1.................4    1...........3.....4
              | example A |           |    example B    |    | example A |
              |     example B   |           | ex C|                | example D |
              1.................4     1.....2.....3.....4    1.....2...........4


            >>> A = build_example('1\n2',  '3',    'A', start_lineno=1)
            >>> B = build_example('1\n2',  '3\n4', 'B', start_lineno=1)
            >>> C = build_example('2',     '3',    'C', start_lineno=2)
            >>> D = build_example('2\n3',  '4',    'D', start_lineno=2)

        Collision 1: two examples begin in the same line where one
        may be larger than the other. This is too ambiguous:

            >>> examples = f.check_example_overlap([B, A], 'foo.rst')
            Traceback<...>
            ValueError: In foo.rst, examples at lines 1-4 (found by <...>) and at lines 1-5 (found by <...>) overlap each other.


        Collision 2: one example is a subset of the other and may both end
        in the same line. It makes sense to drop the smaller one:

            >>> examples = f.check_example_overlap([B, C], 'foo.rst')
            >>> len(examples)
            1

            >>> examples
            [Example [B] in file <...>, lines 1-5]

        Collision 3: two examples overlap but they are not neither of those
        two previous collisions.

            >>> examples = f.check_example_overlap([A, D], 'foo.rst')
            Traceback<...>
            ValueError: In foo.rst, examples at lines 2-5 (found by <...>) and at lines 1-4 (found by <...>) overlap each other.

        '''

        collision_free = False
        while not collision_free:
            collision_free = True
            if not examples:
                return examples  # pragma: no cover

            prev = examples[0]
            for i, example in enumerate(examples[1:], 1):
                collision_type_1 = prev.start_lineno == example.start_lineno
                collision_type_2 = not collision_type_1 and \
                                    (example.end_lineno <= prev.end_lineno)
                collision_type_3 = not collision_type_1 and \
                                    not collision_type_2 and \
                                    example.start_lineno <= prev.end_lineno

                any_collision = collision_type_1 or collision_type_2 or collision_type_3
                if not any_collision:
                    prev = example
                    continue

                collision_free = not any_collision
                curr_where = Where(
                    example.start_lineno, example.end_lineno, filepath,
                    example.zdelimiter
                )
                prev_where = Where(
                    prev.start_lineno, prev.end_lineno, filepath,
                    prev.zdelimiter
                )

                self._log_debug(" * Collision Type (1/2/3): %s/%s/%s\n"        \
                                " * Languages (prev/current): %s/%s\n"         \
                                    % (collision_type_1, collision_type_2,
                                        collision_type_3, prev.runner.language,
                                        example.runner.language), curr_where)
                prev.pretty_print()
                example.pretty_print()

                if collision_type_2:
                    del examples[i]
                    self._log_drop("inner example", curr_where)
                    break

                msg = "In %s, examples at lines %i-%i (found by %s) and " +\
                      "at lines %i-%i (found by %s) overlap each other."
                msg = msg % (
                    filepath, example.start_lineno, example.end_lineno,
                    example.finder, prev.start_lineno, prev.end_lineno,
                    prev.finder
                )
                raise ValueError(msg)

        if clog().isEnabledFor(CHAT):
            clog().debug("Examples after removing any overlapping")
            for finder in set(e.finder for e in examples):
                clog().chat(
                    "File '%s': %i examples [%s]", filepath,
                    len([e for e in examples if e.finder == finder]),
                    str(finder)
                )

        if True or clog().isEnabledFor(DEBUG):
            for e in examples:
                e.pretty_print()
        return examples

    def _log_drop(self, reason, where):
        self._log_debug(" => Dropped example: " + reason, where)

    def _log_debug(self, what, where):
        clog().debug(build_where_msg(where, self, what))

    @profile
    def get_examples_using(self, finder, string, filepath, start_lineno):
        return self.from_string_get_items_using(
            finder, string, self.get_example, 'examples', filepath,
            start_lineno
        )

    @profile
    def get_zones_using(self, zdelimiter, string, filepath, start_lineno):
        return self.from_string_get_items_using(
            zdelimiter, string, self.get_zone, 'zones', filepath, start_lineno
        )

    def get_example(self, finder, match, where):
        with enhance_exceptions(where, finder):
            # let's find what language is about
            language = finder.get_language_of(self.options, match, where)

            if not language:
                self._log_drop('language undefined', where)
                return

            if language not in self.allowed_languages:
                self._log_drop('language %s not allowed' % language, where)
                return

        with enhance_exceptions(where, finder), log_with(language):
            # who can parse it?
            parser = self.parser_by_language.get(language)
            if not parser:
                self._log_drop(
                    'no parser found for %s language' % language, where
                )
                return  # TODO should be an error?

            # who can execute it?
            runner = self.runner_by_language.get(language)
            if not runner:
                self._log_drop(
                    'no runner found for %s language' % language, where
                )
                return  # TODO should be an error?

            # save the indentation here
            indent = match.group('indent')

            # then, get the source (runneable code) and the expected (the string)
            snippet, expected = finder.get_snippet_and_expected(match, where)

            if expected == None:
                expected = ""

        with enhance_exceptions(where, parser), log_with(language):
            # perfect, we have everything to build an example
            example = Example(
                finder, runner, parser, snippet, expected, indent, where
            )
            return example

    def get_zone(self, zdelimiter, match, where):
        with enhance_exceptions(where, zdelimiter):
            zone_str = zdelimiter.get_zone(match, where)
            return Zone(zdelimiter, zone_str, where)

    def from_string_get_items_using(
        self,
        matcher,
        string,
        getter,
        what,
        filepath='<string>',
        start_lineno=1,
        zdelimiter=None
    ):
        charno = 0
        items = []

        for match in matcher.get_matches(string, filepath):
            str_matched = string[match.start():match.end()]
            if str_matched.endswith('\n'):
                str_matched = str_matched[:-1]

            # start_lineno and end_lineno are inclusive
            start_lineno += string[charno:match.start()].count('\n')
            end_lineno = start_lineno + str_matched.count('\n')

            # update charno here
            charno = match.start()

            # where we are, used for the messages of the exceptions
            where = Where(start_lineno, end_lineno, filepath, zdelimiter)

            item = getter(matcher, match, where)
            if item is not None:
                items.append(item)
        return items


class ExampleFinder(object):
    def __init__(self, verbosity, encoding, **unused):
        self.verbosity = verbosity
        self.encoding = encoding

    def example_regex(self):
        raise NotImplementedError()  # pragma: no cover

    def get_matches(self, string, filepath='<string>'):
        return self.example_regex().finditer(string)

    def get_language_of(self, options, match, where):
        raise NotImplementedError()  # pragma: no cover

    def __repr__(self):
        return '%s Finder' % tohuman(self.target if self.target else self)

    def check_and_remove_indent(self, example_str, indent, where):
        r'''
        Given an example string, remove its indentation

            >>> from byexample.finder import ExampleFinder, Where
            >>> mfinder = ExampleFinder(0, 'utf8'); mfinder.target = 'python-prompt'
            >>> check_and_remove_indent = mfinder.check_and_remove_indent

            >>> where = Where(1, 2, 'foo.rst', None)
            >>> check_and_remove_indent('  >>> 1 + 2\n  3', '  ', where)
            '>>> 1 + 2\n3'

            >>> where
            (1, 2, 'foo.rst', None)

        If the string contains a line with a lower level of indentation,
        truncate the example at that point and ignore the rest.

            >>> check_and_remove_indent('  >>> 1 + 2\n3', '  ', where)
            '>>> 1 + 2'

            >>> where
            (1, 1, 'foo.rst', None)

        The only exception to this are the empty lines
            >>> check_and_remove_indent('  >>> 1 + 2\n\n  3', '  ', where)
            '>>> 1 + 2\n\n3'

        '''
        start_lineno, _, _, _ = where

        lines = example_str.split('\n')

        indent_stripped = []
        for lineno, line in enumerate(lines):
            if not line.startswith(indent) and line:
                # shrink the example and update the new end line number
                where.end_lineno = start_lineno + lineno - 1
                break

            indent_stripped.append(line[len(indent):])

        if not indent_stripped:
            raise ValueError("Inconsistent state.")

        return '\n'.join(indent_stripped)

    def check_keep_matching(self, example_str, match):
        r'''
        Given an example string, try to apply the match again.

        This is a health-check intended to be used after a call to
        'check_and_remove_indent' and other processing functions.

            >>> from byexample.finder import ExampleFinder
            >>> import byexample.regex as re

            >>> mfinder = ExampleFinder(0, 'utf8'); mfinder.target = 'python-prompt'
            >>> check_and_remove_indent = mfinder.check_and_remove_indent
            >>> check_keep_matching     = mfinder.check_keep_matching

            >>> code = '  >>> 1 + 2'
            >>> match = re.compile(r'[ ]*>>> [^\n]*').match(code)

            >>> code_i = check_and_remove_indent(code, '  ', (1, 2, 'foo.rst', None))
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
                  'processing it (filtering & removing) done by ' +\
                  'ExampleFinder.get_snippet_and_expected method. '

            raise ValueError(msg)

        if new_match.start() != 0 or new_match.end() != len(example_str):
            msg = '%i bytes were left out after processing it ' +\
                  '(filtering & removing) done by '+\
                  'ExampleFinder.get_snippet_and_expected method. ' +\
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


class ZoneDelimiter(object):
    def __init__(self, verbosity, encoding, **unused):
        self.verbosity = verbosity
        self.encoding = encoding

    def zone_regex(self):
        raise NotImplementedError()  # pragma: no cover

    def get_matches(self, string, filepath='<string>'):
        return self.zone_regex().finditer(string)

    def get_zone(self, match, where):
        return match.group('zone')

    def __repr__(self):
        return '%s Zone Delimiter' % tohuman(
            self.target if self.target else self
        )
