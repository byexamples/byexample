from byexample.concern import Concern

stability = 'provisional'

class BadTarget(Concern):
   def __init__(self, **kargs):
       super().__init__(**kargs)
       # 'target' attribute is missing,
       # byexample will complain about this
       assert not hasattr(self, 'target')
