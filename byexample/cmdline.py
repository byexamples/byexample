from __future__ import unicode_literals
import sys, argparse, os, multiprocessing, glob, itertools, codecs
import bracex
from . import __version__, __doc__, _author, _license, _url, _license_disclaimer

from .log_level import str_to_level
from .prof import profile
'''
>>> from byexample.cmdline import ByexampleArgumentParser
>>> from byexample.cmdline import _expand_brace_glob_patterns
'''


def _byexample_location():
    ''' Return the location of the current file (cmdline.py)
        and the paths of the python package for byexample.

        The paths are joined with ; so the paths and the location
        are string, returned in a dictionary.
    '''
    import byexample
    try:
        paths = '; '.join(byexample.__path__)
    except:
        paths = 'paths are unknown'

    try:
        loc = os.path.dirname(byexample.__file__)
    except:
        loc = 'could not be found'

    return dict(paths=paths, loc=loc)


def _byexample_dependencies():
    ''' Return a single string of the dependencies and its versions
        joined with a comma.

        If a dependency cannot be loaded, assume that it is not installed
        (aka, not found). If the version cannot be determined, set it
        to unknown.

    '''
    import importlib
    tmp = []
    for dependency in (
        'appdirs',
        'argcomplete',
        'bracex',
        'pexpect',
        'pygments',
        'termscraper',
        'tqdm',
    ):

        try:
            mod = importlib.import_module(dependency)
        except ImportError:
            msg = f'{dependency} (not found)'
        else:
            try:
                ver = mod.__version__
                msg = f'{dependency} ({ver})'
            except AttributeError:
                msg = f'{dependency} (unknown)'

        tmp.append(msg)

    return ', '.join(tmp)


class _CSV(argparse.Action):
    r'''Transform an argument of the form 'a,b' into a list
        of arguments [a, b]
        '''
    def __call__(self, parser, namespace, values, option_string=None):
        # -l a,b  => [a, b]
        values = values.split(',')
        getattr(namespace, self.dest).extend(values)


class _Print(argparse.Action):
    r'''Print a given message bypassing the formatting rules of
        argparse, then, exit.'''
    def __init__(self, *args, **kargs):
        self.message = kargs.pop('message')
        argparse.Action.__init__(self, *args, **kargs)

    def __call__(self, parser, namespace, values, option_string=None):
        parser.exit(message=self.message)


def _key_val_type(item):
    try:
        key, val = [i.strip() for i in item.split(":", 1)]
    except:
        raise argparse.ArgumentTypeError(
            "Invalid format '%s'. Use key:val instead." % item
        )

    if not key or not val:
        raise argparse.ArgumentTypeError(
            "Neither the key nor the value can be empty in '%s'." % item
        )

    return (key, val)


def _jobs_type(item):
    jobs_str = item.strip()
    ncpus = 1
    if jobs_str.startswith("cpu"):
        try:
            ncpus = multiprocessing.cpu_count()
        except:
            ncpus = 1

        if jobs_str == "cpu":
            jobs_str = "1"
        else:
            jobs_str = jobs_str[3:]

    try:
        jobs_num = int(jobs_str)
        assert jobs_num > 0
    except:
        raise argparse.ArgumentTypeError(
            "Invalid jobs specification '%s'. Use 'cpu', 'cpu<n>' or <n> (a positive number)."
            % item
        )

    return jobs_num * ncpus


def _show_failures_type(item):
    failures_str = item.strip()
    if failures_str == 'all':
        return failures_str

    try:
        failures_num = int(failures_str)
        assert failures_num >= 0
    except:
        raise argparse.ArgumentTypeError(
            "Invalid show-failures specification '%s'. Use 'all', '0' or <n> (a positive number)."
            % item
        )

    return failures_num


def _true_false_type(answer):
    answer = str(answer).lower()
    if answer in {'yes', 'true', '1', 'y'}:
        return True
    elif answer in {'no', 'false', '0', 'n'}:
        return False
    else:
        raise argparse.ArgumentTypeError(
            "Invalid answer '%s'. Expected 'yes' or 'no'." % answer
        )


