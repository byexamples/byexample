'''
Javascript code (using nodejs).

Inside of a Markdown Fenced Code:

```javascript
1 + 2;

out:
3
```

The "out:" label marks the begin of the expected output to compare.

The semicolons are optional (as long as they are syntactically correct):

```javascript
'hello' + ' ' + 'world'

out:
'hello world'
```

Prompt based is allowed too using '>' as the first prompt
and '.' as the second prompt:

> function mul(a, b) {
.   return a * b;
. }

> mul(4, 2)
8


'''

import re
from byexample.common import constant, abspath
from byexample.parser import ExampleParser
from byexample.finder import ExampleFinder
from byexample.runner import ExampleRunner, PexepctMixin, ShebangTemplate

stability = 'experimental'

class JavascriptPromptFinder(ExampleFinder):
    target = 'javascript-prompt'

    @constant
    def example_regex(self):
        return re.compile(r'''
            (?P<snippet>
                (?:^(?P<indent> [ ]*) (?:>)[ ]  .*)           # PS1 line
                (?:\n           [ ]*  \.[ ]             .*)*)    # PS2 lines
            \n?
            ## Want consists of any non-blank lines that do not start with PS1
            (?P<expected> (?:(?![ ]*$)        # Not a blank line
                          (?![ ]*(?:>))      # Not a line starting with PS1
                          .+$\n?              # But any other line
                      )*)
            ''', re.MULTILINE | re.VERBOSE)

    def get_language_of(self, *args, **kargs):
        return 'javascript'

    def get_snippet_and_expected(self, match, where):
        snippet, expected = ExampleFinder.get_snippet_and_expected(self, match, where)

        snippet = self._remove_prompts(snippet)
        return snippet, expected

    def _remove_prompts(self, snippet):
        lines = snippet.split("\n")
        return '\n'.join(line[2:] for line in lines)

class JavascriptParser(ExampleParser):
    language = 'javascript'

    @constant
    def example_options_string_regex(self):
        return re.compile(r'//\s*byexample:\s*([^\n\'"]*)$',
                                                    re.MULTILINE)

    def extend_option_parser(self, parser):
        pass

class JavascriptInterpreter(ExampleRunner, PexepctMixin):
    language = 'javascript'

    def __init__(self, verbosity, encoding, **unused):
        PexepctMixin.__init__(self,
                                PS1_re = r'node > ',
                                any_PS_re = r'(?:node > )|(?:\.\.\. )')

        self.encoding = encoding

    def run(self, example, flags):
        return self._exec_and_wait(example.source, timeout=int(flags['timeout']))

    def interact(self, example, options):
        PexepctMixin.interact(self)

    def get_default_cmd(self, *args, **kargs):
        return  "%e %p %a", {
                    'e': '/usr/bin/env',
                    'p': 'nodejs',
                    'a': [abspath(__file__, 'byexample-repl.js')]
                    }

    def initialize(self, options):
        shebang, tokens = self.get_default_cmd()
        shebang = options['shebangs'].get(self.language, shebang)

        cmd = ShebangTemplate(shebang).quote_and_substitute(tokens)

        # run!
        self._spawn_interpreter(cmd, delaybeforesend=options['delaybeforesend'],
                                     geometry=options['geometry'])

        self._drop_output() # discard banner and things like that

    def shutdown(self):
        self._shutdown_interpreter()
