from __future__ import unicode_literals
from byexample.concern import Concern
import re
from functools import partial

stability = 'provisional'


class PasteError(Exception):
    def __init__(self, example, missing):
        n = "tag is" if len(missing) == 1 else "tags are"
        msg = "You enabled the 'paste' mode and I found some tags\nthat you did not captured before:\n  %s" \
              "\nMay be the example from where you copied was skipped or" \
              "\nmay be the %s misspelled." % (', '.join(missing), n)

        Exception.__init__(self, msg)


class Clipboard(Concern):
    target = 'clipboard'

    def __init__(self, verbosity, encoding, **unused):
        pass

    def extend_option_parser(self, parser):
        parser.add_flag(
            "paste",
            default=False,
            help="enable the paste mode of captured texts."
        )
        return parser

    def start(self, examples, runners, filepath, options):
        self.clipboard = {}
        options['clipboard'] = self.clipboard

    @staticmethod
    def repl_from_clipboard(m, clipboard, missing):
        tag_name = m.groupdict()['name']
        try:
            return clipboard[tag_name]
        except KeyError:
            missing.append(tag_name)
            return m.group(0)  # replace it by itself.

    PASTE_RE = re.compile(r"<(?P<name>(?:\w|-|\.)+)>")

    def before_build_regex(self, example, options):
        if not options['paste']:
            return

        repl = partial(
            self.repl_from_clipboard, clipboard=self.clipboard, missing=[]
        )
        example.expected_str = re.sub(
            self.PASTE_RE, repl, example.expected_str
        )

        # do not check for missings: we assume that they are capture tags

    def finish_parse(self, example, options, exception):
        if exception is not None:
            return

        options.up(example.options)
        paste = options['paste']
        options.down()

        if not paste:
            return

        missing = []
        repl = partial(
            self.repl_from_clipboard,
            clipboard=self.clipboard,
            missing=missing
        )
        example.source = re.sub(self.PASTE_RE, repl, example.source)

        if missing:
            raise PasteError(example, missing)

    def finally_example(self, example, options):
        got = getattr(example, 'got', None)
        if got == None:
            return  # probably the example failed so we didn't get any output
        _, captured = example.expected.get_captures(example, got, options, 0)
        self.clipboard.update(captured)
