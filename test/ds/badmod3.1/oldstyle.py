from byexample.runner import ExampleRunner, PexpectMixin
from byexample.concern import Concern

stability = 'experimental'

class BogusOldStyleModule(Concern, PexpectMixin):
    target = 'bogusoldstylemodule'

    def __init__(self, **kargs):
        Concern.__init__(self, **kargs)

        # We cannot inherit from PexpectMixin if we didn't
        # inherit from ExampleRunner.__init__ before
        PexpectMixin.__init__(
            self, PS1_re=r'\(gdb\)[ ]', any_PS_re=r'\(gdb\)[ ]'
        )
