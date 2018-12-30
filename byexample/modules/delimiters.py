from __future__ import unicode_literals
import re
from byexample.finder import ZoneDelimiter
from byexample.common import constant

stability = 'provisional'

class NoDelimiter(ZoneDelimiter):
    target = 'no-delimiter'

    @constant
    def zone_regex(self):
        return re.compile(r'\A(?P<zone>.*)\Z', re.DOTALL | re.MULTILINE)

    def __repr__(self):
        return "No Zone Delimiter"


class CppCommentDelimiter(ZoneDelimiter):
    target = {'.cpp', '.c', '.h', '.hpp', '.js'}

    @constant
    def zone_regex(self):
        return re.compile(r'''
            # Begin with a /* marker
            ^[ ]*
             /\*

             # then, grab everything
             (?P<zone>.*?)

             # and the close marker
             \*/
            ''', re.DOTALL | re.MULTILINE | re.VERBOSE)

    @constant
    def leading_asterisk(self):
        return re.compile(r'^[ \*]+(?=[^ \*]|$)', re.MULTILINE)

    def get_zone(self, match, where):
        zone = ZoneDelimiter.get_zone(self, match, where)
        return self.leading_asterisk().sub(' ', zone)

    def __repr__(self):
        return "/* ... */"

class HashCommentDelimiter(ZoneDelimiter):
    target = {'.rb'}

    @constant
    def zone_regex(self):
        return re.compile(r'''
            # Begin with a # marker
            ^[ ]*
             \#

             # then, grab everything that begins with a #
             # until we cannot do it anymore
             (?P<zone>  .*$\n?                  # first line
                        (?:[ ]* \# .*$\n?)*     # the rest of the lines
                    )
            ''', re.MULTILINE | re.VERBOSE)

    @constant
    def leading_sharp(self):
        return re.compile(r'^[ ]*#', re.MULTILINE)

    def get_zone(self, match, where):
        zone = ZoneDelimiter.get_zone(self, match, where)
        return self.leading_sharp().sub(' ', zone)

    def __repr__(self):
        return "# ..."

class DocStringDelimiter(ZoneDelimiter):
    target = {'.py'}

    @constant
    def zone_regex(self):
        return re.compile(r'''
            # Begin with a triple single or double quote
            ^[ ]*
             [bBuU]?[rR]?(?P<marker>(?:\'\'\') | (?:"""))

             # then, grab everything until the first end marker
             (?P<zone>.*?)

             # finally, the end marker
             [^\\](?P=marker) # then we must match the same kind of quotes
            ''', re.DOTALL | re.MULTILINE | re.VERBOSE)

    def __repr__(self):
        return "''' ... ''' or \"\"\" ... \"\"\""

class MarkdownFencedCodeDelimiter(ZoneDelimiter):
    target = {'.md'}

    @constant
    def zone_regex(self):
        return re.compile(r'''
            # Begin with a markdown fenced-code marker or a html comment marker
            ^[ ]*
                (?:
                    (?P<marker>```(?:``)*(?=[^`]))  # fenced-code marker (backticks)
                    | (?:<!--)              # or the html comment marker
                )

            # then, grab everything until the first end marker
            (?P<zone>.*?)

            # finally, the end marker
            (?(marker)    # if we matched a fenced-code maker previously
                  ^[ ]*(?P=marker) # then we must match the same amount of backticks
                  |(?:-->)    # otherwise, we must match the close of the html comment
            )
            ''', re.DOTALL | re.MULTILINE | re.VERBOSE)

    def __repr__(self):
        return "``` ... ``` or <!-- ... -->"
