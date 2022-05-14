from __future__ import unicode_literals
from byexample.concern import Concern
import byexample.regex as re
from functools import partial
import os

stability = 'provisional'

class BadConcernNewStyle(Concern):
    target = 'badconcernnewstyle'

    def __init__(self, **kargs):
        # Not calling Concern.__init__ is an error
        self.verbosity = self.cfg.verbosity
        self.encoding = self.cfg.encoding
