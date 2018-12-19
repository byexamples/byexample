from __future__ import unicode_literals
import re
from byexample.finder import ZoneDelimiter
from byexample.common import constant

stability = 'experimental'

class NoDelimiter(ZoneDelimiter):
    target = 'no-delimiter'

    @constant
    def zone_regex(self):
        return re.compile(r'\A(?P<zone>.*)\Z', re.DOTALL | re.MULTILINE)

    def __repr__(self):
        return "No Zone Delimiter"
