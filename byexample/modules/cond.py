from __future__ import unicode_literals
from byexample.concern import Concern
from functools import partial

stability = 'experimental'


class UnknownConditionTag(Exception):
    def __init__(self, example, missing):
        msg = "You enabled the conditional execution of this example "     \
              "based on the tag that *is not* in the clipboard.\n"          \
              "May be the example from where you capture it was skipped,"   \
              "may be the tag '%s' is misspelled or may be the Clipboard "  \
              "was disabled." % (missing)

        Exception.__init__(self, msg)


class Conditional(Concern):
    target = 'conditional'

    def extend_option_parser(self, parser):
        mutexg = parser.add_mutually_exclusive_group()
        mutexg.add_argument(
            "+if",
            "+on",
            metavar='<tag>',
            nargs=1,
            default=False,
            help=
            "run the example only if the tag is non-empty; skip the example otherwise."
        )
        mutexg.add_argument(
            "+unless",
            metavar='<tag>',
            nargs=1,
            default=True,
            help=
            "run the example unless the tag is non-empty; skip the example otherwise."
        )
        return parser

    def finish_parse(self, example, options, exception):
        if exception is not None:
            return

        options.up(example.options)
        ifcond = options['if']
        uncond = options['unless']
        options.down()

        if ifcond is not False:
            cond = ifcond[0]
            neg = True
        elif uncond is not True:
            cond = uncond[0]
            neg = False
        else:
            return

        clipboard = options.get('clipboard', {})
        if cond not in clipboard:
            raise UnknownConditionTag(example, cond)

        skip = bool(
            clipboard[cond]
        )  # TODO emptiness is enough?: what about strings like '0' and 'false'?
        if neg:
            skip = not skip

        if skip:
            example.options['skip'] = True