class HelpExtraFormatter(argparse.HelpFormatter):
    __hide = True
    EPILOG = "==EPILOG=="

    def __init__(self, *args, **kargs):
        argparse.HelpFormatter.__init__(self, *args, **kargs)
        self.__hidding_section = False

    @classmethod
    def hide(cls):
        cls.__hide = True

    @classmethod
    def unhide(cls):
        cls.__hide = False

    def start_section(self, heading, *args, **kargs):
        if heading == 'Advanced Options' and self.__hide:
            self.__hidding_section = True
        else:
            argparse.HelpFormatter.start_section(self, heading, *args, **kargs)

    def end_section(self, *args, **kargs):
        if self.__hidding_section:
            self.__hidding_section = False
        else:
            argparse.HelpFormatter.end_section(self, *args, **kargs)

    def add_text(self, text, *args, **kargs):
        if not self.__hidding_section:
            if text == self.EPILOG:
                self.__add_examples()
            else:
                argparse.HelpFormatter.add_text(self, text, *args, **kargs)

    def add_argument(self, *args, **kargs):
        if not self.__hidding_section:
            argparse.HelpFormatter.add_argument(self, *args, **kargs)

    def add_arguments(self, *args, **kargs):
        if not self.__hidding_section:
            argparse.HelpFormatter.add_arguments(self, *args, **kargs)

    def add_usage(self, usage, actions, *args, **kargs):
        if self.__hide:
            actions = list(
                filter(
                    lambda a: a.option_strings and not a.option_strings[0].
                    startswith('-x-'), actions
                )
            )
        argparse.HelpFormatter.add_usage(self, usage, actions, *args, **kargs)

    def __add_examples(self):
        def raw_print(text):
            return text

        self.start_section("Examples")
        self._add_item(raw_print, ["  byexample -l python file.py\n"])
        self._add_item(
            raw_print,
            ["  byexample -l python,ruby --ff --timeout=8 file.md\n"]
        )
        self._add_item(
            raw_print, ["  byexample -l python,ruby --show-options\n"]
        )
        self._add_item(raw_print, ["\n"])
        self._add_item(
            raw_print,
            ["See %s for the full documentation\nand more examples.\n" % _url]
        )
        self.end_section()


class _HelpExtraAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if option_string == "-xh":
            HelpExtraFormatter.unhide()
        parser.print_help()
        parser.exit()


def _expand_brace_glob_patterns(filepatterns):
    r''' Expand the given file paths expanding the brace and glob patterns.

        >>> _expand_brace_glob_patterns(['byexample/cmdline.py', 'byexample/runner.py'])
        ['byexample/cmdline.py', 'byexample/runner.py']

        >>> _expand_brace_glob_patterns(['byexample/cmdline.{py,rb}', 'byexample/run*.py'])
        ['byexample/cmdline.py', 'byexample/runner.py']

        Brace expansion (a la Bash) takes place before glob expansion

        >>> _expand_brace_glob_patterns(['byexample/run*.{py,rb}'])
        ['byexample/runner.py']

        Escaping is possible for the brace expansion but escaping
        the glob pattern is not supported (currently, glob.glob
        does not support it)

        >>> _expand_brace_glob_patterns([r'test/ds/file_patterns/foo*'])
        ['test/ds/file_patterns/foo*', 'test/ds/file_patterns/foo{1,2}']

        >>> _expand_brace_glob_patterns([r'test/ds/file_patterns/foo*{1,2}'])
        []

        >>> _expand_brace_glob_patterns([r'test/ds/file_patterns/foo*\{1,2}'])
        ['test/ds/file_patterns/foo{1,2}']

        Escaping the glob pattern is *not* supported and it is *not* defined

        >>> _expand_brace_glob_patterns([r'test/ds/file_patterns/foo\*'])  # just nonsense
        ['test/ds/file_patterns/foo*', 'test/ds/file_patterns/foo{1,2}']

        Expanded paths that end up being empty paths or paths to directories
        are stripped as well as non-existing files.

        >>> _expand_brace_glob_patterns(['byexample/', ''])
        []
    '''
    # imagine the following file patterns:
    #   tmp/a.c     foo/*.{c,cpp,rb}   bar/

    # expand the brace patterns for each file-pattern and get
    #   tmp/a.c     foo/*.c    foo/*.cpp    foo/*.rb     bar/
    gpatterns = itertools.chain.from_iterable(
        bracex.iexpand(f) for f in filepatterns
    )

    # expand the glob patterns into a list of names and get
    #   tmp/a.c     foo/a.c  foo/b.c   ''    foo/r.rb     bar/
    names = itertools.chain.from_iterable(
        glob.iglob(g, recursive=True) for g in gpatterns
    )

    # filter out the names that are empty or are directories and get
    #   tmp/a.c     foo/a.c  foo/b.c    foo/r.rb
    fnames = (f for f in names if f.strip() and not os.path.isdir(f))

    # remove duplicated and return a list
    # we sort the list but the order is undefined (don't assume that)
    return list(sorted(set(fnames)))


