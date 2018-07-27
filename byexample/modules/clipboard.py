from byexample.concern import Concern
import re
from functools import partial

stability = 'experimental'

class PasteError(Exception):
    def __init__(self, example, missing):
        msg = "You enabled the 'paste' mode and I found some tags that you did not captured before." \
              "\nMay be it is a misspelling of: %s" % ', '.join(missing)

        Exception.__init__(self, msg)

class Clipboard(Concern):
    target = 'clipboard'

    def __init__(self, verbosity, encoding, **unused):
        pass

    def extend_option_parser(self, parser):
        parser.add_flag("paste", help="enable the paste mode of captured texts.")
        return parser

    def start(self, examples, runners, filepath):
        self.clipboard = {}

    @staticmethod
    def repl_from_clipboard(m, clipboard, missing):
        tag_name = m.groupdict()['name']
        try:
            return clipboard[tag_name]
        except KeyError:
            missing.append(tag_name)
            return m.group(0)   # replace it by itself.

    PASTE_RE = re.compile(r"<(?P<name>(?:\w|-|\.)+)>")
    def before_build_regex(self, example, options):
        if not options.get('paste', False):
            return

        repl = partial(self.repl_from_clipboard, clipboard=self.clipboard,
                                                 missing=[])
        example.expected_str = re.sub(self.PASTE_RE, repl, example.expected_str)

        # do not check for missings: we assume that they are capture tags

    def start_example(self, example, options):
        if not options.get('paste', False):
            return

        missing = []
        repl = partial(self.repl_from_clipboard, clipboard=self.clipboard,
                                                 missing=missing)
        example.source = re.sub(self.PASTE_RE, repl, example.source)

        if missing:
            raise PasteError(example, missing)


    def finally_example(self, example, options):
        got = getattr(example, 'got', None)
        if got == None:
            return  # probably the example failed so we didn't get any output
        _, captured = example.expected.get_captures(example, got, options, 0)
        self.clipboard.update(captured)

