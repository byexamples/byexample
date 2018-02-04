import sys, pkgutil, inspect, pprint

from .options import Options, OptionParser
from .interpreter import Interpreter
from .finder import ExampleFinder, MatchFinder
from .runner import ExampleRunner
from .checker import Checker
from .parser import ExampleParser
from .concern import Concern, ConcernComposite
from .common import log

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

def get_default_options_parser(cmdline_args):
    options_parser = OptionParser(add_help=False, prog='byexample')
    options_parser.add_flag("fail-fast", default=cmdline_args.fail_fast)
    options_parser.add_flag("norm-ws", default=False)
    options_parser.add_flag("pass", default=False)
    options_parser.add_flag("skip", default=False)
    options_parser.add_flag("capture", default=True)
    options_parser.add_flag("enhance-diff", default=cmdline_args.enhance_diff)
    options_parser.add_flag("interact", default=cmdline_args.interact)
    options_parser.add_argument("+timeout", type=int,
                                default=cmdline_args.timeout)
    options_parser.add_argument("+diff", choices=['none', 'unified', 'ndiff', 'context'],
                                default=cmdline_args.diff)

    return options_parser


def get_options(args, cfg):
    # the options_parser should have a set of default values based
    # on the flags and values from the command line.
    optparser = get_default_options_parser(args)

    # we parse the argument 'options' to allow the user to change
    # some options.
    #
    # this argument 'options' will be parsed again later by a parser to
    # extract options that may be more language-specific
    #
    # for this reason we parse this string in a non-strict way as it is
    # possible that the string contains language-specific flags
    options = optparser.parse(args.options_str, strict=False)

    # In order words, the order of preference for a given option is:
    #
    #  scope | preference | source
    #  global  [lowest]     byexample's own default
    #  global    :::        command line
    #  global    :::        argument 'options'
    #  example [highest]    example's options (to be done in the Parser instances)
    #
    # Because this, we pass these to the rest of the system to be used and
    # completed later
    cfg['optparser'] = optparser
    cfg['options']= options

    return options

def init(args):
    encoding = get_encoding(args.encoding, args.verbosity)

    cfg = {
            'use_progress_bar': args.pretty == 'all',
            'use_colors': args.pretty == 'all',
            'quiet':      args.quiet,
            'verbosity':  args.verbosity,
            'encoding':   encoding,
            'output':     sys.stdout,
            'interact':   args.interact,
            'opts_from_cmdline': args.options_str,
            }

    options = get_options(args, cfg)

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

    finder = ExampleFinder(allowed_languages, registry, **cfg)
    runner = ExampleRunner(concerns, checker, **cfg)

    return testfiles, finder, runner, options
