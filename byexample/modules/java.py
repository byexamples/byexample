"""
Example:

    j> 1 + 2
    => 3

    Yes, leave this as an empty example with trailing space
    We expect to be executed and do nothing
    j>   

    j> int hello() {
    ..    System.out.println("hello bla world");
    ..    return 4;
    .. }

    j> hello()      // byexample: +norm-ws
    hello   <...>   world
    => 4

    j> int j = 2
    j> for (int i = 0; i < 4; i++) {
    ..  j += i;
    .. }

    j> j + 3
    => 11

    Pretty print of common data structures: primitive arrays,
    ArrayList, and HashMap

    j> int[] anArray = {
    ..     100, 200, 300,
    ..     400, 500, 600,
    ..     700, 800, 900, 1000
    .. };
    => int[10] { 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000 }

    Leave the "// foo" comment there, this made jshell to fail in the
    past
    j> String[][] names = {   // foo
    ..             {"Mr. ", "Mrs. ", "Ms. "},
    ..             {"Smith", "Jones"}
    ..         };
    => String[2][] { String[3] { "Mr. ", "Mrs. ", "Ms. " }, String[2] { "Smith", "Jones" } }

    j> ArrayList<String> cars = new ArrayList<String>();
    => []

    j> cars.add("BMW");
    j> cars.add("Mercedes-Benz");
    j> cars.add("Audi");
    j> cars.add("Lexus");

    j> cars
    => [BMW, Mercedes-Benz, Audi, Lexus]

    j> HashMap<String, String> colors = new HashMap<String, String>();
    => {}

    j> colors.put("red", "#f00");
    j> colors.put("green", "#0f0");
    j> colors.put("blue", "#00f");

    j> colors
    => {red=#f00, green=#0f0, blue=#00f}

    Closures
    j> ArrayList<Integer> numbers = new ArrayList<Integer>();
    j> numbers.add(1);
    j> numbers.add(2);
    j> numbers.add(3);

    j> numbers.forEach( (n) -> { System.out.println(n); } );
    1
    2
    3

    Autodetect print expression:
    j> "foo bar 1"
    => "foo bar 1"

    j> "foo bar 2"

    j> "foo bar 3"
    => "foo bar 3"

    j> "foo bar 4"    // byexample: +norm-ws
    => "foo bar 4"


    j> Scanner in = new Scanner(System.in)
    j> String s

    j> System.out.print("num: "); s = in.nextLine(); // byexample: +type +skip
    num: [42]
    j> s            // byexample: +skip
    => 42

    j> s = in.nextLine()        // byexample: +type +skip
    [it works!]
    j> s            // byexample: +skip
    => "it works!"

"""

from __future__ import unicode_literals
import pexpect, sys, time, subprocess, itertools
import byexample.regex as re
from byexample.common import constant
from byexample.log import clog
from byexample.parser import ExampleParser
from byexample.finder import ExampleFinder
from byexample.runner import ExampleRunner, PexpectMixin, ShebangTemplate

stability = 'experimental'


class JavaPromptFinder(ExampleFinder):
    target = 'java-prompt'

    @constant
    def example_regex(self):
        return re.compile(
            r'''
            # Snippet consists of one PS1 line >> and zero or more PS2 lines
            (?P<snippet>
                (?:^(?P<indent> [ ]*) j>[ ]   .*)    # PS1 line
                (?:\n           [ ]*  \.\.    .*)*)  # zero or more PS2 lines
            \n?
            # Want consists of any non-blank lines that do not start with PS1
            # The '=>' indicator is included (implicitly) and may not exist
            (?P<expected> (?:(?![ ]*$)            # Not a blank line
                             (?![ ]*   j>)        # Not a line starting with PS1
                             .+$\n?               # But any other line
                      )*)
            ''', re.MULTILINE | re.VERBOSE
        )

    def get_language_of(self, *args, **kargs):
        return 'java'

    def get_snippet_and_expected(self, match, where):
        snippet, expected = ExampleFinder.get_snippet_and_expected(
            self, match, where
        )

        snippet, expected = self._remove_prompts(snippet, expected)
        return snippet, expected

    def _remove_prompts(self, snippet, expected):
        lines = snippet.split("\n")
        n = lines[0].index("j> ")

        snippet = '\n'.join(line[n + 3:] for line in lines)
        expected = '\n'.join(line[n:] for line in expected.split('\n'))

        return snippet, expected


