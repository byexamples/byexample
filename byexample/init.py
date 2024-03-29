from __future__ import unicode_literals
import sys, pkgutil, inspect, pprint, os, operator, traceback, functools
import importlib.util

from itertools import chain as chain_iters

from .options import Options, OptionParser
from .runner import ExampleRunner
from .finder import ExampleHarvest, ExampleFinder, ZoneDelimiter
from .executor import FileExecutor
from .differ import Differ
from .parser import ExampleParser
from .concern import Concern, ConcernComposite
from .common import enhance_exceptions
from .log import clog, log_context, configure_log_system, setLogLevels, TRACE, DEBUG, CHAT, INFO, NOTE, ERROR, CRITICAL, init_thread_specific_log_system, log_with
from .prof import profile
from .cfg import Config
from .cmdline import _show_failures_type


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


def is_a(target_class):
    '''
    Returns a function that will return True if its argument
    is a subclass of target_class.
    '''
    def _is_X(obj):
        if not inspect.isclass(obj):
            return False

        class_ok = issubclass(obj, target_class) and \
               obj is not target_class

        return class_ok

    return _is_X


class NS:
    def __setattr__(self, name, val):
        if name[0] == '_':
            raise AttributeError(
                "You cannot store 'private' attributes (the ones that starts with underscore)."
            )

        return object.__setattr__(self, name, val)

    def _attribute_names(self):
        return frozenset(k for k in dir(self) if k[0] != '_')

    def _as_dict(self):
        return {k: getattr(self, k) for k in self._attribute_names()}

    def _is_empty(self):
        return not bool(self._attribute_names())


def import_and_register_modules_iter(dirnames):
    ''' Import and register the (python) modules located in the given
        directories.

        The loaded modules will be registered and accessible
        from sys.modules as any imported python module.

        This function will not try to instantiate any
        object from the loaded modules.

        Moreover, this function will not assume that it is running
        in the main process of byexample so it will not use anything
        from byexample's runtime like clog() as this function may
        be called by a child process.
    '''
    for importer, name, is_pkg in pkgutil.iter_modules(dirnames):
        path = importer.path
        err = None

        try:
            spec = importer.find_spec(name)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            sys.modules[name] = module

        except Exception as e:
            err = e

        yield (path, name, module, err)


class InvalidExtension(Exception):
    def __init__(self, path, name, msg):
        Exception.__init__(
            self, f"From '{os.path.abspath(path)}' module '{name}'\n{msg}"
        )


