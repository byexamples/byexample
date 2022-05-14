from byexample.concern import Concern

stability = 'provisional'

class BadInit(Concern):
   target = 'badinit'

   def __init__(self, **kargs):
       super().__init__(**kargs)

       # This will fail and we expect the exception to be caught
       # by byexample initialization process
       print(self.noattr)