class JavaParser(ExampleParser):
    language = 'java'

    @constant
    def example_options_string_regex(self):
        return re.compile(r'//\s*byexample:\s*([^\n\'"]*)$', re.MULTILINE)

    def extend_option_parser(self, parser):
        parser.add_argument(
                "+java-expr-print",
                choices=['auto', 'true', 'false'],
                default='auto',
                help='print the expression\'s value (true); ' +\
                     'suppress it (false); or print it only ' +\
                     'if the example has a => (auto, the default)')

        parser.add_argument(
                "+java-class-path",
                metavar='<path>',
                default=None,
                help='List of directories, JAR archives, ' +\
                     'and ZIP archives to search for class files ' +\
                     'separated by a colon (:). On Windows use a ' +\
                     'semicolon (;).'
                     )
        parser.add_argument(
                "+java-module-path",
                metavar='<path>',
                default=None,
                help='List of directories, JAR archives, ' +\
                     'and ZIP archives to search for modules ' +\
                     'separated by a colon (:). On Windows use a ' +\
                     'semicolon (;).'
                     )
        parser.add_argument(
                "+java-add-modules",
                metavar='<name>[,<name>...]',
                default=None,
                help='Root modules to resolve in addition to the ' +\
                     'initial module. <name> can also be ALL-DEFAULT, ' +\
                     'ALL-SYSTEM, ALL-MODULE-PATH.'
                     )
        parser.add_argument(
                "+java-add-exports",
                metavar='<module>/<package>=<target>[,<target>...]',
                default=None,
                help='Updates <module> to export <package> to ' +\
                     '<target-module>, regardless of module declaration. ' +\
                     '<target-module> can be ALL-UNNAMED to export to all ' +\
                     'unnamed modules. In jshell, if the <target-module> ' +\
                     'is not specified then ALL-UNNAMED is used.'
                     )
        return parser


