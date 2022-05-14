from __future__ import unicode_literals
from byexample.concern import Concern
import byexample.regex as re
from functools import partial
import os

stability = 'provisional'

class BadConcern(Concern):
    target = 'badconcern'

    def __init__(self, verbosity, encoding, **kargs):
        # Not calling Concern.__init__ is an error
        self.verbosity = verbosity
        self.encoding = encoding
