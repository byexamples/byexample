from __future__ import unicode_literals
import sys, pkgutil, inspect, pprint, os

from .options import Options, OptionParser
from .runner import ExampleRunner
from .finder import ExampleHarvest, ExampleFinder, ZoneDelimiter
from .executor import FileExecutor
from .differ import Differ
from .parser import ExampleParser
from .concern import Concern, ConcernComposite
from .common import enhance_exceptions
from .log import clog, log_context, configure_log_system, setLogLevels, TRACE, DEBUG, CHAT, INFO, NOTE, ERROR, CRITICAL


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
            clog().warn(
                "Class '%s' has not attribute '%s'.", obj.__name__, key_attr
            )

        return class_ok and attr_ok

    return _is_X


@log_context('byexample.load')
def load_modules(dirnames, cfg):
    verbosity = cfg['verbosity']
    registry = {
        'runners': {},
        'finders': {},
        'parsers': {},
        'concerns': {},
        'zdelimiters': {},
    }
    for importer, name, is_pkg in pkgutil.iter_modules(dirnames):
        path = importer.path

        clog().debug("From '%s' loading '%s'...", path, name)

        try:
            module = importer.find_module(name).load_module(name)
        except Exception as e:
            clog().info(
                "From '%s' loading '%s'...failed: %s", path, name, str(e)
            )
            continue

        stability = getattr(module, 'stability', 'undefined')
        if stability not in (
            'experimental', 'provisional', 'unstable', 'stable', 'deprecated'
        ):
            stability = 'experimental/%s?' % str(stability)

        clog().chat("From '%s' loaded '%s' (%s)", path, name, stability)
        for klass, key, what in [
            (ExampleRunner, 'language', 'runners'),
            (ExampleParser, 'language', 'parsers'),
            (ExampleFinder, 'target', 'finders'),
            (ZoneDelimiter, 'target', 'zdelimiters'),
            (Concern, 'target', 'concerns')
        ]:

            # we are interested in any class that is a subclass of 'klass'
            # and it has an attribute 'key'
            predicate = is_a(klass, key, verbosity - 2)

            container = registry[what]
            klasses_found = inspect.getmembers(module, predicate)
            if klasses_found:
                klasses_found = list(zip(*klasses_found))[1]

                # remove already loaded
                klasses_found = set(klasses_found) - set(container.values())

            if klasses_found:
                clog().debug(
                    "Classes found for '%s': %s", what,
                    ', '.join(k.__name__ for k in klasses_found)
                )

            objs = [klass(**cfg) for klass in klasses_found]
            if objs:
                loaded_objs = []
                for obj in objs:
                    key_value = getattr(obj, key)
                    if key_value:
                        if not isinstance(key_value, (list, tuple, set)):
                            key_value = [key_value]

                        for k in key_value:
                            container[k] = obj
                        loaded_objs.append(obj)

                clog().chat(
                    "\n".join((" - %s" % repr(i)) for i in loaded_objs)
                )
            else:
                clog().chat("No classes found for '%s'.", what)

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


def verify_encodings(input_encoding, verbosity):
    if sys.stdout.encoding is None:
        try:
            import locale
            e = (locale.getdefaultlocale()[1] or 'UTF-8')
        except:
            e = 'UTF-8'

        clog().error(
            "The encoding of your terminal is unset.\n" +
            "Try to set the environment variable PYTHONIOENCODING='%s' first\n"
            + "or run 'byexample' like this:\n" +
            "  PYTHONIOENCODING='%s' byexample ...\n", e, e
        )
        sys.exit(-1)

    clog().chat("Encoding (input): %s.", input_encoding)
    clog().chat("Encoding (output): %s.", sys.stdout.encoding)


def geometry(x):
    lines, columns = [int(v.strip()) for v in str(x).split('x')]
    if lines < 0 or columns < 0:
        raise ValueError("Invalid geometry %s" % x)

    return (lines, columns)