@log_context('byexample.load')
@profile
def load_modules(dirnames, cfg, sharer):
    verbosity = cfg['verbosity']
    registry = {
        'runners': {},
        'finders': {},
        'parsers': {},
        'concerns': {},
        'zdelimiters': {},
    }

    MULTI_VALUED_KEY_ATTR_TYPES = (list, tuple, set)
    namespaces_by_class = {}
    for path, name, module, err in import_and_register_modules_iter(dirnames):
        if err:
            clog().exception(
                "From '%s' loading module '%s' failed. Skipping.",
                os.path.abspath(path),
                name,
                exc_info=err
            )
            continue

        stability = getattr(module, 'stability', 'undefined')
        if stability not in (
            'experimental', 'provisional', 'unstable', 'stable', 'deprecated',
            'unsupported'
        ):
            stability = 'experimental/%s?' % str(stability)

        clog().chat(
            "From '%s' loaded module '%s' (%s). Searching for extensions...",
            path, name, stability
        )

        for extension_class, attr_key, is_multikey, what in [
            (ExampleRunner, 'language', False, 'runners'),
            (ExampleParser, 'language', False, 'parsers'),
            (ExampleFinder, 'target', False, 'finders'),
            (ZoneDelimiter, 'target', True, 'zdelimiters'),
            (Concern, 'target', False, 'concerns')
        ]:

            # we are interested in any class that is a subclass of 'extension_class'
            predicate = is_a(extension_class)

            container = registry[what]
            klasses_found = inspect.getmembers(module, predicate)
            if klasses_found:
                klasses_found = list(zip(*klasses_found))[1]

                # remove already loaded
                not_loaded_yet = set(klasses_found) - set(container.values())

                # preserve class order based on where they were found
                # by inspect.getmembers
                klasses_found = [
                    cls for cls in klasses_found if cls in not_loaded_yet
                ]

            if klasses_found:
                clog().debug(
                    "Classes found for '%s': %s", what,
                    ', '.join(k.__name__ for k in klasses_found)
                )

            objs = []
            for klass in klasses_found:
                ns = NS()  # a private namespace for each object
                try:
                    obj = klass(ns=ns, sharer=sharer, cfg=cfg, **cfg)
                except Exception as err:
                    raise InvalidExtension(
                        path, name,
                        f"Instantiation of {klass.__name__} failed: {str(err)}"
                    ) from err

                # If the extension class forgot to call Extension.__init__, we raise
                # an exception here.
                if not obj._was_extension_init_called():
                    raise InvalidExtension(
                        path, name,
                        f"The object of class {klass.__name__} did not call the constructor of {extension_class.__name__}."
                    )

                # We allow for a class to not define its attr_key attribute (target/language) but
                # it must be defined after the instantiation and initialization of the
                # extension object. No excuses.
                if not hasattr(obj, attr_key):
                    raise InvalidExtension(
                        path, name,
                        f"The object of class {klass.__name__} did not define a '{attr_key}' attribute."
                    )

                # Check for attr_key's value type if it is not None.
                attr_key_value = getattr(obj, attr_key)
                if attr_key_value is not None:
                    if is_multikey and not isinstance(
                        attr_key_value, (str, ) + MULTI_VALUED_KEY_ATTR_TYPES
                    ):
                        raise InvalidExtension(
                            path, name,
                            "The attribute '%s' of %s must be a string-like value or a list of strings but it is of type %s."
                            % (
                                attr_key, obj.__class__.__name__,
                                type(attr_key_value)
                            )
                        )
                    elif not is_multikey and not isinstance(
                        attr_key_value, str
                    ):
                        raise InvalidExtension(
                            path, name,
                            "The attribute '%s' of %s must be a single string-like value but it is of type %s."
                            % (
                                attr_key, obj.__class__.__name__,
                                type(attr_key_value)
                            )
                        )

                objs.append(obj)
                if not ns._is_empty():
                    # keep a reference of the namespace only if
                    # it is not empty (because they are immutable from now on,
                    # an empty namespace will remain empty and it will not
                    # have any value for use)
                    namespaces_by_class[klass] = ns

            if objs:
                loaded_objs = []
                for obj in objs:
                    key_value = getattr(obj, attr_key)
                    if key_value is not None:
                        if is_multikey:
                            # ensure that the attr_key is list-like iterable
                            # (we accept a multi-valued attr_key)
                            if not isinstance(key_value, (list, tuple, set)):
                                assert isinstance(key_value, str)
                                key_value = {key_value}
                            else:
                                tmp = set(key_value)
                                if len(tmp) < len(key_value):
                                    clog().warn(
                                        f"Extension {obj.__class__.__name__} has duplicated entries in its '{attr_key}' attribute."
                                    )
                                elif not tmp:
                                    clog().warn(
                                        f"Extension {obj.__class__.__name__} has no entries in its '{attr_key}' attribute. If is intentional, prefer to set None instead."
                                    )
                                    # Stop this iteration and continue with the for-loop in this case
                                    continue
                                key_value = tmp
                        else:
                            assert isinstance(key_value, str)
                            # for simplicity we see this single-valued string
                            # as a singleton set
                            key_value = {key_value}

                        assert isinstance(key_value, set)
                        assert (is_multikey and len(key_value) >= 1
                                ) or (not is_multikey and len(key_value) == 1)
                        for k in key_value:
                            container[k] = obj
                        loaded_objs.append(obj)

                clog().chat(
                    "\n".join((" - %s" % repr(i)) for i in loaded_objs)
                )
            else:
                clog().chat("No classes found for '%s'.", what)

    return registry, namespaces_by_class


