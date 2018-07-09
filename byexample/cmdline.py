import sys, argparse, os
from . import __version__, __doc__, _author, _license, _url, _license_disclaimer

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
                "Invalid format '%s'. Use key:val instead." % item)

    if not key or not val:
        raise argparse.ArgumentTypeError(
                "Neither the key nor the value can be empty in '%s'." % item)

    return (key, val)

def parse_args(args=None):
    '''Parse the arguments args and return the them.
       If args is None, parse the sys.argv[1:].
       '''

    search_default = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modules')

    parser = argparse.ArgumentParser()
    parser.add_argument('-V', '--version', nargs=0, action=_Print,
            message='{prog} {version} - {license}\n\n{doc}'
                    '\n\n{license_disclaimer}'.format(
                                prog=parser.prog,
                                doc=__doc__,
                                version=__version__,
                                license=_license,
                                license_disclaimer=_license_disclaimer.format(
                                        author=_author,
                                        url=_url)),
                        help='show %(prog)s\'s version and license, then exit')
    parser.add_argument("files", nargs='*', metavar='file',
                        help="file that have the examples to run.")
    parser.add_argument("--ff", "--fail-fast", action='store_true',
                        dest='fail_fast',
                        help="if an example fails, fail and stop all the execution.")
    parser.add_argument("--dry", action='store_true',
                        help="do not run any example, only parse them.")
    parser.add_argument("--skip", nargs='+', metavar='file', default=[],
                        help='skip these files')
    parser.add_argument("-m", "--modules", action='append', metavar='dir',
                        dest='modules_dirs',
                        default=[search_default],
                        help='append a directory for searching modules there.')
    parser.add_argument("-d", "--diff", choices=['none', 'unified', 'ndiff', 'context'],
                        default='none',
                        help='select diff algorithm.')
    parser.add_argument("--no-enhance-diff", action='store_false',
                        dest='enhance_diff',
                        help='by default, improves are made so the diff are easier to ' +\
                             'to understand: non-printable characters are visible; ' +\
                             'captured string shown, and more; ' +\
                             'this flag disables all of that.')
    parser.add_argument("-l", "--language", metavar='language',
                        dest='languages',
                        action=_CSV,
                        required=True,
                        default=[],
                        help='select which languages to parse and run. '+
                             'Comma separated syntax is also accepted.')
    parser.add_argument("--timeout",
                        default=2,
                        type=float,
                        help='timeout in seconds to complete each example (2 by default); ' + \
                             'this can be changed per example with this option.')
    parser.add_argument("-o", "--options",
                        dest='options_str',
                        default="",
                        help='add additional options; see --show-options to list them.')
    parser.add_argument("--show-options", action='store_true',
                        help="show the available options for the selected languages (with -l)")
    parser.add_argument("--encoding",
                        default=sys.stdout.encoding,
                        help='select the encoding (supported in Python 3 only, ' + \
                             'use the same encoding of stdout by default)')
    parser.add_argument("--pretty", choices=['none', 'all'],
                        default='all',
                        help="control how to pretty print the output.")
    parser.add_argument("--interact", "--debug", action='store_true',
                        help="interact with the runner/interpreter manually if an example fails.")
    parser.add_argument("--shebang", action='append', metavar='runner:shebang',
                        dest='shebangs',
                        default=[],
                        type=_key_val_type,
                        help='change the command line of the given <runner> by ' + \
                             '<shebang>; the tokens %%e %%p %%a are replaced by ' + \
                             'the default values for environment, program name, ' + \
                             'and arguments (however no all ' + \
                             'the runners will honor this and some may break).')

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", action='count', dest='verbosity', default=0,
                        help="verbosity level, add more flags to increase the level.")
    group.add_argument("-q", "--quiet", action='store_true',
                        help="quiet mode, do not print anything even if an example fails; "
                             "supress the progress output.")

    namespace = parser.parse_args(args)

    # Some extra checks
    # -----------------

    # the languages must be uniq
    copy = set(namespace.languages) # copy of uniqs
    for l in namespace.languages:
        if l not in copy:
            parser.error("argument --languages: '%s' is duplicated." % l)
        copy.remove(l)

    # the shebangs must belong to a language and must be uniq
    copy = set(k for k, v in namespace.shebangs)
    for k in (k for k, v in namespace.shebangs):
        if k not in copy:
            parser.error("argument --shebang: '%s' is duplicated." % k)
        elif k not in namespace.languages:
            parser.error("argument --shebang: runner '%s' is unknown." % k)
        copy.remove(k)

    namespace.shebangs = dict(namespace.shebangs)

    return namespace


