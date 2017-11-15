import sys, argparse, traceback, collections, re, os, pkgutil, inspect, time
from doctest import _indent

Example = collections.namedtuple('Example', ['interpreter', 'filepath',
                                             'lineno', 'end_lineno', 'options',
                                             'indentation',
                                             'source', 'expected', 'expected_re',
                                             'capture', 'match'])

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

def build_exception_msg(msg, where):
    start_lineno, filepath = where
    return 'File "%s", line %i\n%s' % (filepath, start_lineno, msg)


def log(msg, x):
    if x >= 0:
        print(msg)

class Options(collections.MutableMapping):
    r'''
    The execution of the examples can be modified by configuring different options.

    ``Options`` behaves as a normal dictionary

        >>> opt = Options()

        >>> opt['foo'] = 42
        >>> opt['foo']
        42

        >>> opt['bar']
        Traceback (most recent call last):
        KeyError: 'bar'

        >>> len(opt)
        1

        >>> del opt['foo']
        >>> len(opt)
        0

    But the interesting is that it works as a stack of dictionaries: one can push
    a new dictionary on the top of the stack where new keys can be set but the
    rest of the dictionaries are keep intact.
    If a key is retrieved, the search starts from the top through all the stack
    until the key is found.
    To control the stack there are two methods ``up`` and ``down``. We could use
    the classic ``push`` and ``pop`` but a dictionary already has a ``pop`` so
    we preferred to not break that contract.

        >>> opt['foo'] = 42
        >>> opt.up() # push a new dictionary
        >>> opt['bar'] = 256

        >>> opt['foo'], opt['bar'] # look up through the entire stack
        (42, 256)

        >>> len(opt)
        2

        >>> sorted(list(opt))
        ['bar', 'foo']

        >>> d = opt.as_dict()   # actually, you can see it as a normal dictionary
        >>> isinstance(d, dict)
        True
        >>> d['foo'], d['bar']
        (42, 256)

        >>> del opt['foo'] # but only the top most dictionary is mutable
        Traceback (most recent call last):
        KeyError: 'foo'

        >>> opt['foo'] = 257 # this only hides the 'foo' key of the dict below
        >>> opt['foo']
        257

        >>> opt.down() # remove the top most dictionary from the stack
        >>> opt['foo']
        42

        >>> 'bar' in opt
        False

    Multiple levels are allowed

        >>> opt = Options({'foo': 1})
        >>> opt.up({'foo': 2, 'bar': 2})
        >>> opt.up({'foo': 3, 'baz': 3})

        >>> sorted(list(opt))
        ['bar', 'baz', 'foo']

        >>> [opt[x] for x in sorted(list(opt))]
        [2, 3, 3]

        >>> opt.down()
        >>> [opt[x] for x in sorted(list(opt))]
        [2, 2]

        >>> opt.down()
        >>> [opt[x] for x in sorted(list(opt))]
        [1]

        >>> opt.down()
        Traceback (most recent call last):
        IndexError: list index out of range

    '''

    def __init__(self, *args, **kwargs):
        self.top = dict()
        self.stack = [self.top] # [top, ...., bottom]

        self.cache = None

        self.update(dict(*args, **kwargs))  # use the free update to set keys

    def __getitem__(self, key):
        for d in self.stack:
            if key in d:
                return d[key]

        return self.top[key] # KeyError

    def __setitem__(self, key, value):
        self.top[key] = value

    def __delitem__(self, key):
        del self.top[key]

    def __iter__(self):
        return iter(self.as_dict())

    def __len__(self):
        return len(self.as_dict())

    def __repr__(self):
        return repr(self.as_dict())

    def up(self, other_mapping=None):
        if isinstance(other_mapping, Options):
            other_mapping = other_mapping.as_dict()

        self.top = other_mapping if other_mapping is not None else {}
        self.stack.insert(0, self.top)
        if self.top:
            self.cache = None

    def down(self):
        if self.top:
            self.cache = None

        del self.stack[0]
        self.top = self.stack[0]

    def as_dict(self):
        if len(self.stack) > 1 and self.cache is not None:
            collapsed = self.cache.copy()
        elif len(self.stack) == 1:
            collapsed = {}
        else:
            collapsed = self.stack[-1].copy()
            for d in reversed(self.stack[1:-1]):
                collapsed.update(d)

            self.cache = collapsed.copy()

        collapsed.update(self.top)
        return collapsed

    def copy(self):
        clone = Options()
        clone.stack = list(self.stack) # copy
        clone.cache = self.cache       # do not copy
        clone.top = clone.stack[0]

        return clone

