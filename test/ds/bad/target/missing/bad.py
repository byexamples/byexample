from byexample.concern import Concern

stability = 'provisional'

class BadTarget(Concern):
   def __init__(self, **kargs):
       Concern.__init__(self, **kargs)
       # 'target' attribute is missing,
       # byexample will complain about this
       assert not hasattr(self, 'target')
