from __future__ import unicode_literals
import sys, argparse, os, multiprocessing
from . import __version__, __doc__, _author, _license, _url, _license_disclaimer

from .log_level import str_to_level


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


def parse_args(args=None):
    '''Parse the arguments args and return the them.
       If args is None, parse the sys.argv[1:].
       '''

    search_default = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'modules'
    )

    python_version = sys.version.split(' ', 1)[0]
    parser = argparse.ArgumentParser(
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
        metavar='<enc>',
        default=sys.stdout.encoding.lower(),
        help='select the encoding (default: %(default)s).'
    )
    g.add_argument(
        "--pretty",
        choices=['none', 'all'],
        default='all',
        help="control how to pretty print the output."
    )
    g.add_argument(
        '-V',
        '--version',
        nargs=0,
        action=_Print,
        message='{prog} {version} (Python {python_version}) - {license}\n\n{doc}'
        '\n\n{license_disclaimer}'.format(
            prog=parser.prog,
            doc=__doc__,
            version=__version__,
            python_version=python_version,
            license=_license,
            license_disclaimer=_license_disclaimer.format(
                author=_author, url=_url
            )
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
                 '<shebang>; the tokens %%e %%p %%a are replaced by ' + \
                 'the default values for environment, program name, ' + \
                 'and arguments (however no all ' + \
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

    # the languages must be uniq
    copy = set(namespace.languages)  # copy of uniqs
    for l in namespace.languages:
        if l not in copy:
            parser.error("argument --languages: '%s' is duplicated." % l)
        copy.remove(l)

    # the shebangs must belong to a language and must be uniq
    copy = set(k for k, v in namespace.shebangs)
    for k in (k for k, v in namespace.shebangs):
        if k not in copy:
            parser.error("argument --x-shebang: '%s' is duplicated." % k)
        elif k not in namespace.languages:
            parser.error("argument --x-shebang: runner '%s' is unknown." % k)
        copy.remove(k)

    namespace.shebangs = dict(namespace.shebangs)

    # the log masks must be uniq and the levels must be known
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

    return namespace
