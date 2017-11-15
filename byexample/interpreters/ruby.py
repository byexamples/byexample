import re, pexpect, sys, time
from byexample.byexample import ExampleParser

class RubyInterpreter(ExampleParser):
    ''' An interpreter for Ruby using irb.
        Example:
            rb> def hello
            ...     'hello bla world'
            ... end;

            rb> hello      # doctest: +ELLIPSIS
            => "hello...world"

    '''
    def example_regex(self):
        return re.compile(r'''
            # Source consists of a PS1 line rb>
            # followed by zero or more PS2 lines.
            (?P<source>
                (?:^(?P<indent> [ ]*) rb>[ ]     .*)    # PS1 line
                (?:\n           [ ]*  \.\.\.   .*)*)    # PS2 lines
            \n?
            # Want consists of any non-blank lines that do not start with PS1
            # The '=>' indicator is included (implicitly)
            (?P<expected> (?:(?![ ]*$)     # Not a blank line
                         (?![ ]*rb>)       # Not a line starting with PS1
                         .+$\n?            # But any other line
                      )*)
            ''', re.MULTILINE | re.VERBOSE)

    def example_options_regex(self):
        optstring_re = re.compile(r'#\s*byexample:\s*([^\n\'"]*)$',
                                                    re.MULTILINE)

        opt_re = re.compile(r'(?:(?P<add>\+)|(?P<del>-))(?P<name>\w+)',
                                                    re.MULTILINE)

        return optstring_re, opt_re

    def remove_prompts(self, source):
        return '\n'.join(line[self.PROMPT_LEN+1:] for line in source.split("\n"))

    def __repr__(self):
        return self.INTERPRETER_NAME

    INTERPRETER_NAME = "Ruby (%s)" % "/usr/bin/irb"
    PROMPT_LEN = 3


    _EXCEPTION_RE = re.compile(r"""
        # in ruby, the exception message is shown at the begin
        # there isn't a good candidate for hdr so we use the first word
        # of the message
        (?P<msg>  (?:^(?P<hdr>\w+)       [^\n]*)  # start with alphanum
                  (?:\n(?!\tfrom[ ]) [^\n]*    )* # rest cannot be a 'from' line

        )  \n?

        # the traceback must start with a 'from' line
        # more 'from' lines can follow but other lines are also accepted
        (?P<stack> ^\tfrom[ ] .*)
        """, re.VERBOSE | re.MULTILINE | re.DOTALL)


    def run(self, example, flags):
        self.irb.send(example.source + '\n')
        self._expect_prompt()

        return self._get_output()

    def _expect_prompt(self, timeout=2):
        # now we wait for a PS1 prompt
        # if we get a timeout that could mean:
        #   - the code executed is taking too long to finish
        #   - the code is malformed and the interpreter is waiting
        #     more data like this:
        #     >>> [ 1, 2,
        #     ...   3, 4,
        #     (the ] is missing)
        # if we don't get a timeout that could mean:
        #   - good, we got the *last* prompt line
        #   - good but we may didn't get the *last* prompt line
        #     and we should try to find the next prompt again
        expect = [self.PS1, pexpect.TIMEOUT]
        PS1_found, Timeout = range(len(expect))

        what = self.irb.expect(expect, timeout=timeout)
        self.last_output.append(self.irb.before)

        if what == PS1_found:
            while what != Timeout:
                what = self.irb.expect(expect, timeout=0.05)
                self.last_output.append(self.irb.before)

            # good, we found a prompt and we couldn't find another prompt after
            # the last one so we should be on the *last* prompt
        elif what == Timeout:
            raise Exception("Prompt not found: the code is taking too long to finish or there is a syntax error. Until now we got (last 1000 bytes):\n%s" % self.irb.before[-1000:])

    def _get_output(self):
        out = "".join(self.last_output)
        self.drop_output()

        # remove any other 'prompt'
        out = re.sub(r'irb[^:]*:\d+:\d+(>|\*) ', '', out)

        # uniform the new line endings (aka universal new lines)
        out = re.sub(r'\r\n', r'\n', out)

        # if there is an output that looks like a traceback,
        # grab the exception's message
        m = self._EXCEPTION_RE.match(out)
        if m is not None:
            out = m.group('msg')

        # TODO: is this ok?
        if out and not out.endswith('\n'):
            out += '\n'

        return out

    def initialize(self):
        self.PS1 = 'irb[^:]*:\d+:0(>|\*) '

        self.irb = pexpect.spawn('/usr/bin/irb', echo=False)
        self.irb.delaybeforesend = 0.010
        self.last_output = []

        self._expect_prompt(timeout=10)
        self.drop_output() # discard banner and things like that

    def drop_output(self):
        self.last_output = []

    def shutdown(self):
        self.irb.sendeof()
        self.irb.close()
        time.sleep(0.01)
        self.irb.terminate(force=True)