def _range(x):
    min, max = [int(v.strip()) for v in str(x).split(':')]
    if min < 0 or max < 0 or min > max:
        raise ValueError("Invalid range %s" % x)

    return (min, max)


def get_default_options_parser(cmdline_args):
    options_parser = OptionParser()
    options_parser.add_flag(
        "fail-fast",
        default=cmdline_args.fail_fast,
        help="if an example fails, fail and stop all the execution."
    )
    options_parser.add_flag(
        "norm-ws", default=False, help="ignore the amount of whitespaces."
    )
    options_parser.add_flag(
        "pass",
        default=False,
        help="run the example but do not check its output."
    )
    options_parser.add_flag(
        "skip", default=False, help="do not run the example."
    )
    options_parser.add_flag(
        "tags", default=True, help="enable the tags <...>."
    )
    options_parser.add_flag(
        "enhance-diff",
        default=cmdline_args.enhance_diff,
        help="improve how the diff are shown."
    )
    options_parser.add_argument(
        "+rm",
        default=[],
        action='append',
        help="remove a character from the got and expected strings."
    )
    options_parser.add_argument(
        "+timeout",
        default=cmdline_args.timeout,
        type=float,
        help="timeout in seconds to complete the example."
    )
    options_parser.add_argument(
        "+diff",
        default=cmdline_args.diff,
        choices=['none', 'unified', 'ndiff', 'context', 'tool'],
        help="select diff algorithm."
    )
    options_parser.add_argument(
        "+geometry",
        default=(24, 80),
        type=geometry,
        help=
        "number of lines and columns of the terminal of the form LxC (default to 24x80)."
    )
    options_parser.add_argument(
        "+term",
        default='dumb',
        choices=['as-is', 'dumb', 'ansi'],
        help=
        "select a terminal emulator to interpret the output (default to 'dumb')."
    )
    options_parser.add_flag(
        "input", default=False, help="enable the input tags [...]"
    )

    options_parser.add_argument(
        "+input-prefix-range",
        default=(6, 12),
        type=_range,
        help=
        "amount of characters that must precede at minimum/maximum an input tag in the form min:max"
    )

    options_parser.add_flag(
        "force-echo-filtering",
        default=False,
        help=
        "each interpreter disables the echo from the terminal but in some cases this cannot be done and an active filtering is required (this is an experimental feature, it will break your tests if no echo is received and it will force a full terminal emulation (see +term=ansi and +geometry))."
    )

    return options_parser


@log_context('byexample.options')
def get_options(args, cfg):
    # the options object should have a set of default values based
    # on the flags and values from the command line.
    options = Options(
        {
            'interact': False,
            'shebangs': args.shebangs,
            'difftool': args.difftool,
        }
    )
    clog().chat("Options (cmdline): %s", options)

    # create a parser for the rest of the options.
    optparser = get_default_options_parser(args)
    options['optparser'] = optparser
    options.update(optparser.defaults())

    clog().chat("Options (cmdline + byexample's defaults): %s", options)
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
    cfg['options'] = options

    clog().chat(
        "Options (cmdline + byexample's defaults + --options): %s", options
    )

    options['x'] = {}
    for k, v in vars(args).items():
        if k.startswith('x_'):
            options['x'][k[2:]] = v

    return options


def show_options(cfg, registry, allowed_languages):
    parsers = [
        p for p in registry['parsers'].values()
        if p.language in allowed_languages
    ]

    concerns = [c for c in registry['concerns'].values()]

    def _title(t, nl=True):
        print(('\n' + t) if nl else t)
        print("-" * len(t))

    _title("byexample's options", nl=False)
    cfg['options']['optparser'].print_help()

    for concern in concerns:
        _title("%s's specific options" % concern.target)
        with enhance_exceptions(
            'Extending the options', concern, cfg['use_colors']
        ):
            concern.get_extended_option_parser(parent_parser=None).print_help()

    for parser in parsers:
        _title("%s's specific options" % parser.language)
        with enhance_exceptions(
            'Extending the options', parser, cfg['use_colors']
        ):
            parser.get_extended_option_parser(parent_parser=None).print_help()