class ExampleParser(object):
    def __init__(self, verbosity=0):
        self.verbosity = verbosity

    def example_regex(self):
        '''
        Return a regular expression to match an example with at
        least three groups:
         - indent: to capture the indentation of the example (first line)
         - source: the code to execute (including any prompt string)
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

    def remove_prompts(self, source):
        '''
        Remove from the source the prompts. The given source is aligned
        and with its indentation removed.
        '''
        raise NotImplementedError() # pragma: no cover

    def get_examples_from_file(self, options, filepath, encoding):
        with open(filepath, 'r') as f:
            string = f.read()

        return self.get_examples_from_string(options, string, filepath)

    def get_examples_from_string(self, options, string, filepath='<string>'):
        charno = 0
        lineno = 1  # humans tend to count from 1
        examples = []
        for match in self.example_regex().finditer(string):
            example_str = string[match.start():match.end()]

            # lineno and end_lineno are inclusive
            lineno += string[charno:match.start()].count('\n')
            end_lineno = lineno + example_str.count('\n') - 1

            # update charno here
            charno = match.start()

            # where we are, used for the messages of the exceptions
            where = (lineno, filepath)

            indent = match.group('indent')
            example_str = self.check_and_remove_ident(example_str, indent, where)
            match = self.check_keep_matching(example_str, match, where)

            source   = match.group("source")
            expected_str = match.group("expected")

            options.up(self.extract_options(source, where))

            norm_ws = options.get('WS', False)

            if norm_ws:
                expected_str = self.normalize_whitespace(expected_str)

            expected_re, capture = self.expected_as_regex(expected_str, norm_ws, where)

            source = self.remove_prompts(source)
            if not source.endswith('\n'):
                source   += '\n'

            example = Example(
                              # the source and the expected strings extracted from 'match'
                              source=source, expected=expected_str,

                              # expected regex version
                              expected_re=expected_re,

                              # the names of the capture tags in the expected regex
                              capture=capture,

                              # the options to customize this example
                              options=options.copy(),

                              # full match of this example (without indentation)
                              match=match,

                              # the original indentation of the example
                              indentation=indent,

                              # file from where this example was extracted
                              filepath=filepath,

                              # start / end line numbers (inclusive) in the file
                              lineno=lineno, end_lineno=end_lineno,

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
            >>> check_and_remove_ident = ExampleParser().check_and_remove_ident
            >>> check_and_remove_ident('  >>> 1 + 2\n  3\n ', '  ', (1, 'foo.rst'))
            '>>> 1 + 2\n3'

        If the string contains a line with a lower level of indentation,
        raise an exception.

            >>> check_and_remove_ident('  >>> 1 + 2\n3\n', '  ', (1, 'foo.rst')) # doctest: +ELLIPSIS
            Traceback (most recent call last):
            ValueError: ...

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
                raise ValueError(build_exception_msg(msg, where))

            indent_stripped.append(line[len(indent):])

        return '\n'.join(indent_stripped)

    def check_keep_matching(self, example_str, match, where):
        r'''
        Given an example string, try to apply the match again.
        This is a health-check intended to be used after a call to
        'check_and_remove_ident'

            >>> check_and_remove_ident = ExampleParser().check_and_remove_ident
            >>> check_keep_matching    = ExampleParser().check_keep_matching

            >>> code = '  >>> 1 + 2'
            >>> match = re.match(r'[ ]*>>> [^\n]*', code)

            >>> code_i = check_and_remove_ident(code, '  ', (1, 'foo.rst'))
            >>> code_i != code
            True
            >>> new_match = check_keep_matching(code_i, match, (1, 'foo.rst'))

        This should not happen but if for some reason the regex doesn't match
        the full string, raise an exception:

            >>> x_code = 'x' + code_i
            >>> check_keep_matching(x_code, match, (1, 'foo.rst')) # doctest: +ELLIPSIS
            Traceback (most recent call last):
            ValueError: ...

            >>> code_x = code_i + '\nx'
            >>> check_keep_matching(code_x, match, (1, 'foo.rst')) # doctest: +ELLIPSIS
            Traceback (most recent call last):
            ValueError: ...

        '''
        start_lineno, filepath = where

        new_match = match.re.match(example_str)
        if not new_match:
            msg = 'The regex does not match the example after ' +\
                  'removing the indentation. '

            raise ValueError(build_exception_msg(msg, where))

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
            raise ValueError(build_exception_msg(msg, where))

        return new_match

    def normalize_whitespace(self, expected_str):
        ws_re = self.whitespace_non_compiled_regex()
        return ' '.join(re.split(ws_re, expected_str))

    def expected_as_regex(self, expected_str, normalize_whitespace, where):
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

            >>> expected_as_regex = ExampleParser().expected_as_regex

            >>> m, _ = expected_as_regex('a<foo>b<bar>c', False, (1, 'foo.rst'))
            >>> # there is not ambiguity here: a----b---c
            >>> m.match('axxbyyyc').groups()
            ('xx', 'yyy')

            >>> # but here? foo is 'x' and bar 'xyyy'?, '' and 'xxyyy', or ....
            >>> expected_as_regex('a<foo><bar>c', False, (1, 'foo.rst')) # doctest: +ELLIPSIS
            Traceback (most recent call last):
            ValueError: ...

        '''
        start_lineno, filepath = where

        charno = 0
        regexs = []
        names_seen = set()

        regexs.append(r"\A") # the begin of the string
        for match in self.capture_tag_regex().finditer(expected_str):
            if charno == match.start() and charno > 0:
                msg = "Two consecutive capture tags were found. " +\
                      "This is ambiguous."
                raise ValueError(build_exception_msg(msg, where))

            self._add_as_regex(expected_str[charno:match.start()], regexs, normalize_whitespace)

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

        self._add_as_regex(expected_str[charno:], regexs, normalize_whitespace)

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

    def extract_options(self, source, where):
        start_lineno, filepath = where
        optstring_re, opt_re = self.example_options_regex()

        match = optstring_re.search(source)
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
                raise ValueError(build_exception_msg(msg, where))

            options[name] = True if add else False

        return options