class JavaInterpreter(ExampleRunner, PexpectMixin):
    language = 'java'

    def __init__(self, verbosity, encoding, **unused):
        PexpectMixin.__init__(
            self, PS1_re=r'jshell> ', any_PS_re=r'((jshell)|(\.\.\.))> '
        )

        self.encoding = encoding
        self.is_print_expr_set = None

    def run(self, example, options):
        # jshell's output requires to be emulated by an ANSI Terminal
        # so we force this
        options['geometry'] = self._terminal_default_geometry
        options['term'] = 'ansi'
        return PexpectMixin._run(self, example, options)

    def _change_terminal_geometry(self, rows, cols, options):
        raise Exception("This should never happen")

    def _run_impl(self, example, options):
        src = example.source
        src = self._strip_lines_into_one(
            src, strip_comment=True, rstrip_ws=True
        )

        # Is the example expecting the expression being print?
        expr_print_mode = options['java_expr_print']
        print_expr = expr_print_mode == 'true'
        if expr_print_mode == 'auto':
            print_expr = self._detect_expression_print_expected(example)

        # change the print expression mode if it is different from
        # the one already set
        if print_expr != self.is_print_expr_set:
            if print_expr:
                setmode = '/set feedback byexampleconcise\n'
                self.is_print_expr_set = True
            else:
                setmode = '/set feedback byexamplesilent\n'
                self.is_print_expr_set = False

            src = setmode + src

        # append a cookie as a Java comment: we expect to see this echoed
        # back in the output
        src += ' // byexampleEOFcookie'
        out = self._exec_and_wait(src, options, from_example=example)

        # drop all the lines until we see the last line echoed which should
        # have our cookie
        lines = itertools.dropwhile(
            lambda line: 'byexampleEOFcookie' not in line, out.split('\n')
        )

        # drop the last line (the one that has the cookie) and
        # return the rest as a single result.
        out = '\n'.join(itertools.islice(lines, 1, sys.maxsize))
        return out

    _SINGLE_LINE_COMMENT_RE = re.compile(r'//[^\n]*$')

    def _strip_lines_into_one(self, src, strip_comment, rstrip_ws):
        # jshell supports multiline code but for some reason when we write
        # such code from byexample, jshell does not flush the secondary prompt
        # and the whole thing hangs.
        # So the simplest thing to do is to collapse all the lines into one
        # Java is a language which syntax should not be affected by this
        # in contrast to Python **except** when a single-line comment "//"
        # is used.
        #
        # Valid code like this:
        #  int foo() { // super
        #    return 42;
        #  }
        # It will not work as it will be seen as:
        #  int foo () { // super return 42; }
        #
        # The workaround is to strip those comments.
        #
        # We also found that if the line has some whitespace on the
        # right jshell will not work either. Strip that too.
        #
        _RE = self._SINGLE_LINE_COMMENT_RE
        lines = src.split('\n')
        if strip_comment:
            lines = (_RE.sub('', line) for line in lines)

        if rstrip_ws:
            lines = (line.rstrip() for line in lines)

        return ''.join(lines)

    _EXPR_RESULT_RE = re.compile(r'^=>( |$)', re.MULTILINE | re.DOTALL)

    def _detect_expression_print_expected(self, example):
        # aka, check for a =>
        expected_str = example.expected.str
        return self._EXPR_RESULT_RE.search(expected_str) != None

    def interact(self, example, options):
        PexpectMixin.interact(self)

    def get_default_cmd(
        self, class_path, module_path, add_modules, add_exports, *a, **kargs
    ):
        args = ['--no-startup']
        if class_path:
            args.extend(['--class-path', class_path])
        if module_path:
            args.extend(['--module-path', module_path])
        if add_modules:
            args.extend(['--add-modules', add_modules])
        if add_exports:
            args.extend(['--add-exports', add_exports])

        return "%e %p %a", {'e': '/usr/bin/env', 'p': 'jshell', 'a': args}

    def initialize(self, options):
        # Set the prompts to the defaults of jshell. Once we had
        # configured jshell to work nice with byexample we can change
        # the prompts back to byexample's one.
        # We need to do this in each initialize() call because
        # __init__() is called only once per worker and not per file
        # execution.
        self._set_prompts(
            PS1_re=r'jshell> ', any_PS_re=r'((jshell)|(\.\.\.))> '
        )

        # always/yes; never/no; autodetect normalization
        self.expr_print_mode = options['java_expr_print']

        shebang, tokens = self.get_default_cmd(
            class_path=options['java_class_path'],
            module_path=options['java_module_path'],
            add_modules=options['java_add_modules'],
            add_exports=options['java_add_exports']
        )
        shebang = options['shebangs'].get(self.language, shebang)

        cmd = ShebangTemplate(shebang).quote_and_substitute(tokens)

        dfl_timeout = options['x']['dfl_timeout']

        # NO_COLORS seems to have no effect but TERM set to 'dumb' makes
        # jshell to output less garbage
        env_update = {'NO_COLORS': '1', 'TERM': 'dumb'}

        # setting the geometry here will also set
        # the _terminal_default_geometry variable for later
        options.up()
        options['geometry'] = (
            max(options['geometry'][0], 128), max(options['geometry'][1], 128)
        )
        # run!
        self._spawn_interpreter(cmd, options, env_update=env_update)
        options.down()

        cfg = r'''
        /open DEFAULT

        /set mode byexampleconcise concise -quiet
        /set prompt byexampleconcise "\n/byexample/ps1> "  "\n/byexample/ps2> "

        /set truncation byexampleconcise 1000
        /set truncation byexampleconcise 1000 expression,varvalue

        /set format byexampleconcise action ""
        /set format byexampleconcise display ""
        /set format byexampleconcise display "{pre}attempted to use {typeKind} {name}{resolve}{post}" class,interface,enum,annotation-used
        /set format byexampleconcise display "{pre}attempted to call method {name}({type}){resolve}{post}" method-used
        /set format byexampleconcise display "{result}" vardecl,varinit,expression,varvalue,assignment-added,modified,replaced-primary-ok
        /set format byexampleconcise result "=> {value}{post}" added,modified,replaced-primary-ok

        /set mode byexamplesilent byexampleconcise -quiet
        /set format byexamplesilent display "" vardecl,varinit,expression,varvalue,assignment-added,modified,replaced-primary-ok
        /set format byexamplesilent result "" added,modified,replaced-primary-ok
        '''

        # strip each line and remove empty ones so the configuration for jshell
        # is "compact"
        cfg = '\n'.join(
            filter(None, (line.strip() for line in cfg.split('\n')))
        )

        # send the configuration and wait for the old prompt
        self._exec_and_wait(cfg, options, timeout=dfl_timeout)

        # disable the print-expr if we don't want it (false) or we may want it
        # but it will depend on the example (auto)
        if self.expr_print_mode in ('auto', 'false'):
            setmode = '/set feedback byexamplesilent'
            self.is_print_expr_set = False
        else:
            setmode = '/set feedback byexampleconcise'
            self.is_print_expr_set = True

        # change the expected prompts for the next and further interactions
        # with jshell
        self._set_prompts(
            PS1_re=r'/byexample/ps1> ', any_PS_re=r'/byexample/ps[12]> '
        )

        # send the configuration for the set-mode (print expr)
        # and wait for the new prompt to be on
        self._exec_and_wait(setmode, options, timeout=dfl_timeout)

    def shutdown(self):
        self._shutdown_interpreter()

    def cancel(self, example, options):
        return self._abort(example, options)
