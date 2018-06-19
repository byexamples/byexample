import sys, argparse, os
from . import __version__, __doc__, _author, _license, _url, _license_disclaimer
from .cmdline import _Print
from .common import human_exceptions
from .differ import Differ
from .options import Options

doc = 'Compare files and make the differences more human-understandable.'

def parse_args(args=None):
    '''Parse the arguments args and return the them.
       If args is None, parse the sys.argv[1:].
       '''

    parser = argparse.ArgumentParser()
    parser.add_argument('-V', '--version', nargs=0, action=_Print,
            message='{prog} - byexample {version}\'s spin-off - {license}\n\n{doc}'
                    '\n\n{license_disclaimer}'.format(
                                prog=parser.prog,
                                doc=doc,
                                version=__version__,
                                license=_license,
                                license_disclaimer=_license_disclaimer.format(
                                        author=_author,
                                        url=_url)),
                        help='show %(prog)s\'s version and license, then exit')
    parser.add_argument("file", nargs='+',
                        help="files to compare of the form: 'file1 file2'. " +\
                             "If --to-file or --from-file is given, there is " +\
                             "no restriction on the argument.")
    parser.add_argument("-d", "--diff", choices=['none', 'unified', 'ndiff', 'context'],
                        default='ndiff',
                        help='select diff algorithm.')
    parser.add_argument("--no-enhance-diff", action='store_false',
                        dest='enhance_diff',
                        help='by default, improves are made so the diff are easier to ' +\
                             'to understand: non-printable characters are visible; ' +\
                             'this flag disables all of that.')
    parser.add_argument("--encoding",
                        default=sys.stdout.encoding,
                        help='select the encoding (supported in Python 3 only, ' + \
                             'use the same encoding of stdout by default)')
    parser.add_argument("--pretty", choices=['none', 'all'],
                        default='all',
                        help="control how to pretty print the output.")
    parser.add_argument("-q", "--quiet", action='store_true',
                        help="quiet mode, do not print anything even if " +\
                             "there are differences.")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--from-file",
                        help="compare this file against the rest of the files.")
    group.add_argument("--to-file",
                        help="compare all the files against this one.")

    args = parser.parse_args(args)
    assert not (args.to_file is not None and args.from_file is not None)

    if args.from_file is None and args.to_file is None:
        if len(args.file) != 2:
            if len(args.file) > 2:
                parser.error("too many files to compare")
            else:
                parser.error("too few files to compare")

        args.file_duples = [tuple(args.file)]

    elif args.from_file is not None:
        args.file_duples = [(args.from_file, f) for f in args.file]
    else:
        args.file_duples = [(f, args.to_file) for f in args.file]

    assert hasattr(args, 'file_duples')
    return args


class Status:
    ok = 0
    failed = 1
    error = 2

def read_file(filename):
    return open(filename, 'rtU').read()

def init(args):
    encoding = None if sys.version_info[0] <= 2 else args.encoding

    cfg = {
            'use_colors': args.pretty == 'all',
            'quiet':      args.quiet,
            'verbosity':  0,
            'encoding':   encoding,
            'output':     sys.stdout,
            }

    # if the output is not atty, disable the color anyways
    cfg['use_colors'] &= cfg['output'].isatty()

    differ  = Differ(**cfg)

    options = Options({
                'use_colors': cfg['use_colors'],
                'enhance_diff': args.enhance_diff,
                'diff': args.diff
                })

    return args.file_duples, differ, options

def main(args=None):
    args = parse_args(args)
    human_args = (0, args.quiet, Status.error)
    with human_exceptions('During the initialization phase:', *human_args):
        file_duples, differ, options = init(args)

    exit_status = Status.ok
    for from_f, to_f in file_duples:
        with human_exceptions("Files '%s' and '%s':" % (from_f, to_f), *human_args):
            expected = read_file(from_f)
            got = read_file(to_f)

            if expected != got:
                if not args.quiet:
                    print("Differences found between files '%s' and '%s':" % (from_f, to_f))

                    diff = differ.output_difference(expected,
                                                     got,
                                                     options,
                                                     options['use_colors'])
                    print(diff)

                exit_status = max(exit_status, Status.failed)

    return exit_status