class ExampleMultiParser(ExampleParser):
    def __init__(self, interpreters, verbosity=0):
        ExampleParser.__init__(self, verbosity)
        self.interpreters = interpreters

    def get_examples_from_string(self, options, string, filepath='<string>'):
        all_examples = [i.get_examples_from_string(options, string, filepath) for i in self.interpreters]
        all_examples = sum(all_examples, []) # flatten

        # sort the examples in the same order
        # that they were found in the file/string.
        all_examples.sort(key=lambda this: this.lineno)

        self.check_example_overlap(all_examples, filepath)

        return all_examples

    def check_example_overlap(self, examples, filepath):
        if not examples:
            return  # pragma: no cover

        prev = examples[0]
        for example in examples[1:]:
            if prev.end_lineno >= example.lineno:
                msg = "In %s, examples at line %i of %s and " +\
                      "at line %i of %s collides."
                msg = msg % (example.filepath, example.lineno,
                             example.interpreter, prev.lineno,
                             prev.interpreter)
                raise ValueError(msg)

            prev = example


class ExampleRunner(object):
    def __init__(self, reporter, checker, verbosity=0):
        self.reporter  = reporter
        self.checker   = checker
        self.verbosity = verbosity

    def initialize_interpreters(self, interpreters):
        log("Initializing %i interpreters..." % len(interpreters),
                                                    self.verbosity-1)
        for interpreter in interpreters:
            log("* %s" % str(interpreter), self.verbosity-1)
            interpreter.initialize()

    def shutdown_interpreters(self, interpreters):
        log("Shutting down %i interpreters..." % len(interpreters),
                                                    self.verbosity-1)
        for interpreter in interpreters:
            log("* %s" % str(interpreter), self.verbosity-1)
            interpreter.shutdown()

    def run(self, examples, options, filepath):
        interpreters = list(set(e.interpreter for e in examples))

        self.initialize_interpreters(interpreters)
        self.reporter.start_run(examples, interpreters, filepath)

        fail_fast = options['FAIL_FAST']

        failed = False
        user_aborted = False
        crashed = False
        for example in examples:
            options.up(example.options)
            try:
                if options['SKIP']:
                    self.reporter.skip_example(example, options)
                    continue

                self.reporter.start_example(example, options)
                try:
                    got = example.interpreter.run(example, options)
                except KeyboardInterrupt:    # pragma: no cover
                    self.reporter.user_aborted(example)
                    user_aborted = True
                except Exception as e:       # pragma: no cover
                    self.reporter.crashed(example, e)
                    crashed = True

                if user_aborted or crashed:  # pragma: no cover
                    failed = True
                    break # always fail fast if the user aborted or code crashed

                force_pass = options['PASS']
                if force_pass or self.checker.check_output(example, got, options):
                    self.reporter.success(example, got, self.checker)
                else:
                    self.reporter.failure(example, got, self.checker)
                    failed = True
                    if fail_fast:
                        break
            finally:
                options.down()

        self.reporter.end_run(examples, interpreters)
        self.shutdown_interpreters(interpreters)

        return failed, (user_aborted or crashed)

