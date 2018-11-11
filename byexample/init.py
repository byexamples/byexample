import sys, pkgutil, inspect, pprint, os

from .options import Options, OptionParser
from .runner import ExampleRunner
from .finder import ExampleHarvest, ExampleFinder
from .executor import FileExecutor
from .differ import Differ
from .parser import ExampleParser
from .concern import Concern, ConcernComposite
from .common import log

def are_tty_colors_supported(output):
    def get_colors():
        try:
            import curses
            curses.setupterm()
            return int(curses.tigetnum('colors'))
        except:
            # assume that we have a terminal with color support
            return 8

    # assume that colors are enabled by default iff:
    # - the output is a TTY terminal (the output is not a redirection
    #   to a file or pipe for example)
    # - the terminal name (TERM) has not the 'm' suffix like xterm-m
    #   (see term(7) for more terminal names conventions)
    # - ncurses queries the terminal and it says that colors are supported
    #   and it has 8 or more colors.
    #
    # the order is important because, for example, the value of TERM is
    # more relevant: the terminal may have support for colors but if TERM
    # has the -m suffix, we should honor that; the user may relay on this.
    return output.isatty() and \
           'm' not in os.getenv('TERM', '').split('-') and \
           get_colors() >= 8

def is_a(target_class, key_attr, warn_missing_key_attr):
    '''
    Returns a function that will return True if its argument
    is a subclass of target_class and it has the attribute key_attr

    If warn_missing_key_attr is True, log a warning if the "the argument"
    is a subclass of target_class but it has not the attribute
    key_attr.
    '''
    def _is_X(obj):
        if not inspect.isclass(obj):
            return False

        class_ok = issubclass(obj, target_class) and \
               obj is not target_class

        attr_ok = hasattr(obj, key_attr)

        if class_ok and not attr_ok:
            log(" * Warning: class '%s' has not attribute '%s'." % \
                    (obj.__name__, key_attr),  0)

        return class_ok and attr_ok

    return _is_X

