r"""
Example:

  >> 1 + 2
  3

  >> fn hello() {
  ::    println!("hello bla world"); // classic
  :: }

  >> hello();           // byexample: +norm-ws
  hello   <...>   world

  >> let mut j = 2;
  >> for i in 0..4 {
  ::   j += i;
  :: }; // extra ; to suppress output check

  >> j + 3
  11

  >> println!("{}", "this\n
  :: is a multiline\n
  :: string\n");
  this
  is a multiline
  string

  >> /* this
  :: is a multiline
  :: comment */

  >> #[derive(Debug)]
  :: struct Point {
  ::   x: f32,
  ::   y: f32,
  :: }

  >> let p1 = Point { x: 2.0, y: 3.0 };
  >> p1
  Point { x: 2.0, y: 3.0 }

  >> #[derive(Debug)]
  :: struct Child(i32);

  >> #[derive(Debug)]
  :: struct Parent(Child);

  >> let c1 = Child(42);
  >> let c2 = Parent(Child(33));

  >> c1
  Child(42)
  >> c2
  Parent(Child(33))

  Pretty print for arrays and tuple are supported but only
  up to 12 elements. This is a restriction of Rust.

  >> let array = [1, 2, 3];
  >> let tuple = (1, true, 2.3);

  >> array
  [1, 2, 3]
  >> tuple
  (1, true, 2.3)

  Slices are not supported in the main space but they are okay
  in a function
  >> let slice: &[i32] = &array[0..2];      // byexample: +skip

  >> fn bar(slice: &[i32]) {
  ::    println!("{:?}", slice);
  :: }

  >> bar(&array[0..2]);
  [1, 2]

  >> const PI : f64 = 3.1416;
  >> PI
  3.1416

  Closure are not supported in the main space but they are okay
  in a function
  >> let i = 4;
  >> let closure_explicit = |j: i32| -> i32 { i + j };  // byexample: +skip
  >> let closure_implicit = |j     |          i + j  ;  // byexample: +skip
  >> let one = || 1;                                    // byexample: +skip

  >> let k = Box::new(42);          // byexample: +skip
  >> let stealer = move || { k };   // byexample: +skip
  >> println!("{:?}", stealer());   // byexample: +skip

  >> fn baz() {
  ::    let i = 4;
  ::    let closure_explicit = |j: i32| -> i32 { i + j };
  ::    let closure_implicit = |j     |          i + j  ;
  ::    let one = || 1;
  ::
  ::    let k = Box::new(42);
  ::    let stealer = move || { k };
  ::    println!("{:?} {:?} {:?} {:?}", closure_explicit(2), closure_implicit(2), one(), stealer());
  :: }

  >> baz();
  6 6 1 42


  Types
  >> type Nanosecs = u64;
  >> let a : Nanosecs = 2;
  >> a
  2

  Scopes
  >> let y = {
  ::   let z = 11;
  ::   i + z  // this is an *expression*, the result of the block
  :: };
  >> y
  15

  Flow control
  >> let mut m = if i < 1 {
  ::   i + 2
  :: } else {
  ::   i + 8
  :: };

  >> loop {
  ::    if m >= 20 {
  ::        break;
  ::    }
  ::
  ::    m += 1;
  ::    if m % 2 == 0 {
  ::        continue;
  ::    }
  ::
  ::    println!("m is odd: {}", m);
  :: };
  m is odd: 13
  m is odd: 15
  m is odd: 17
  m is odd: 19

  >> 'theloop : while true {
  ::    m -= 1;
  ::    if m == 0 {
  ::        break 'theloop;
  ::    }
  :: };

  >> m
  0

"""

from __future__ import unicode_literals
import sys, time
import byexample.regex as re
from byexample.common import constant
from byexample.parser import ExampleParser
from byexample.runner import ExampleRunner, PexpectMixin, ShebangTemplate
from byexample.finder import ExampleFinder

stability = 'experimental'