def get_allowed_languages(registry, flavors):
    runners = registry['runners'].values()
    parsers = registry['parsers'].values()

    flavor2lang = {
        f: obj.language
        for obj in chain_iters(runners, parsers)
        for f in set(obj.flavors) | set([obj.language])
    }

    available_flavors = set(flavor2lang.keys())
    flavors = set(flavors)

    not_found = flavors - available_flavors

    if not_found:
        not_found = ', '.join(not_found)
        raise ValueError(("The following languages were specified " + \
                          "but they were not found in any module:\n -> %s\n" + \
                          "May be you forgot to add another place where to " + \
                          "find it with -m or --modules.\nRun again with -vvv to get " + \
                          "more information about why is this happening.") %
                               not_found)

    languages = set(flavor2lang[f] for f in flavors)

    if len(flavors) != len(languages):
        flavor_lang_list = list(flavor2lang.items())
        flavor_lang_list.sort(key=operator.itemgetter(1))  # sort by language

        prev_flavor = prev_lang = None
        for f, l in flavor_lang_list:
            if l == prev_lang:
                bad_flavor = f
                break
            prev_flavor, prev_lang = f, l
        else:
            assert False

        raise ValueError(("The language flavors '%s' and '%s' refere to the same language '%s'.\n" + \
                          "You need to choose one.") %
                               (prev_flavor, bad_flavor, prev_lang))

    return frozenset(languages)


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
        "tags",
        default=True,
        help="enable the capturing and non-capturing tags (<name> and <...>)."
    )
    options_parser.add_flag(
        "capture",
        default=True,
        help="enable the capturing tags (<name>); requires +tags be enabled."
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
        metavar='<secs>',
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
        metavar='<lines>x<cols>',
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
        "type",
        default=False,
        help="enable the input tags [...]",
        aliases=['input']
    )

    options_parser.add_argument(
        "+input-prefix-range",
        metavar='<min>:<max>',
        default=(6, 12),
        type=_range,
        help=
        "amount of characters that must precede at minimum/maximum an input tag in the form min:max"
    )

    grp = options_parser.add_flag(
        "force-echo-filtering",
        default=False,
        help=
        "each interpreter disables the echo from the terminal but in some cases this cannot be done and an active filtering is required (this is an experimental feature, it will break your tests if no echo is received and it will force a full terminal emulation (see +term=ansi and +geometry))."
    )

    # Note: +force-echo-filtering-for and (+/-)force-echo-filtering
    # are mutually exclusive
    options_parser.add_argument(
        "+force-echo-filtering-for",
        required=False,
        action='append',
        default=[],
        into_group=grp,
        help=
        "apply an active echo filtering for the languages selected (this is an experimental feature, it will break your tests if no echo is received and it will force a full terminal emulation (see +term=ansi and +geometry))."
    )

    options_parser.add_flag(
        "filter-esc-seqs",
        default=True,
        help=
        "filter escape and control sequences from the terminal that may interfere, only used if +term=dumb."
    )

    options_parser.add_flag(
        "warn-tab",
        default=True,
        help=
        "emit a warning if the source code of an example has a tab character (a tab could interfere with the interpreter/runner)."
    )

    options_parser.add_argument(
        "+show-failures",
        metavar='<n>',
        default=cmdline_args.show_failures,
        type=_show_failures_type,
        help="show up to <n> failures per file and suppress the rest"
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
            'captured_env_vars': args.captured_env_vars,
            'language_specific_defaults': {}
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

    clog().chat(
        "Options (cmdline + byexample's defaults + --options): %s", options
    )

    options['x'] = {}
    for k, v in vars(args).items():
        if k.startswith('x_'):
            options['x'][k[2:]] = v

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
    return options


def show_options(cfg):
    registry = cfg['registry']
    allowed_languages = cfg['allowed_languages']

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


@profile
def extend_option_parser_with_concerns(cfg):
    registry = cfg['registry']
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
@profile
def extend_options_with_language_specific(cfg):
    registry = cfg['registry']
    allowed_languages = cfg['allowed_languages']

    parsers = [
        p for p in registry['parsers'].values()
        if p.language in allowed_languages
    ]

    defaults_by_lang = cfg['options']['language_specific_defaults']
    for parser in parsers:
        with enhance_exceptions(
            'Extending the options', parser, cfg['use_colors']
        ):
            # get from the parser a set of default options
            parser_optparser = parser.get_extended_option_parser(
                parent_parser=None
            )
            defaults = parser_optparser.defaults()

            # let each language-specific parser to parse the options from
            # the command line.
            with cfg['options'].with_top(defaults):
                opts = parser.extract_cmdline_options(cfg['opts_from_cmdline'])

            # we do not update cfg['options'] here anymore
            # as we want to isolation parser's options from affecting
            # byexample and other parsers/runners.
            #
            # cfg['options'].update(....)  <- not more

            # instead we should keep private each lang-specific option
            # Note: the parser may decide on extract_cmdline_options() to
            # change cfg['options'] as it has access to it via parser.options.
            # We leave this option in case that the parser really needs
            # to modify some of the main/byexample's options
            defaults.update(opts)
            if parser.language not in defaults_by_lang:
                # ensure we are dealing with plain dicts as we don't
                # need multiple layers of language-specific defaults
                defaults_by_lang[parser.language] = dict(defaults)
            else:
                defaults_by_lang[parser.language].update(defaults)

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
@profile
def _load_modules_and_init_cfg(args, sharer):
    lvl = verbosity_to_log_levels(args.verbosity, args.quiet)
    lvl.update(args.log_masks)
    setLogLevels(lvl)

    verify_encodings(args.encoding, args.verbosity)
    cfg = {
        'use_progress_bar': args.pretty == 'all' and \
                            not args.no_progress_bar,
        'use_colors': args.pretty == 'all',
        'quiet': args.quiet,
        'verbosity': args.verbosity,
        'encoding': args.encoding,
        'enc_error_handler': args.enc_error_handler,
        'output': sys.stdout,
        'interact': False,
        'opts_from_cmdline': args.options_str,
        'dry': args.dry,
        'jobs': args.jobs,
        # special value to denote that we are not in a worker/job yet
        # but in the main thread.
        'job_number': '__main__',
    }

    clog().chat("sys.argv: %s", sys.argv)
    testfiles = args.testfiles

    # ensure consistency: we cannot spawn more jobs than testfiles
    assert cfg['jobs'] <= len(testfiles)

    cfg['options'] = get_options(args, cfg)

    # if the output has not color support, disable the color anyways
    cfg['use_colors'] &= are_tty_colors_supported(cfg['output'])
    cfg['selected_languages'] = frozenset(args.languages)

    # Make a partial application of _prepare_subprocess_call(), binding
    # all the necessary parameters to import and register the byexample
    # modules (again) in a subprocess.
    #
    # The bound parameters are constant so the function, despite having
    # state, it is actually stateless (its state is constant, immutable)
    # Moreover, _prepare_subprocess_call() is thread-safe so the resulting
    # partial-bound function is thread-safe too.
    #
    # See _prepare_subprocess_call().
    prepare_subprocess_call = functools.partial(
        _prepare_subprocess_call, dirnames=tuple(args.modules_dirs)
    )
    cfg['prepare_subprocess_call'] = prepare_subprocess_call
    del prepare_subprocess_call

    # Loade the modules. This requires the prepare_subprocess_call set
    # in case they want to spawn processes later.
    # While the config is not finally complete, we still pass a Config object
    # to load_modules to ensure that it is not going to be modified
    # (it is not bullet proof, just a best effort)
    registry, namespaces_by_class = load_modules(
        args.modules_dirs, Config(cfg), sharer
    )

    # With the modules loaded, now we can know which languages are allowed
    # to run
    cfg['allowed_languages'] = get_allowed_languages(registry, args.languages)

    # Keep a reference to the registry too.
    cfg['registry'] = registry
    del registry

    # Create a namespace for each class. A namespace is where
    # all the *shared objects* live.
    namespaces = {}
    for klass, ns in namespaces_by_class.items():
        shared_ns = sharer.Namespace(**ns._as_dict())
        shared_ns._attribute_names = ns._attribute_names()
        namespaces[klass] = shared_ns

    cfg['namespaces'] = namespaces
    del namespaces

    # not longer needed: all the runner, parsers, concerns objects
    # were created and if they wanted to setup a shared object that was
    # their opportunity.
    del sharer

    # 'ns' was a temporal setting. In theory, it was never added to cfg
    # but this is just to ensure that.
    assert 'ns' not in cfg

    return testfiles, Config(cfg)


@log_context('byexample.init')
@profile
def init_byexample(args, sharer):
    testfiles, cfg = _load_modules_and_init_cfg(args, sharer)

    if args.show_options:
        show_options(cfg)
        sys.exit(0)

    if not testfiles:
        if not cfg['quiet']:
            clog().error(
                "No files were found (you passed %i files, %i were skipped)",
                len(set(args.files)), len(set(args.skip))
            )
            if not set(args.files) and set(args.skip):
                clog().warn(
                    "You are probably skipping more files than you want.\n" +\
                    "You may need to add a '--' to separate the files that\n" +\
                    "you want to skip from the ones that you want to execute:\n" +\
                    "\n  byexample --skip <files to skip> -- <files to execute>"
                )
        sys.exit(1)

    _extend_opts_and_config_log_system(cfg)
    return testfiles, cfg


@log_context('byexample.init')
@profile
def _extend_opts_and_config_log_system(cfg):
    # extend the option parser with all the parsers of the concerns.
    # do this *after* showing the options so we can show each parser's opt
    # separately
    extend_option_parser_with_concerns(cfg)

    # now that we know what languages are allowed, extend the options
    # for them
    extend_options_with_language_specific(cfg)

    if cfg['quiet']:
        cfg['registry']['concerns'].pop('progress', None)

    if not clog().isEnabledFor(CHAT):
        clog().chat("Options:\n%s.", pprint.pformat(cfg['options']))

    clog().chat("Configuration:\n%s.", pprint.pformat(cfg))

    concerns = ConcernComposite(cfg)
    configure_log_system(use_colors=cfg['use_colors'], concerns=concerns)


def _subprocess_trampoline(
    dirnames, serialized_func, serialized_args, serialized_kwargs
):
    # All of this happens in the *child* process
    # We reload the modules if they weren't loaded yet
    # and only then we deserialize the target function and we
    # call it.
    #
    # If _subprocess_trampoline is called in a fresh subprocess,
    # we are sure that no module was loaded yet however, it is
    # possible that the user runs a subprocess using forking
    # which makes a copy of the python process (parent) and therefore
    # it will have the modules loaded already.
    #
    # By the moment it is unclear if in addition to the loading we want
    # to do more like the instantiation of the plugins.
    from .init import import_and_register_modules_iter
    _ = list(import_and_register_modules_iter(dirnames))

    import multiprocessing.reduction
    fpickler = multiprocessing.reduction.ForkingPickler
    target = fpickler.loads(serialized_func)
    args = fpickler.loads(serialized_args)
    kwargs = fpickler.loads(serialized_kwargs)

    return target(*args, **kwargs)


def _prepare_subprocess_call(target, dirnames, *, args=(), kwargs={}):
    ''' Prepare the given target function to be executable in a separated
        process (child process).

        The preparation includes the (re)import and (re)registration of
        the modules found in <dirnames>, once loaded by byexample in the parent
        process.

        This re-import and re-registration within the child process
        is needed because the child may be an independent fresh Python
        process without any idea of how to load byexample modules.

        _prepare_subprocess_call returns a dictionary with keys 'target'
        and 'args' suitable to call multiprocessing.Process.

        Note: no user code should call _prepare_subprocess_call directly.
        Instead, call a partial bound function from the Config cfg object
        given to each extension (ExampleFinder, ExampleParser, Concern, ...).
        This partial function will not require the <dirnames> argument.
    '''
    # Implementation note: this function must be thread-safe because it
    # may be called from different threads.
    import multiprocessing.reduction
    fpickler = multiprocessing.reduction.ForkingPickler

    serialized_func = bytes(fpickler.dumps(target))
    serialized_args = bytes(fpickler.dumps(args))
    serialized_kwargs = bytes(fpickler.dumps(kwargs))

    trampoline_args = (
        dirnames, serialized_func, serialized_args, serialized_kwargs
    )

    return {'target': _subprocess_trampoline, 'args': trampoline_args}


@profile
def init_worker(cfg, job_num):
    ''' Initialize a worker with worker/job number is passed
        by parameter.

        The registry's elements (parsers, runners, concerns,
        zdelimiters and finders) from <cfg> are recreated and
        the rest are copied so the worker is initialized with
        a fresh and independent copy.

        The only difference is that <cfg> will have <job_num>
        as the value of the 'job_number' key.

        If the recreation process is thread safe (depends of the objects'
        implementations), then init_worker is thread safe.
    '''
    patch = {}
    # Patch the job_number: let the rest of byexample for this worker to know
    # in which worker is on
    assert cfg['job_number'] == '__main__'
    patch['job_number'] = int(job_num)

    # Get an independent copy of cfg (and therefore, thread-safe)
    # with some keys patched
    cfg = cfg.copy(patch=patch)

    concerns = ConcernComposite(cfg)

    init_thread_specific_log_system(concerns)

    with log_with('byexample.init') as log:
        differ = Differ(cfg)

        harvester = ExampleHarvest(cfg)
        executor = FileExecutor(concerns, differ, cfg)

        return harvester, executor