class SimpleReporter(object):
    def __init__(self, output, quiet=False, verbosity=0):
        self.output = output
        self.quiet = quiet
        self.verbosity = verbosity

    def _write(self, msg):
        if self.quiet:
            return

        self.output.write(msg)
        self.output.flush()

    def start_run(self, examples, interpreters, filepath):
        self.num_examples = len(examples)
        self.examplenro = 0
        self.in_dot_line = True
        self.filepath = filepath
        self.begin = time.time()

        self.fail = self.good = self.aborted_or_crashed = self.skipped = 0

    def end_run(self, examples, interpreters):
        if self.in_dot_line:
            self._write('\n')

        elapsed   = max(time.time() - self.begin, 0)
        if elapsed < 300:
            elapsed_str = "%0.2f seconds" % elapsed
        elif elapsed < 3600:
            elapsed_str = "%i minutes, %i seconds" % (elapsed / 60,
                                                      elapsed % 60)
        else:
            # if your examples run in terms of hours you may have
            # a real problem... I desire to you the best of the luck
            elapsed_str = "%i hours, %i minutes" % ( elapsed / 3600,
                                                    (elapsed % 3600) / 60)

        msg = "File %s, %i/%i test ran in %s\nPass: %i Fail: %i Aborted: %i\n" % (
                    self.filepath,
                    self.examplenro, (self.num_examples - self.skipped),
                    elapsed_str,
                    self.good, self.fail, self.aborted_or_crashed)
        self._write(msg)

    def skip_example(self, example, options):
        self.skipped += 1

    def start_example(self, example, options):
        self.examplenro += 1
        self.current_merged_flags = options

    def user_aborted(self, example):
        if self.in_dot_line:  # pragma: no cover
            self._write('\n')
            self.in_dot_line = False

        msg = 'Execution aborted by the user at example %i of %i.\n' % (
                                    self.examplenro, self.num_examples)
        self._print_error_header(example)
        self._write(msg)
        self.aborted_or_crashed += 1

    def crashed(self, example, exception):
        if self.in_dot_line:  # pragma: no cover
            self._write('\n')
            self.in_dot_line = False

        msg = 'Execution of example %i of %i crashed.\n%s' % (
                                    self.examplenro, self.num_examples,
                                    traceback.format_exc(exception))
        self._print_error_header(example)
        self._write(msg)
        self.aborted_or_crashed += 1

    def success(self, example, got, checker):
        if not self.in_dot_line:  # pragma: no cover
            self._write('\n')
            self.in_dot_line = True

        self._write('.')

        self.good += 1

    def failure(self, example, got, checker):
        if not self.in_dot_line:  # pragma: no cover
            self._write('\n')
            self.in_dot_line = True

        self._write('F\n')

        self._print_error_header(example)
        diff = checker.output_difference(example, got, self.current_merged_flags)
        self._write(diff)
        self._write('\n')

        self.fail += 1

    def _print_error_header(self, example):
        filepath = example.filepath
        lineno = example.lineno

        self._write("*" * 70)

        msg = '\nFile "%s", line %i\n' % (filepath, lineno+1)
        self._write(msg)

        self._write("Failed example:\n")
        self._write(_indent(example.source))

