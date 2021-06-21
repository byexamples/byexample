from __future__ import unicode_literals
from byexample.concern import Concern
import byexample.regex as re
from functools import partial
import os

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

    def __init__(self, verbosity, encoding, sharer, options, **unused):
        if sharer is None:
            # we are in the worker thread, let's get a private copy of
            # the environment variables captured (if any)
            # this private copy will ensure that no other worker can
            # change the values or the examples executed (which can
            # change the environment but they will not change this copy)
            # this is a way to make the workers more independent.
            captured = options['captured_env_vars']
            self.envs = {
                name: os.getenv(name, default='')
                for name in captured
            }

    def extend_option_parser(self, parser):
        parser.add_flag(
            "paste",
            default=False,
            help="enable the paste mode of captured texts."
        )
        return parser

    def start(self, examples, runners, filepath, options):
        # get a copy as the default state of the clipboard
        self.clipboard = dict(self.envs)
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
        example.expected_str = re.compile(self.PASTE_RE
                                          ).sub(repl, example.expected_str)

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
        example.source = re.compile(self.PASTE_RE).sub(repl, example.source)

        if missing:
            raise PasteError(example, missing)

    def finally_example(self, example, options):
        got = getattr(example, 'got', None)
        if got == None:
            return  # probably the example failed so we didn't get any output
        _, captured = example.expected.get_captures(example, got, options, 0)
        self.clipboard.update(captured)
