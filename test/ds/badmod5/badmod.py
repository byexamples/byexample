from byexample.concern import Concern

stability = 'provisional'

class BogusModule(Concern):
   target = ['bogusmodule']

   def __init__(self, **kargs):
       super().__init__(**kargs)
