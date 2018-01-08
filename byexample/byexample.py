import sys, argparse, os, pkgutil, inspect, pprint

from .options import Options
from .interpreter import Interpreter
from .finder import ExampleFinder, MatchFinder
from .runner import ExampleRunner, Checker
from .parser import ExampleParser
from .concern import Concern, ConcernComposite
from .common import log, build_exception_msg

from . import __version__

def parse_args():
    class CSV(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            # -l a,b  => [a, b]
            values = values.split(',')
            getattr(namespace, self.dest).extend(values)

    class DictExtend(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            assert isinstance(values, dict)
            getattr(namespace, self.dest).update(values)

    def key_val_type(item):
        try:
            key, val = [i.strip() for i in item.split("=", 1)]
            option = {key: val}
        except:
            raise argparse.ArgumentTypeError(
                    "Invalid option format '%s'. Use key=val instead." % item)

        if not key or not val:
            raise argparse.ArgumentTypeError(
                    "Neither the key nor the value of the option can be empty in '%s'." % item)

        return option

    search_default = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modules')
    parser = argparse.ArgumentParser()
    parser.add_argument('-V', '--version', action='version',
                        version='%(prog)s {version}'.format(version=__version__))
    parser.add_argument("files", nargs='+', metavar='file',
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
                        help='by default, some non-printable characters are replaced ' +\
                             'by printable ones in the diffs to make them easier to spot; ' +\
                             'this flag disables that.')
    parser.add_argument("-l", "--language", metavar='language',
                        dest='languages',
                        action=CSV,
                        required=True,
                        default=[],
                        help='select which languages to parse and run. '+
                             'Comma separated syntax is also accepted.')
    parser.add_argument("--timeout",
                        default=2,
                        type=int,
                        help='timeout in seconds to complete each example (2 by default); ' + \
                             'this can be changed per example with TIMEOUT option.')
    parser.add_argument("-o", "--option",
                        dest='options',
                        action=DictExtend,
                        type=key_val_type,
                        default={},
                        help='add additional options of the form key=val.')
    parser.add_argument("--encoding",
                        default=sys.stdout.encoding,
                        help='select the encoding (supported in Python 3 only, ' + \
                             'use the same encoding of stdout by default)')
    parser.add_argument("--pretty", choices=['none', 'all'],
                        default='all',
                        help="control how to pretty print the output.")
    parser.add_argument("--interact", "--debug", action='store_true',
                        help="interact with the interpreter manually if an example fails.")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", action='count', dest='verbosity', default=0,
                        help="verbosity level, add more flags to increase the level.")
    group.add_argument("-q", "--quiet", action='store_true',
                        help="quiet mode, do not print anything even if an example fails; "
                             "supress the progress output.")

    return parser.parse_args()

def is_a(target_class, key_attr):
    '''
    Returns a function that will return True if its argument
    is a subclass of target_class and it has the attribute key_attr
    '''
    def _is_X(obj):
        if not inspect.isclass(obj):
            return False

        return issubclass(obj, target_class) and \
               obj is not target_class and \
               hasattr(obj, key_attr)

    return _is_X

def load_modules(dirnames, cfg):
    verbosity = cfg['verbosity']
    registry = {'interpreters': {},
                'finders': {},
                'parsers': {},
                'concerns': {},
                }
    for importer, name, is_pkg in pkgutil.iter_modules(dirnames):
        path = importer.path

        log("From '%s' loading '%s'..." % (path, name), verbosity-2)

        try:
            module = importer.find_module(name).load_module(name)
        except Exception as e:
            log("From '%s' loading '%s'...failed: %s" % (path, name, str(e)),
                                                        verbosity-2)
            continue

        log("From '%s' loaded '%s'" % (path, name), verbosity-1)
        for klass, key, what in [(Interpreter, 'language', 'interpreters'),
                                 (ExampleParser, 'language', 'parsers'),
                                 (MatchFinder, 'target', 'finders'),
                                 (Concern, 'target', 'concerns')]:

            # we are interested in any class that is a subclass of 'klass'
            # and it has an attribute 'key'
            predicate = is_a(klass, key)

            container = registry[what]
            klasses_found = inspect.getmembers(module, predicate)
            if klasses_found:
                klasses_found = list(zip(*klasses_found))[1]

                # remove already loaded
                klasses_found = set(klasses_found) - set(container.values())

            objs = [klass(**cfg) for klass in klasses_found]
            if objs:
                loaded_objs = []
                for obj in objs:
                    key_value = getattr(obj, key)
                    if key_value:
                        container[key_value] = obj
                        loaded_objs.append(obj)

                log("\n".join((" - %s" % repr(i)) for i in loaded_objs), verbosity-1)

    return registry

def get_allowed_languages(registry, selected):
    available = set([obj.language for obj in registry['interpreters'].values()] + \
                      [obj.language for obj in registry['parsers'].values()])

    selected = set(selected)
    not_found = selected - available

    if not_found:
        not_found = ', '.join(not_found)
        raise ValueError(("The following languages were specified " + \
                          "but they were not found in any module:\n -> %s\n" + \
                          "May be you forgot to add another place where to " + \
                          "find it with -m or --modules.\nRun again with -vvv to get " + \
                          "more information about why is this happening.") %
                               not_found)
    return selected

def get_encoding(encoding, verbosity):
    if sys.version_info[0] <= 2: # version major
        # we don't support a different encoding
        encoding = None

    log("Encoding: %s." % encoding, verbosity-2)
    return encoding

def main():
    args = parse_args()

    encoding = get_encoding(args.encoding, args.verbosity)

    cfg = {
            'use_progress_bar': args.pretty == 'all',
            'use_colors': args.pretty == 'all',
            'quiet':      args.quiet,
            'verbosity':  args.verbosity,
            'encoding':   encoding,
            'output':     sys.stdout,
            'interact':   args.interact,
            }

    # if the output is not atty, disable the color anyways
    cfg['use_colors'] &= cfg['output'].isatty()

    registry = load_modules(args.modules_dirs, cfg)

    allowed_languages = get_allowed_languages(registry, args.languages)

    allowed_files = set(args.files) - set(args.skip)
    testfiles = [f for f in args.files if f in allowed_files]

    if cfg['quiet']:
        registry['concerns'].pop('progress', None)

    log("Configuration:\n%s." % pprint.pformat(cfg), cfg['verbosity']-2)
    log("Registry:\n%s." % pprint.pformat(registry), cfg['verbosity']-2)

    concerns = ConcernComposite(registry, **cfg)

    checker  = Checker(**cfg)
    options  = Options(FAIL_FAST=args.fail_fast, WS=False, PASS=False,
                       SKIP=False, ENHANCE_DIFF=args.enhance_diff,
                       TIMEOUT=args.timeout,
                       UDIFF=args.diff=='unified',
                       NDIFF=args.diff=='ndiff',
                       CDIFF=args.diff=='context',
                       INTERACT=args.interact
                       )

    options.up(args.options)

    finder = ExampleFinder(allowed_languages, registry, **cfg)
    runner = ExampleRunner(concerns, checker, **cfg)

    exit_status = 0
    for filename in testfiles:
        examples = finder.get_examples_from_file(options, filename)
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
