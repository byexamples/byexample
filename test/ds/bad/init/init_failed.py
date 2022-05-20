from byexample.concern import Concern

stability = 'provisional'

class BadInit(Concern):
   target = 'badinit'

   def __init__(self, **kargs):
       Concern.__init__(self, **kargs)

       # This will fail and we expect the exception to be caught
       # by byexample initialization process
       print(self.noattr)