def extend_option_parser_with_concerns(cfg, registry):
    concerns = [c for c in registry['concerns'].values()]

    # join the concerns' option parser into one single parser
    # starting from the byexample's one
    optparser = cfg['options']['optparser']
    for concern in concerns:
        with enhance_exceptions(
            'Extending the options', concern, cfg['use_colors']
        ):
            # update the options with the concerns's default ones and
            # only with them; only after this merge concerns's parser with
            # the previous parser
            concern_optparser = concern.get_extended_option_parser(
                parent_parser=None
            )
            cfg['options'].update(concern_optparser.defaults())

            optparser = concern.get_extended_option_parser(optparser)

    cfg['options']['optparser'] = optparser
    return optparser


@log_context('byexample.options')
def extend_options_with_language_specific(cfg, registry, allowed_languages):
    parsers = [
        p for p in registry['parsers'].values()
        if p.language in allowed_languages
    ]

    # update the defaults for all the parsers
    for parser in parsers:
        with enhance_exceptions(
            'Extending the options', parser, cfg['use_colors']
        ):
            parser_optparser = parser.get_extended_option_parser(
                parent_parser=None
            )
            cfg['options'].update(parser_optparser.defaults())

    # update again but with the options that *may* had set in the command line
    for parser in parsers:
        opts = parser.extract_cmdline_options(cfg['opts_from_cmdline'])
        cfg['options'].update(opts)

    clog().chat(
        "Options (cmdline + --options + language specific): %s", cfg['options']
    )


def verbosity_to_log_levels(verbosity, quiet):
    if quiet:
        return {'byexample': CRITICAL}

    tmp = [
        {
            'byexample': NOTE
        },
        {
            'byexample': NOTE,
            'byexample.exec': INFO
        },  # -v
        {
            'byexample': NOTE,
            'byexample.exec': CHAT
        },  # -vv
        {
            'byexample': INFO,
            'byexample.exec': CHAT
        },  # -vvv
        {
            'byexample': CHAT
        },  # -vvvv
        {
            'byexample': DEBUG
        },  # -vvvvv
        {
            'byexample': TRACE
        },  # -vvvvvv
    ]

    return tmp[min(verbosity, len(tmp) - 1)]


@log_context('byexample.init')
def init(args):
    lvl = verbosity_to_log_levels(args.verbosity, args.quiet)
    lvl.update(args.log_masks)
    setLogLevels(lvl)

    verify_encodings(args.encoding, args.verbosity)
    cfg = {
        'use_progress_bar': args.pretty == 'all',
        'use_colors': args.pretty == 'all',
        'quiet': args.quiet,
        'verbosity': args.verbosity,
        'encoding': args.encoding,
        'output': sys.stdout,
        'interact': False,
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

    if not testfiles:
        if not cfg['quiet']:
            clog().error(
                "No files were found (you passed %i files and %i were skipped)",
                (len(set(args.files)), len(set(args.files) - allowed_files))
            )
        sys.exit(1)

    # extend the option parser with all the parsers of the concerns.
    # do this *after* showing the options so we can show each parser's opt
    # separately
    extend_option_parser_with_concerns(cfg, registry)

    # now that we know what languages are allowed, extend the options
    # for them
    extend_options_with_language_specific(cfg, registry, allowed_languages)

    if cfg['quiet']:
        registry['concerns'].pop('progress', None)

    if not clog().isEnabledFor(CHAT):
        clog().chat("Options:\n%s.", pprint.pformat(cfg['options']))

    clog().chat("Configuration:\n%s.", pprint.pformat(cfg))
    clog().chat("Registry:\n%s.", pprint.pformat(registry))

    concerns = ConcernComposite(registry, **cfg)

    differ = Differ(**cfg)

    harvester = ExampleHarvest(allowed_languages, registry, **cfg)
    executor = FileExecutor(concerns, differ, **cfg)

    configure_log_system(use_colors=cfg['use_colors'], concerns=concerns)
    return testfiles, harvester, executor, options
