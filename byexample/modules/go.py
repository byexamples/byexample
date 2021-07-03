"""
Example:

  Basic examples. The colon in the expected output tells to byexample
  to print the expression value provided by yaegis
  > 1 + 2
  : 3

  > 2 * 3
  : 6

  Example of multiline function definition
  Note that no expression is checked because the expected output does
  not have a colon and byexample was instructed to work in 'auto' mode
  > func hello() {
  .    fmt.Println("hello bla world")
  . }

  Custom options/flags
  > hello()               // byexample: +norm-ws
  hello   <...>   world

  Imports
  > import (
  .  "fmt"
  .  "time"
  . )

  > time.Now()
  : <...> UTC <...>

  > func swap(a string, b string) (string, string) {
  .   return b, a
  . }

  Variable definition with ':='
  > a, b := swap("world", "hello")
  > a + " " + b
  : hello world

  Variable definitions with 'var'
  > var (
  .     ToBe   bool       = false
  .     MaxInt uint64     = 1<<64 - 1
  .     z      complex128 = cmplx.Sqrt(-5 + 12i)
  . )

  Force the print of the expression even if the expected output
  does not have a colon
  > z           // byexample: +go-expr-print=true
  <...> (2+3i)

  > const PI = 3.1416
  > PI
  : 3.1416

  For-loops
  > sum := 2
  > for i := 0; i < 4; i++ {
  .   sum += i
  . }
  > sum + 3
  : 11

  > if v := sum; v > 5 {
  .   sum++
  . }
  > sum
  : 9

  Defer example
  > func foo() {
  .   fmt.Println("Begin")
  .   defer fmt.Println("Deferred")
  .   fmt.Println("End")
  . }

  > foo()
  Begin
  End
  Deferred

  Pointers in the main space are NOT supported
  > var p *int = &sum   // byexample: +skip
  > *p = 42             // byexample: +skip
  > sum                 // byexample: +skip
  : 42

  But pointers in a function are supported
  > func bar(p *int) {
  .    *p = 37
  . }
  > bar(&sum)
  > sum
  : 37

  Structs
  > type Vertex struct {
  .    X int
  .    Y int
  . }
  > Vertex{1, 2}
  : {1 2}

  Arrays
  > primes := [6]int{2, 3, 5, 7, 11, 13}
  > primes
  : [2 3 5 7 11 13]

  Slices in the main space are NOT supported
  > var subprimes[]int = primes[1:4]    // byexample: +skip

  Slices in a function are supported
  > func chunk(primes *[6]int) {
  .    var subprimes[]int = primes[1:4]
  .    fmt.Println(subprimes)
  . }
  > chunk(&primes)
  [3 5 7]

  Slices created by make are supported even in the main space
  > mem := make([]int, 5)
  > mem
  : [0 0 0 0 0]

  Slice literals in a function are supported too
  Slice literals of a struct however requires the struct definition
  to be in the same line.
  > func slice_literal() {
  .     q := []int{2, 3, 5, 7, 11, 13}
  .     fmt.Println("q:", q)
  .
  .     s := []struct { x int; b bool }{  // <-- struct definition in one line
  .     	{2, true},
  .     	{3, false},
  .     	{5, true},
  .     	{7, true},
  .     	{11, false},
  .     	{13, true},
  .     }
  .     fmt.Println("s:", s)
  . }
  > slice_literal()
  q: [2 3 5 7 11 13]
  s: [{2 true} {3 false} {5 true} {7 true} {11 false} {13 true}]

  Dictionary are supported
  > var dictionary map[string]Vertex
  > dictionary
  : map[]

  > dictionary = make(map[string]Vertex)
  > dictionary["p1"] = Vertex{
  .      40, -74,
  . }
  > dictionary
  : map[p1:{40 -74}]

  > var dictionary2 = map[string]Vertex{
  .     "p1": Vertex {
  .         1,
  .         2,
  .     },
  .     "p2": Vertex {
  .         3,
  .         4,
  .     },
  . }
  > dictionary2
  : map[p1:{1 2} p2:{3 4}]

  > var dictionary3 = map[string]Vertex{
  .     "p1": {1, 2},
  .     "p2": {3, 4},
  . }
  > dictionary3
  : map[p1:{1 2} p2:{3 4}]

  High-order functions and closures
  > func run(fn func(int, int) int) int {
  .   return fn(3, 4)
  . }

  > func add(x, y int) int { return x + y; }
  > run(add)
  : 7

  > func accum() func(int) int {
  .   sum := 0
  .   return func(x int) int {
  .     sum += x
  .     return sum
  .   }
  . }

  > adder := accum()
  > for i := 0; i < 4; i++ {
  .   fmt.Println(adder(i))
  . }
  0
  1
  3
  6

  > func (v Vertex) norm2() float64 {
  .    return v.X*v.X + v.Y*v.Y
  . }

  > v := Vertex{3, 4}
  > v.norm2()
  : 25

  Interfaces are supported but pretty print don't
  > type Norm2 interface {
  .   norm2() float64
  . }

  > var n2 Norm2
  > n2 = v  // Vertex implements Norm2
  > n2
  : {0x<...>}
  > n2.norm2()
  : 25

  Type assertions are not supported but you can use
  type switches in a function
  > var iface interface{} = "hello"
  > s := i.(string)     // byexample: +skip

  > func do(i interface{}) {
  .       switch v := i.(type) {
  .       case int:
  .               fmt.Printf("Twice %v is %v\n", v, v*2)
  .       case string:
  .               fmt.Printf("%q is %v bytes long\n", v, len(v))
  .       default:
  .               fmt.Printf("I don't know about type %T!\n", v)
  .       }
  . }

  > do(21)
  Twice 21 is 42
  > do("foo")
  "foo" is 3 bytes long
  > do(3.1416)
  I don't know about type float64!

  Typing is not supported (yaegi does not support it)
  > reader := bufio.NewReader(os.Stdin)
  > text, _ := reader.ReadString('\n')    // byexample: +type +skip
  [foo]

  Channels are supported
  > ch := make(chan int)
  > func counter() {
  .    for i := 0; i < 4; i++ {
  .        ch <- i
  .    }
  .    close(ch)
  . }
  > go counter()
  > for i := range ch {
  .   fmt.Println(i)
  . }
  0
  1
  2
  3

"""

