from byexample.concern import Concern
import multiprocessing

class SubMod(Concern):
    target = 'submod'

    def __init__(self, prepare_subprocess_call, **kargs):
        super().__init__(prepare_subprocess_call=prepare_subprocess_call, **kargs)
        # keep a reference to this function helper
        self.prepare_subprocess_call = prepare_subprocess_call

    @classmethod
    def watch_in_bg(cls, foo, bar):
        print("--->", foo, bar)

    def start_example(self, *args):
        # prepare_subprocess_call takes the 'target' function
        # and an optional 'args' and 'kwargs' arguments
        # like multiprocessing.Process does.
        #
        # it will return a dictionary that be unpacked
        # with the double '**' directly into multiprocessing.Process
        # call
        ctx = multiprocessing.get_context('spawn')
        self.child = ctx.Process(
                    **self.prepare_subprocess_call(
                            target=SubMod.watch_in_bg,
                            args=(42,),
                            kwargs={'bar': 'bg'}
                        )
                    )
        self.child.start() # Start the child process as usual

    def end_example(self, *args):
        self.child.join()

