from .common import tohuman

class Hook(object):
    def __repr__(self):
        return '%s Hook' % tohuman(self.target)

    def start_run(self, examples, interpreters, filepath):
        '''
        Called at the begin of the execution of the given examples
        found in the specific filepath with the given interpreters.

        The interpreters are already initialized but no example
        was executed yet.

        You could use this opportunity to alter the examples, or
        even alter the example list (the parameter) in place.
        Or you could inject some code to the given interpreters
        before running any example.
        '''
        pass    # pragma: no cover

    def end_run(self, failed, user_aborted, crashed):
        '''
        Called at the end of the execution of the examples
        given in the start_run call.

        The parameters say if the run execution failed or not
        and if it was aborted by the user or crashed.

        The interpreters given in start_run are still up and running
        but may not be in a consistent state if the user aborted the
        execution or if the interpreter crashed.

        You could perform some clean up task injecting some code
        in the interpreters.
        '''
        pass    # pragma: no cover

    def skip_example(self, example, options):
        '''
        It is the turn for the example to be executed but it will not.
        No other hook method will be called with this example.
        '''
        pass    # pragma: no cover

    def start_example(self, example, options):
        '''
        Called when the given example is about to be executed.

        The options parameters are the union of the example's options
        and the options set before (probably by the user from the command
        line).

        You may expect that eventually one of the following methods will
        be called to mark the end of the execution of the example:
         - user_aborted
         - crashed
         - success
         - failure

        And may be, start_interact and finish_interact.
        '''
        pass    # pragma: no cover

    def start_interact(self, example, options):
        '''
        Called before the user start an interactive session with the
        example's interpreter.

        You may use this opportunity to perform some maintance tasks
        in the interpreter to make the user life easier.
        '''
        pass    # pragma: no cover

    def finish_interact(self, exception):
        '''
        Called after the interactive session. If something went wrong,
        the exception will be passed, None if everything went fine.
        '''
        pass    # pragma: no cover

    def user_aborted(self, example):
        '''
        The given example was cancelled and the run execution
        aborted by the user, probably with a ctrl-c (^C) or SIGINT.
        '''
        pass    # pragma: no cover

    def crashed(self, example, exception):
        '''
        The given example crashed. More formally, the example's interpreter
        crashed.

        The given exception is a Python exception object.

        You could use this to try to debug why the interpreter crashed.
        Most probably is due a bug in the interpreter or in byexample (sorry).
        '''
        pass    # pragma: no cover

    def success(self, example, got, checker):
        '''
        Called when an example execution finish and its output is
        what it was expecting or the example was marked to PASS.

        Hurra!
        '''
        pass    # pragma: no cover

    def failure(self, example, got, checker):
        '''
        Called when an example execution finish but its output wasn't
        expected.
        '''
        pass    # pragma: no cover

class HookComposite(Hook):
    def __init__(self, registry, **unused):
        self.hooks = registry['hooks'].values()

def _patch(cls, method_name):
    def for_each_hook_do(self, *args, **kargs):
        for hook in self.hooks:
            getattr(hook, method_name)(*args, **kargs)

    setattr(cls, method_name, for_each_hook_do)

for method_name in ('start_run', 'end_run',
                    'skip_example', 'start_example',
                    'start_interact', 'finish_interact',
                    'user_aborted', 'crashed',
                    'success', 'failure'):
    _patch(HookComposite, method_name)