def load_modules(dirnames, cfg):
    verbosity = cfg['verbosity']
    registry = {'runners': {},
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
                                                        verbosity)
            continue

        stability = getattr(module, 'stability', 'undefined')
        if stability not in ('experimental', 'provisional', 'unstable', 'stable', 'deprecated'):
            stability = 'experimental/%s?' % str(stability)

        log("From '%s' loaded '%s' (%s)" % (path, name, stability), verbosity-1)
        for klass, key, what in [(ExampleRunner, 'language', 'runners'),
                                 (ExampleParser, 'language', 'parsers'),
                                 (ExampleFinder, 'target', 'finders'),
                                 (Concern, 'target', 'concerns')]:

            # we are interested in any class that is a subclass of 'klass'
            # and it has an attribute 'key'
            predicate = is_a(klass, key, verbosity-2)

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
    available = set([obj.language for obj in registry['runners'].values()] + \
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

def _float_zero_to_none(x):
    if x == 0:
        return None

    return float(x)

def geometry(x):
    lines, columns = [int(v.strip()) for v in str(x).split('x')]
    if lines < 0 or columns < 0:
        raise ValueError("Invalid geometry %s" % x)

    return (lines, columns)

def get_default_options_parser(cmdline_args):
    options_parser = OptionParser()
    options_parser.add_flag("fail-fast", help="if an example fails, fail and stop all the execution.")
    options_parser.add_flag("norm-ws", help="ignore the amount of whitespaces.")
    options_parser.add_flag("pass", help="run the example but do not check its output.")
    options_parser.add_flag("skip", help="do not run the example.")
    options_parser.add_flag("tags", help="enable the tags <...>.")
    options_parser.add_flag("enhance-diff", help="improve how the diff are shown.")
    options_parser.add_flag("interact", help="interact with the runner/interpreter manually if an example fails.")
    options_parser.add_argument("+rm", action='append', help="remove a character from the got and expected strings.")
    options_parser.add_argument("+timeout", type=float, help="timeout in seconds to complete the example.")
    options_parser.add_argument("+diff", choices=['none', 'unified', 'ndiff', 'context'],
                                        help="select diff algorithm.")
    options_parser.add_argument("+delaybeforesend", type=_float_zero_to_none,
                                    help="delay in seconds before sending a line to an runner/interpreter; 0 disable this (default).")
    options_parser.add_argument("+geometry", type=geometry,
                                    help="number of lines and columns of the terminal of the form LxC (default to 24x80).")

    return options_parser


def get_options(args, cfg):
    # the options object should have a set of default values based
    # on the flags and values from the command line.
    options = Options({ 'fail_fast': args.fail_fast,
                        'norm_ws': False,
                        'pass': False,
                        'skip': False,
                        'tags': True,
                        'rm': [],
                        'enhance_diff': args.enhance_diff,
                        'interact': args.interact,
                        'timeout': args.timeout,
                        'diff': args.diff,
                        'delaybeforesend': None,
                        'shebangs': args.shebangs,
                        'geometry': (24, 80)
                        })
    log("Options (cmdline): %s" % options, cfg['verbosity']-2)

    # create a parser for the rest of the options.
    optparser = get_default_options_parser(args)
    options['optparser'] = optparser

    # we parse the argument 'options' to allow the user to change
    # some options.
    #
    # this argument 'options' will be parsed again later by a parser to
    # extract options that may be more language-specific
    #
    # for this reason we parse this string in a non-strict way as it is
    # possible that the string contains language-specific flags
    options.up(optparser.parse(args.options_str, strict=False))

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
    cfg['options']= options

    log("Options (cmdline + --options): %s" % options, cfg['verbosity']-2)
    return options

def show_options(cfg, registry, allowed_languages):
    parsers = [p for p in registry['parsers'].values()
               if p.language in allowed_languages]

    concerns = [c for c in registry['concerns'].values()]

    def _title(t, nl=True):
        print(('\n' + t) if nl else t)
        print("-" * len(t))

    _title("byexample's options", nl=False)
    cfg['options']['optparser'].print_help()

    for concern in concerns:
        _title("%s's specific options" % concern.target)
        concern.get_extended_option_parser(parent_parser=None).print_help()

    for parser in parsers:
        _title("%s's specific options" % parser.language)
        parser.get_extended_option_parser(parent_parser=None).print_help()

def extend_option_parser_with_concerns(cfg, registry):
    concerns = [c for c in registry['concerns'].values()]

    # join the concerns' option parser into one single parser
    # starting from the byexample's one
    optparser = cfg['options']['optparser']
    for concern in concerns:
        optparser = concern.get_extended_option_parser(optparser)

    cfg['options']['optparser'] = optparser
    return optparser

def extend_options_with_language_specific(cfg, registry, allowed_languages):
    parsers = [p for p in registry['parsers'].values()
               if p.language in allowed_languages]

    for parser in parsers:
        opts = parser.extract_cmdline_options(cfg['opts_from_cmdline'])
        cfg['options'].update(opts)

    log("Options (cmdline + --options + language specific): %s" % cfg['options'],
            cfg['verbosity']-2)

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

    allowed_files = set(args.files) - set(args.skip)
    testfiles = list(sorted(f for f in args.files if f in allowed_files))

    # Do not spawn more jobs than testfiles
    args.jobs = cfg['jobs'] = min(args.jobs, len(testfiles))

    options = get_options(args, cfg)

    # if the output has not color support, disable the color anyways
    cfg['use_colors'] &= are_tty_colors_supported(cfg['output'])

    registry = load_modules(args.modules_dirs, cfg)

    allowed_languages = get_allowed_languages(registry, args.languages)

    if args.show_options:
        show_options(cfg, registry, allowed_languages)
        sys.exit(0)

    # extend the option parser with all the parsers of the concerns.
    # do this *after* showing the options so we can show each parser's opt
    # separately
    extend_option_parser_with_concerns(cfg, registry)

    # now that we know what languages are allowed, extend the options
    # for them
    extend_options_with_language_specific(cfg, registry, allowed_languages)

    if cfg['quiet']:
        registry['concerns'].pop('progress', None)

    log("Configuration:\n%s." % pprint.pformat(cfg), cfg['verbosity']-2)
    log("Registry:\n%s." % pprint.pformat(registry), cfg['verbosity']-2)

    concerns = ConcernComposite(registry, **cfg)

    differ = Differ(**cfg)

    harvester = ExampleHarvest(allowed_languages, registry, **cfg)
    executor  = FileExecutor(concerns, differ, **cfg)

    return testfiles, harvester, executor, options
