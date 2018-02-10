from .common import tohuman

class Concern(object):
    '''
    Cross-cutting Concern interface.

    Set of methods that will be called through the different stages
    of the execution of ``byexample``.
    Each method (also known as 'hook') will allow you to read the current
    state and even to change it.

    Use this mechanism to implement the following (but not limited to):
     - show the progress of the execution
     - log / report generation for export
     - log execution time history for future execution time prediction (estimate)
     - turn on/off debugging, coverage and profile facilities

    See each method's documentation to get an idea of the capabilities of this
    interface.
    '''

    def __repr__(self):
        return '%s Concern' % tohuman(self.target)

    def start_run(self, examples, runners, filepath):
        '''
        Called at the begin of the execution of the given examples
        found in the specific filepath with the given runners.

        The runners are already initialized but no example
        was executed yet.

        You could use this opportunity to alter the examples, or
        even alter the example list (the parameter) in place.
        Or you could inject some code to the given runners
        before running any example.
        '''
        pass    # pragma: no cover

    def end_run(self, failed, user_aborted, crashed):
        '''
        Called at the end of the execution of the examples
        given in the start_run call.

        The parameters say if the run execution failed or not
        and if it was aborted by the user or crashed.

        The runners given in start_run are still up and running
        but may not be in a consistent state if the user aborted the
        execution or if the runner crashed.

        You could perform some clean up task injecting some code
        in the runners.
        '''
        pass    # pragma: no cover

    def skip_example(self, example, options):
        '''
        It is the turn for the example to be executed but it will not.
        No other concern's method will be called with this example.
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
        example's runner/interpreter.

        You may use this opportunity to perform some maintance tasks
        in the runner/interpreter to make the user life easier.
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
        The given example crashed. More formally, the example's runner
        crashed.

        The given exception is a Python exception object.

        You could use this to try to debug why the runner crashed.
        Most probably is due a bug in the runner or in byexample (sorry).
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

class ConcernComposite(Concern):
    def __init__(self, registry, **unused):
        self.concerns = registry['concerns'].values()

# Patch ConcernComposite overriding all its methods
# For a given method X, ConcernComposite will call X on all of
# its sub-concerns.
import inspect
def _patch(cls, method_name):
    def for_each_concern_do(self, *args, **kargs):
        for concern in self.concerns:
            getattr(concern, method_name)(*args, **kargs)

    setattr(cls, method_name, for_each_concern_do)

def _patchable(obj):
    # In Python 3, the class's methods are actually functions
    # so we need to check for both types
    return (inspect.isfunction(obj) or inspect.ismethod(obj)) \
            and not obj.__name__.startswith("_")

for method_name, _ in inspect.getmembers(Concern, predicate=_patchable):
    _patch(ConcernComposite, method_name)

