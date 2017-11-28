import sys, argparse, os, pkgutil, inspect

from .options import Options
from .parser import ExampleMultiParser
from .runner import ExampleRunner, Checker
from .reporter import SimpleReporter
from .common import log, build_exception_msg

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
    parser.add_argument("-d", "--diff", choices=['unified', 'ndiff', 'context'],
                        help='select diff algorithm.')
    parser.add_argument("-i", "--interpreters", action='append', metavar='interpreter',
                        default=[], # all by default
                        help='select which interpreters to use (all by default).')
    parser.add_argument("--encoding",
                        default=sys.stdout.encoding,
                        help='select the encoding (supported in Python 3 only, ' + \
                             'use the same enconding of stdout by default)')
    parser.add_argument("--no-color", action='store_true',
                        help="do not output any escape sequence for coloring.")

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

def search_interprerters(dirnames, allowed_interpreters, verbosity, encoding):
    interpreters = []
    for importer, name, is_pkg in pkgutil.iter_modules(dirnames):
        path = importer.path

        # if we have a whitelist of allowed interpreters, do not load
        # a module if it is not there
        if allowed_interpreters and name not in allowed_interpreters:
            log("From '%s' found '%s' but it was blacklisted. Skip." %
                                                    (path, name), verbosity-2)
            continue

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

    return [klass(verbosity, encoding) for klass in interpreters]

def get_encoding(encoding, verbosity):
    if sys.version_info[0] <= 2: # version major
        # we don't support a different encoding
        encoding = None

    log("Encoding: %s." % encoding, verbosity-2)
    return encoding

def main():
    args = parse_args()

    encoding = get_encoding(args.encoding, args.verbosity)
    available_interpreters = search_interprerters(args.search, args.interpreters,
                                                  args.verbosity, encoding)

    allowed_files = set(args.files) - set(args.skip)
    testfiles = [f for f in args.files if f in allowed_files]

    reporter = SimpleReporter(sys.stdout, not args.no_color,
                              args.quiet, args.verbosity)
    checker  = Checker()
    options  = Options(FAIL_FAST=args.fail_fast, WS=False, PASS=False,
                       SKIP=False, H=True, TIMEOUT=2,
                       UDIFF=args.diff=='unified',
                       NDIFF=args.diff=='ndiff',
                       CDIFF=args.diff=='context'
                       )


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