class ByexampleArgumentParser(argparse.ArgumentParser):
    def convert_arg_line_to_args(self, arg_line):
        ''' Return a list with the arguments read from a line.

            If in the line there is a flag/argument with one or more
            values the flag may be separated from its value(s) with
            a space and this method will replace it with an '='.

            This is in order to produce a single argument for each
            line as it is expected by argparse.ArgumentParser.

            >>> parser = ByexampleArgumentParser()
            >>> parser.convert_arg_line_to_args('--skip=foo')
            ['--skip=foo']

            >>> parser.convert_arg_line_to_args('--skip foo')
            ['--skip=foo']

            >>> parser.convert_arg_line_to_args('--skip=foo bar')
            ['--skip=foo bar']

            >>> parser.convert_arg_line_to_args('--skip foo bar')
            ['--skip=foo bar']

            >>> parser.convert_arg_line_to_args('--skip=')
            ['--skip=']

            >>> parser.convert_arg_line_to_args('--skip ')
            ['--skip ']

            >>> parser.convert_arg_line_to_args('--skip')
            ['--skip']

            >>> parser.convert_arg_line_to_args('foo')
            ['foo']

            >>> parser.convert_arg_line_to_args('foo bar')
            ['foo bar']

            Empty lines or lines that starts with a # are ignored.

            >>> parser.convert_arg_line_to_args('  ')
            []

            >>> parser.convert_arg_line_to_args(' # foo ')
            []
        '''
        arg_line = arg_line.lstrip()
        if arg_line and arg_line[0] in self.prefix_chars:
            flag, _, value = arg_line.partition(' ')
            value = value.lstrip()
            if not value:
                # the flag is argumentless or it is using '='
                # to paste the flag with its argument,
                # return the whole line then
                #
                # Ex:
                #   -foo
                #   -bar=32
                #   -zaz=
                return [arg_line]
            else:
                if '=' in flag:
                    # the line already has the '=' to paste the
                    # flag with the argument, leave them as they are
                    #
                    # Ex:
                    #   -bar=32 42
                    return [arg_line]

                # Paste the flag with its value (or values) with a '='
                return [flag + '=' + value]

        if arg_line and arg_line[0] == '#':
            return []

        if not arg_line:
            return []

        return [arg_line]

    def error(self, msg):
        if '/--options:' in msg:
            msg += "\nIf you wrote --options -foo, try put an equal like --options=-foo"
            msg += "\nand use quotes if you want to set multiples options like --options='-foo +bar'"

        # note: this self.error method must never return: or
        # we exit the program, or we raise an exception or we
        # call our parent's error method that will not return.
        argparse.ArgumentParser.error(self, msg)


