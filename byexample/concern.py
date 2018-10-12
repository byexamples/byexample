from .common import tohuman
from .options import ExtendOptionParserMixin

class Concern(ExtendOptionParserMixin):
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

    Roughly this is the order in which the hooks are called:
     - extend_option_parser
     - start
         - start_parse
             - before_build_regex
         - finish_parse

         - skip_example

         - start_example
         - end_example

         - user_aborted
         - failure
         - success
         - crashed
         - timeout

         - finally_example

         - start_interact
         - finish_interact
     - finish

    See each method's documentation to get an idea of the capabilities of this
    interface.
    '''

    def __repr__(self):
        return '%s Concern' % tohuman(self.target)

    def extend_option_parser(self, parser):
        '''
        See options.ExtendOptionParserMixin.
        By default do not add any new flag.
        '''
        return parser

    def start(self, examples, runners, filepath):
        '''
        Called at the begin of the execution of the given examples
        found in the specific filepath with the given runners.

        The runners are already initialized but no example was built nor
        was executed yet.

        You could use this opportunity to alter the example, or
        even alter the example list (the parameter) in place.
        Or you could inject some code to the given runners
        before running any example.

        Keep in mind that we are talking about examples that are not fully
        parsed yet so you may not get all their attributs.

        If you want to customize the example *after* the parsing stage
        use start_example.
        '''
        pass    # pragma: no cover

    def start_parse(self, example, options):
        '''
        Start the parse of an example to complete it.

        This is called exactly before the Parse object (example.parse_yourself)
        parse and complete the example.
        '''
        pass

    def before_build_regex(self, example, options):
        '''
        Called in the middle of the parsing of an example, after the snippet
        and the expected were extracted and parsed and before building the
        regex from the expected string.

        The example's attributes source, expected_str and options
        are in their final state and could be replaced by you.
        '''
        pass

    def finish_parse(self, example, options, exception):
        '''
        Called after the example was parsed and completed.

        The given exception is a Python exception object if the parse
        fails, None otherwise,

        The reason of a failure during the parsing may be a bug in the example,
        like an invalid option in the example that couldn't be parsed.

        In case of a failure, the example may not be in a consistent state.
        '''
        pass

    def finish(self, failed, user_aborted, crashed, broken, timedout):
        '''
        Called at the end of the execution of the examples
        given in the start call.

        The parameters say if the run execution failed or not
        and if it was aborted by the user, crashed, timedout or the build
        was broken.

        The runners given in start are still up and running
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

        If the example finish (no crash, abort, timeout), eventually the
        finish_example will be called.

        Regardless of the example's result, finally_example will be called.

        You may expect that eventually one of the following methods will
        be called to mark the end of the execution of the example:
         - user_aborted
         - crashed
         - success
         - failure

        And may be, start_interact and finish_interact.
        '''
        pass    # pragma: no cover

    def finish_example(self, example, options):
        '''
        Called when the given example finished its execution normally.

        For example, you could modify example.got, the string captured,
        for sanitization or other enhancement purposes.

        But keep in mind that may exist multiple concern objects and
        the order in which they will be called is undefined, so if two
        or more concern objects edit the same example, you may not always will
        get the same effect.
        '''
        pass    # pragma: no cover

    def finally_example(self, example, options):
        '''
        Called when the given example finished its execution regardless of how.
        '''
        pass    # pragma: no cover

    def start_interact(self, example, options):
        '''
        Called before the user start an interactive session with the
        example's runner/interpreter.

        You may use this opportunity to perform some maintenance tasks
        in the runner/interpreter to make the user life easier.
        '''
        pass    # pragma: no cover

    def finish_interact(self, exception):
        '''
        Called after the interactive session. If something went wrong,
        the exception will be passed, None if everything went fine.
        '''
        pass    # pragma: no cover

    def timedout(self, example, exception):
        '''
        The given example timed out: this may happen because the example
        just ran too slow or because it was syntactically incorrect and
        hang the interpreter.
        '''
        pass    # pragma: no cover

    def user_aborted(self, example):
        '''
        The given example was cancelled and the run execution
        aborted by the user, probably with a ctrl-c (^C) or SIGINT.

        Keep in mind that the abort could happen before the start or
        after finishing the execution (Concern.start and Concern.finish)
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

    def success(self, example, got, differ):
        '''
        Called when an example execution finish and its output is
        what it was expecting or the example was marked to PASS.

        Hurra!
        '''
        pass    # pragma: no cover

    def failure(self, example, got, differ):
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

