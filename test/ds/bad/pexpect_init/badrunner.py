from byexample.runner import ExampleRunner, PexpectMixin

stability = 'experimental'

class BadRunner(ExampleRunner, PexpectMixin):
    language = 'badrunner'

    def __init__(self, **kargs):
        # Calling PexpectMixin before ExampleRunner.__init__ is an error
        PexpectMixin.__init__(
            self, PS1_re=r'\(gdb\)[ ]', any_PS_re=r'\(gdb\)[ ]'
        )

        super(ExampleRunner, self).__init__(**kargs)

