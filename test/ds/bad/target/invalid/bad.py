from byexample.concern import Concern

stability = 'provisional'

class BadTarget(Concern):
   # This is wrong, a target cannot be a list.
   target = ['bogusmodule']

   def __init__(self, **kargs):
       super().__init__(**kargs)