class Checker(object):
    def check_output(self, example, got, flags):
        return example.expected_re.match(got) is not None

    def output_difference(self, example, got, flags):
        self._diff = []
        self.normal_diff(example, got)

        return ''.join(self._diff)

    def _write(self, s, end_with_newline=True):
        self._diff.append(s)
        if end_with_newline and not s.endswith('\n'):
            self._diff.append('\n')

    def normal_diff(self, example, got):
        if example.expected:
            self._write("Expected:")
            self._write(repr(example.expected))

        else:
            self._write("Expected nothing")

        if got:
            self._write("Got:")
            self._write(repr(got))

        else:
            self._write("Got nothing")

def parse_args():
    search_default = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'interpreters')
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs='+', metavar='file',
                        help="file that have the examples to run.")
    parser.add_argument("-f", "--fail-fast", action='store_true',
                        help="if an example fails, fail and stop all the execution.")
    parser.add_argument("--dry", action='store_true',
                        help="do not run any example, only parse them.")
    parser.add_argument("--skip", nargs='+', metavar='file', default=[],
                        help='skip these files')
    parser.add_argument("--search", action='append', metavar='dir',
                        default=[search_default],
                        help='append a directory for searching interpreters there.')

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", action='count', dest='verbosity', default=0,
                        help="verbosity level, add more flags to increase the level.")
    group.add_argument("-q", "--quiet", action='store_true',
                        help="quiet mode, do not print anything even if an example fails.")

    return parser.parse_args()

def is_an_interpreter(obj):
    if not inspect.isclass(obj):
        return False

    for attr in ('get_examples_from_string', 'run', 'INTERPRETER_NAME'):
        if not hasattr(obj, attr):
            return False

    return True

def search_interprerters(dirnames, verbosity=0):
    interpreters = []
    for importer, name, is_pkg in pkgutil.iter_modules(dirnames):
        path = importer.path
        log("From '%s' loading '%s'..." % (path, name), verbosity-2)

        try:
            module = importer.find_module(name).load_module(name)
        except Exception as e:
            log("From '%s' loading '%s'...failed: %s" % (path, name, str(e)),
                                                        verbosity-2)
            continue

        found = inspect.getmembers(module, is_an_interpreter)
        if not found:
            log("From '%s' loaded '%s', found nothing." % (path, name), verbosity-1)
        else:
            i_names, i_classes = zip(*found)
            i_names_str = ', '.join(i_names)
            log("From '%s' loaded '%s', found %i interpreters: %s" % (
                                    path, name, len(i_classes), i_names_str),
                                        verbosity-1)

            interpreters.extend(i_classes)

    return [klass(verbosity) for klass in interpreters]


def main():
    args = parse_args()
    available_interpreters = search_interprerters(args.search, args.verbosity)

    allowed_files = set(args.files) - set(args.skip)
    testfiles = [f for f in args.files if f in allowed_files]

    reporter = SimpleReporter(sys.stdout, args.quiet)
    checker  = Checker()
    options  = Options(FAIL_FAST=args.fail_fast, WS=False, PASS=False,
                       SKIP=False)

    encoding = sys.stdout.encoding

    parser = ExampleMultiParser(available_interpreters, args.verbosity)
    runner = ExampleRunner(reporter, checker, args.verbosity)

    exit_status = 0
    for filename in testfiles:
        examples = parser.get_examples_from_file(options, filename, encoding)
        if args.dry:
            continue

        result = runner.run(examples, options, filename)
        failed, aborted_or_crashed = result

        if failed:
            exit_status = max(exit_status, 1)

        if aborted_or_crashed:
            exit_status = max(exit_status, 2)

        if (failed or aborted_or_crashed) and options['FAIL_FAST']:
            break

    return exit_status