class RustPromptFinder(ExampleFinder):
    target = 'rust-prompt'

    @constant
    def example_regex(self):
        return re.compile(
            r'''
            (?P<snippet>
                (?:^(?P<indent> [ ]*) (?:>>)[ ]  .*)         # PS1 line
                (?:\n           [ ]*  ::             .*)*)    # PS2 lines
            \n?
            ## Want consists of any non-blank lines that do not start with PS1
            (?P<expected> (?:(?![ ]*$)        # Not a blank line
                          (?![ ]*(?:>>))     # Not a line starting with PS1
                          .+$\n?              # But any other line
                      )*)
            ''', re.MULTILINE | re.VERBOSE
        )

    def get_language_of(self, *args, **kargs):
        return 'rust'

    def get_snippet_and_expected(self, match, where):
        snippet, expected = ExampleFinder.get_snippet_and_expected(
            self, match, where
        )

        snippet = self._remove_prompts(snippet)
        return snippet, expected

    def _remove_prompts(self, snippet):
        lines = snippet.split("\n")
        return '\n'.join(line[3:] for line in lines)


class RustParser(ExampleParser):
    language = 'rust'

    @constant
    def example_options_string_regex(self):
        # anything of the form:
        #   //  byexample:  +FOO -BAR +ZAZ=42
        return re.compile(r'//\s*byexample:\s*([^\n\'"]*)$', re.MULTILINE)


class RustInterpreter(ExampleRunner, PexpectMixin):
    language = 'rust'

    def __init__(self, verbosity, encoding, **unused):
        self.encoding = encoding

        PexpectMixin.__init__(self, PS1_re=r'>> ', any_PS_re=r'>> ')

    def get_default_cmd(self, *args, **kargs):
        return "%e %p %a", {
            'e':
            "/usr/bin/env",
            'p':
            "evcxr",
            'a': [
                "--disable-readline",  # no readline
                "--opt",
                "0",  # disable optimizations (reduce exec time)
            ]
        }

    def run(self, example, options):
        # evcxr's output requeries to be emulated by an ANSI Terminal
        # so we force this (see _get_output())
        options['term'] = 'ansi'
        options['timeout'] = (max(options['timeout'], 8))
        return PexpectMixin._run(self, example, options)

    def _run_impl(self, example, options):
        src = example.source
        src = self._strip_and_join_lines_into_one(src, strip=True)
        return self._exec_and_wait(src, options, from_example=example)

    _SINGLE_LINE_COMMENT_RE = re.compile(r'//[^\n]*$')

    def _strip_and_join_lines_into_one(self, src, strip):
        # evcxr doesn't support multiline code if the readline is disabled
        # so the simplest thing to do is to collapse all the lines into one
        # Rust is a language which syntax should not be affected by this
        # in contrast to Python **except** when a single-line comment "//"
        # is used.
        #
        # Valid code like this:
        #  fn foo() { // super
        #    42
        #  }
        # It will not work as it will be seen as:
        #  fn foo () { // super 42 }
        #
        # The workaround is to strip those comments.
        #
        _RE = self._SINGLE_LINE_COMMENT_RE
        lines = src.split('\n')
        if strip:
            lines = (_RE.sub('', line) for line in lines)

        return ''.join(lines)

    def interact(self, example, options):
        PexpectMixin.interact(self)

    def initialize(self, options):
        shebang, tokens = self.get_default_cmd()
        shebang = options['shebangs'].get(self.language, shebang)

        cmd = ShebangTemplate(shebang).quote_and_substitute(tokens)

        options.up()
        # evcxr can be quite slow so we increase the timeout by default
        options['x']['dfl_timeout'] = (max(options['x']['dfl_timeout'], 30))
        self._spawn_interpreter(cmd, options)

        # enable sccache (https://github.com/mozilla/sccache) so evcxr
        # can speed up the compilation of the examples
        self._exec_and_wait(
            ':sccache 1', options, timeout=options['x']['dfl_timeout']
        )
        options.down()

    def _expect_delayed_output(self, options):
        # evcxr runs the example in background so it may return before
        # the example finishes. In those cases we want to wait a little
        # more to capture all the output
        delay = options['x']['delayafterprompt'] or 0
        options['x']['delayafterprompt'] = max(delay, 0.25)
        return super()._expect_delayed_output(options)

    def shutdown(self):
        self._shutdown_interpreter()

    def cancel(self, example, options):
        return self._abort(example, options)