from __future__ import unicode_literals
import pexpect, sys, time, subprocess
import byexample.regex as re
from byexample.common import constant
from byexample.log import clog
from byexample.parser import ExampleParser
from byexample.finder import ExampleFinder
from byexample.runner import ExampleRunner, PexpectMixin, ShebangTemplate

stability = 'provisional'


class GoPromptFinder(ExampleFinder):
    target = 'go-prompt'

    @constant
    def example_regex(self):
        return re.compile(
            r'''
            # Snippet consists of one PS1 line >> and zero or more PS2 lines
            (?P<snippet>
                (?:^(?P<indent> [ ]*) >[ ]   .*)    # PS1 line
                (?:\n           [ ]*  \.    .*)*)  # zero or more PS2 lines
            \n?
            # Want consists of any non-blank lines that do not start with PS1
            # The '=>' indicator is included (implicitly) and may not exist
            (?P<expected> (?:(?![ ]*$)            # Not a blank line
                             (?![ ]*   >)        # Not a line starting with PS1
                             .+$\n?               # But any other line
                      )*)
            ''', re.MULTILINE | re.VERBOSE
        )

    def get_language_of(self, *args, **kargs):
        return 'go'

    def get_snippet_and_expected(self, match, where):
        snippet, expected = ExampleFinder.get_snippet_and_expected(
            self, match, where
        )

        snippet, expected = self._remove_prompts(snippet, expected)
        return snippet, expected

    def _remove_prompts(self, snippet, expected):
        lines = snippet.split("\n")
        n = lines[0].index("> ")

        snippet = '\n'.join(line[n + 2:] for line in lines)
        expected = '\n'.join(line[n:] for line in expected.split('\n'))

        return snippet, expected


class GoParser(ExampleParser):
    language = 'go'

    @constant
    def example_options_string_regex(self):
        return re.compile(r'//\s*byexample:\s*([^\n\'"]*)$', re.MULTILINE)

    def extend_option_parser(self, parser):
        parser.add_argument("+go-expr-print", choices=['auto', 'true', 'false'],
                            default='auto',
                            help='print the expression\'s value (true); ' +\
                                 'suppress it (false); or print it only ' +\
                                 'if the example has a colon (auto, the default)')
        return parser


class GoInterpreter(ExampleRunner, PexpectMixin):
    language = 'go'

    def __init__(self, verbosity, encoding, **unused):
        PexpectMixin.__init__(
            self,
            # yaegi uses a very short PS1 prompt and nothing
            # as a secondary prompt. These regex tries to be as
            # precise as possible but it is little what byexample can
            # do to avoid false positives
            PS1_re=re.compile(r'(^|\n)> ', re.MULTILINE),
            any_PS_re=re.compile(r'(^|\n)(> )?', re.MULTILINE)
        )

        self.encoding = encoding

    def run(self, example, options):
        return PexpectMixin._run(self, example, options)

    def _run_impl(self, example, options):
        src = example.source
        src = src.rstrip()
        out = self._exec_and_wait(src, options, from_example=example)

        # Is the example expecting the expression being print?
        expr_print_mode = options['go_expr_print']
        print_expr = expr_print_mode == 'true'
        if expr_print_mode == 'auto':
            print_expr = self._detect_expression_print_expected(example)

        if not print_expr:
            # the print is not expected/wanted, remove it.
            # for that search the most-right colon and remove
            # anything after that
            last_colon_match = None
            m = self._EXPR_RESULT_RE.search(out)
            while m:
                last_colon_match = m
                m = self._EXPR_RESULT_RE.search(out, m.end())

            # remove anything after the last colon
            if last_colon_match:
                out = out[:last_colon_match.start()]

        return out

    _EXPR_RESULT_RE = re.compile(r'^:( |$)', re.MULTILINE | re.DOTALL)

    def _detect_expression_print_expected(self, example):
        # aka, check for a colon (:)
        expected_str = example.expected.str
        return self._EXPR_RESULT_RE.search(expected_str) != None

    def interact(self, example, options):
        PexpectMixin.interact(self)

    def get_default_cmd(self, *args, **kargs):
        args = ['run', '-i', '-unsafe', '-unrestricted', '-syscall']
        return "%e %p %a", {'e': '/usr/bin/env', 'p': 'yaegi', 'a': args}

    def initialize(self, options):
        # always/yes; never/no; autodetect normalization
        self.expr_print_mode = options['go_expr_print']

        shebang, tokens = self.get_default_cmd()
        shebang = options['shebangs'].get(self.language, shebang)

        cmd = ShebangTemplate(shebang).quote_and_substitute(tokens)

        dfl_timeout = options['x']['dfl_timeout']

        # run!
        self._spawn_interpreter(cmd, options)
        self._drop_output()

    def shutdown(self):
        self._shutdown_interpreter()

    def cancel(self, example, options):
        return False  #self._abort(example, options)