@profile
def parse_args(args=None):
    '''Parse the arguments args and return the them.
       If args is None, parse the sys.argv[1:].
       '''

    DEFAULT_ENC_ERROR_HANDLER = 'strict'

    search_default = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'modules'
    )

    python_version = sys.version.split(' ', 1)[0]
    parser = ByexampleArgumentParser(
        fromfile_prefix_chars='@',
        add_help=False,
        formatter_class=HelpExtraFormatter,
        description=__doc__,
        epilog=HelpExtraFormatter.EPILOG
    )

    parser.add_argument(
        "files",
        nargs='*',
        metavar='<file>',
        help="files that have the examples to run."
    )

    g = parser.add_argument_group("Language Selection")
    g.add_argument(
        "-l",
        "--language",
        "--languages",
        metavar='<languages>',
        dest='languages',
        action=_CSV,
        required=True,
        default=[],
        help='select which languages to parse and run. ' +
        'Comma separated syntax is also accepted.'
    )

    g = parser.add_argument_group("Execution Options")
    g.add_argument(
        "--ff",
        "--fail-fast",
        action='store_true',
        dest='fail_fast',
        help="if an example fails, fail and stop all the execution."
    )
    g.add_argument(
            "--timeout",
            metavar='<secs>',
            default=2,
            type=float,
            help='timeout in seconds to complete each example (%(default)s by default); ' + \
                 'this can be changed per example with this option.')
    g.add_argument(
            "-j",
            "--jobs",
            metavar='<n>',
            default=1,
            type=_jobs_type,
            help='run <n> jobs in parallel (%(default)s by default); ' +\
                 '<n> can be an integer or the string "cpu" or "cpu<n>": ' +\
                 '"cpu" means use all the cpus available; ' +\
                 '"cpu<n>" multiply it by <n> the cpus available.')
    g.add_argument(
        "--dry",
        action='store_true',
        help="do not run any example, only parse them."
    )
    g.add_argument(
        "--skip",
        nargs='+',
        metavar='<file>',
        default=[],
        help='skip these files'
    )
    g.add_argument(
        "--capture-env-var",
        "--capture-env-vars",
        action=_CSV,
        metavar='<var names>',
        default=[],
        dest='captured_env_vars',
        help='capture some environment variables and put them in ' + \
             'the clipboard so they can be pasted and used in ' + \
             'conditional executions. ' + \
             'Comma separated syntax is also accepted.'
    )

    g = parser.add_argument_group("Diff Options")
    g.add_argument(
        "-d",
        "--diff",
        choices=['none', 'unified', 'ndiff', 'context', 'tool'],
        default='none',
        help='select diff algorithm (%(default)s by default).'
    )
    g.add_argument(
            "--difftool",
            metavar='<cmd>',
            dest='difftool',
            default=None,
            help='command line to the external diff program; ' + \
                 'the tokens %%e and %%g are replaced by ' + \
                 'the file names with the expected and the got outputs ' + \
                 'to compare. Enabled only if "--diff tool".')
    g.add_argument(
            "--no-enhance-diff",
            action='store_false',
            dest='enhance_diff',
            help='by default, improves are made so the diff are easier to ' +\
                 'to understand: non-printable characters are visible; ' +\
                 'captured string shown, and more; ' +\
                 'this flag disables all of that.')

    g = parser.add_argument_group("Miscellaneous Options")
    g.add_argument(
        "-o",
        "--options",
        metavar='<options>',
        dest='options_str',
        default="",
        help='add additional options; see --show-options to list them.'
    )
    g.add_argument(
        "--show-options",
        action='store_true',
        help="show the available options for the selected languages (with -l)"
    )
    g.add_argument(
        "-m",
        "--modules",
        action='append',
        metavar='<dir>',
        dest='modules_dirs',
        default=[search_default],
        help='append a directory for searching modules there.'
    )
    g.add_argument(
        "--encoding",
        metavar='<enc>[:<error>]',
        default=sys.stdout.encoding.lower() + ':' + DEFAULT_ENC_ERROR_HANDLER,
        help='select the encoding and optionally the error handler ' +\
             '(default: %(default)s); valid error handlers are ' +\
             '"strict", "ignore" and "replace".'
    )
    g.add_argument(
        "--show-failures",
        metavar='<n>',
        default='all',
        type=_show_failures_type,
        help='show up to <n> failures per file (%(default)s by default) ' +\
             'and suppress the rest (the execution of the examples is not ' +\
             'stopped, only the failures are not shown)'
    )
    g.add_argument(
        "--pretty",
        choices=['none', 'all'],
        default='all',
        help="control how to pretty print the output."
    )
    g.add_argument(
        "--no-progress-bar",
        action='store_true',
        help="do not show the progress bar."
    )
    g.add_argument(
        '-V',
        '--version',
        nargs=0,
        action=_Print,
        message='{prog} {version} (Python {python_version}) - {license}\n\n{doc}'
        '\n\n{license_disclaimer}\nLocation: {loc}\nPackage paths: {paths}\nDependencies: {deps}\n'
        .format(
            prog=parser.prog,
            doc=__doc__,
            version=__version__,
            python_version=python_version,
            license=_license,
            license_disclaimer=_license_disclaimer.format(
                author=_author, url=_url
            ),
            deps=_byexample_dependencies(),
            **_byexample_location(),
        ),
        help='show %(prog)s\'s version and license, then exit'
    )

    g = parser.add_argument_group("Logging")
    mutexg = g.add_mutually_exclusive_group()
    mutexg.add_argument(
        "-v",
        action='count',
        dest='verbosity',
        default=0,
        help="verbosity level, add more flags to increase the level."
    )
    mutexg.add_argument(
        "-q",
        "--quiet",
        action='store_true',
        help="quiet mode, do not print anything even if an example fails; "
        "suppress the progress output."
    )

    g = parser.add_argument_group("Help Options")
    mutexg = g.add_mutually_exclusive_group()
    mutexg.add_argument(
        '-h',
        '--help',
        nargs=0,
        action=_HelpExtraAction,
        help='show this help message and exit'
    )
    mutexg.add_argument(
        '-xh',
        nargs=0,
        action=_HelpExtraAction,
        help=
        "show this help message plus the one for the advanced options and exit"
    )

    g = parser.add_argument_group("Advanced Options")
    g.add_argument(
            "-x-shebang",
            action='append',
            metavar='<runner>:<shebang>',
            dest='shebangs',
            default=[],
            type=_key_val_type,
            help='change the command line of the given <runner> by ' + \
                 '<shebang>; the tokens %%e %%p %%a %%d are replaced by ' + \
                 'the default values for environment, program name, ' + \
                 'arguments and working directory (however no all ' + \
                 'the runners will honor this and some may break).')
    g.add_argument(
        "-x-dfl-timeout",
        metavar="<secs>",
        default=8,
        type=float,
        help='timeout in seconds for internal operations (default: %(default)s).'
    )
    g.add_argument(
        "-x-delaybeforesend",
        metavar="<secs>",
        default=None,
        type=lambda n: None if n == 0 else float(n),
        help=
        "delay in seconds before sending a line to an runner/interpreter; 0 disable this (default)."
    )
    g.add_argument(
        "-x-delayafterprompt",
        metavar="<secs>",
        default=None,
        type=lambda n: None if n == 0 else float(n),
        help=
        "delay in seconds after the prompt to capture more output; 0 disable this (default)."
    )
    g.add_argument(
        "-x-turn-echo-off",
        action='store',
        default=True,
        type=_true_false_type,
        help=
        "turn off the echo on each example execution (if force-echo-filtering is on, the turn-echo-off has no effect); (default: %(default)s)."
    )
    g.add_argument(
        "-x-turn-echo-off-on-spawn",
        action='store',
        default=True,
        type=_true_false_type,
        help=
        "turn off the echo on runner spawn (not affected by force-echo-filtering); (default: %(default)s)."
    )
    g.add_argument(
        "-x-min-rcount",
        metavar="<n>",
        default=16,
        type=int,
        help=
        "minimum match length around a capture tag to perform a guess (default: %(default)s)."
    )
    g.add_argument(
        "-x-not-recover-timeout",
        action='store_true',
        help=
        "do not try to recover from a timeout; abort the execution immediately (beware, this could leave some resources without the proper clean up)."
    )
    g.add_argument(
            "-x-log-mask",
            action='append',
            metavar='<dotted-prefix>:<log-level>',
            dest='log_masks',
            default=[],
            type=_key_val_type,
            help="set the <log-level> of a module named <dotted-prefix> " + \
                 "(ex: byexample.exec.python:chat will put in 'chat' level "+ \
                 "the logs coming from the python execution module.)")
    namespace = parser.parse_args(args)

    # Some extra checks
    # -----------------

    # the languages must be unique
    copy = set(namespace.languages)  # copy of unique languages
    for l in namespace.languages:
        if l not in copy:
            parser.error("argument --languages: '%s' is duplicated." % l)
        copy.remove(l)

    # the shebangs must belong to a language and must be unique
    copy = set(k for k, v in namespace.shebangs)
    for k in (k for k, v in namespace.shebangs):
        if k not in copy:
            parser.error("argument --x-shebang: '%s' is duplicated." % k)
        elif k not in namespace.languages:
            parser.error("argument --x-shebang: runner '%s' is unknown." % k)
        copy.remove(k)

    namespace.shebangs = dict(namespace.shebangs)

    # the log masks must be unique and the levels must be known
    copy = set(k for k, v in namespace.log_masks)
    for k, v in namespace.log_masks:
        if k not in copy:
            parser.error("argument --x-log-mask: '%s' is duplicated." % k)
        copy.remove(k)

    try:
        namespace.log_masks = {
            k: str_to_level(v)
            for k, v in namespace.log_masks
        }
    except KeyError as err:
        k, = err.args
        parser.error(
            "argument --x-log-mask: '%s' is an unknown log level." % k
        )

    # unpack the encoding and its optional error handler and check them
    enc, *enc_error_handler = namespace.encoding.split(':', 1)
    if enc_error_handler:
        enc_error_handler = enc_error_handler[0]
    else:
        enc_error_handler = DEFAULT_ENC_ERROR_HANDLER

    try:
        codecs.lookup_error(enc_error_handler)
    except LookupError:
        parser.error(
            "argument --encoding: error handler '%s' is unknown or unsupported."
            % enc_error_handler
        )

    try:
        codecs.lookup(enc)
    except LookupError:
        parser.error(
            "argument --encoding: encoding '%s' is unknown or unsupported." %
            enc
        )

    namespace.encoding = enc
    namespace.enc_error_handler = enc_error_handler

    # expand the file list based on the brace/glob patterns give (if any)
    namespace.files = _expand_brace_glob_patterns(namespace.files)
    namespace.skip = _expand_brace_glob_patterns(namespace.skip)

    # which files are allowed to be executed: these are the 'testfiles'
    # Note: the order is undefined, we sort them but this is not guaranteed
    # to be like this in the future
    allowed = set(namespace.files) - set(namespace.skip)
    namespace.testfiles = list(
        sorted(f for f in namespace.files if f in allowed)
    )

    # the captured environment variables must be unique
    copy = set(namespace.captured_env_vars)
    for k in namespace.captured_env_vars:
        if k not in copy:
            parser.error(
                "argument --captured-env-vars: '%s' is duplicated." % k
            )
        copy.remove(k)

    # Do not spawn more jobs than testfiles
    namespace.jobs = min(namespace.jobs, len(namespace.testfiles))
    return namespace
