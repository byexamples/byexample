from __future__ import unicode_literals
from .common import enhance_exceptions
from .log import clog, log_context, log_with
from .prof import profile, profile_ctx
import contextlib


class TimeoutException(Exception):
    def __init__(self, msg, output):
        Exception.__init__(self, msg)
        self.output = output


class InputPrefixNotFound(TimeoutException):
    def __init__(self, prefix, input, timeout_exc):
        msg = "The text before typing '%s' was not found. Expected '%s' but found '%s'"
        msg = msg % (input, prefix, timeout_exc.output)
        TimeoutException.__init__(self, msg, timeout_exc.output)

        self.prefix, self.input = prefix, input


class InterpreterClosedUnexpectedly(Exception):
    def __init__(self, msg, output):
        Exception.__init__(self, msg)
        self.output = output


class InterpreterNotFound(Exception):
    def __init__(self, msg, runner_cmd):
        Exception.__init__(self, msg)
        self.runner_cmd = runner_cmd


r'''
>>> from byexample.runner import ExampleRunner
>>> from byexample.executor import FileExecutor

>>> from byexample.log import init_log_system
>>> init_log_system()

>>> class Buggy(ExampleRunner):
...     def __init__(self, name, bug_in):
...         self.language = self.name = name
...         self.bug_in = bug_in
...     def run(self, example, options):
...         print("run()", self.name)
...         if self.bug_in == 'run':
...             raise Exception("Faked on %s of %s" % (self.bug_in, self.name))
...     def initialize(self, options):
...         print("initialize()", self.name)
...         if self.bug_in == 'initialize':
...             raise Exception("Faked on %s of %s" % (self.bug_in, self.name))
...     def shutdown(self):
...         print("shutdown()", self.name)
...         if self.bug_in == 'shutdown':
...             raise Exception("Faked on %s of %s" % (self.bug_in, self.name))
...     def reset(self, options):
...         print("reset()", self.name)
...         if self.bug_in == 'reset':
...             raise Exception("Faked on %s of %s" % (self.bug_in, self.name))

>>> fexec = FileExecutor(None, None, None, None, None)

FileExecutor will initialize the runners in order, stopping on the
first failure and shutting down any previous initialized runner (if any).

In this case 'not-buggy1' should never being called because the first
runner will fail in the 'initialize' phase.

>>> runners = [Buggy("buggy1", "initialize"), Buggy("not-buggy1", "never")]

>>> fexec.initialize_runners(runners, None)
initialize() buggy1
[w] Initialization of Buggy1 Runner failed.
Traceback (most recent call last):
<...>
Exception: Faked on initialize of buggy1

But if we change the order, initialize() of 'not-buggy1' is called
but on the failure of 'buggy1', the shutdown() is called too.

>>> runners = [Buggy("not-buggy1", "never"), Buggy("buggy1", "initialize")]
>>> fexec.initialize_runners(runners, None)
initialize() not-buggy1
initialize() buggy1
shutdown() not-buggy1
[w] Initialization of Buggy1 Runner failed.
Traceback (most recent call last):
<...>
Exception: Faked on initialize of buggy1

If an exception is raised during a shutdown when the initialize() was
aborted, the call to the shutdown()s is not stopped and only the first
exception is raised (the other are just logged).

Note the order of the calls to shutdown(): the reverse order of the calls
to initialize() (like a stack).

>>> runners = [Buggy("not-buggy1", "never"), Buggy("buggy2", "shutdown"), Buggy("buggy1", "initialize")]
>>> fexec.initialize_runners(runners, None)
initialize() not-buggy1
initialize() buggy2
initialize() buggy1
shutdown() buggy2
[w] Shutdown of Buggy2 Runner failed.
shutdown() not-buggy1
[w] Initialization of Buggy1 Runner failed.
Traceback (most recent call last):
<...>
Exception: Faked on initialize of buggy1

On reset/shutdown we have a similar situation except that reset_runners
receives the list of runners and it is caller's responsibility (us) to
pass a reversed list to have the same stack-like de-initialization order.

>>> runners = [Buggy("not-buggy1", "never"), Buggy("buggy1", "shutdown"), Buggy("buggy2", "shutdown")]
>>> fexec.initialize_runners(runners, None)
initialize() not-buggy1
initialize() buggy1
initialize() buggy2

>>> fexec.reset_runners(list(reversed(runners)))
shutdown() buggy2
shutdown() buggy1
[w] Shutdown of Buggy1 Runner failed.
shutdown() not-buggy1
[w] Shutdown of Buggy2 Runner failed.
Traceback (most recent call last):
<...>
Exception: Faked on shutdown of buggy2

Note: no tests nor documentation about 'reset' is done yet.

>>> fexec.close()   # byexample: -skip
'''


class FileExecutor(object):
    def __init__(
        self, concerns, differ, verbosity, use_colors, options, **unused
    ):
        self.concerns = concerns
        self.differ = differ
        self.use_colors = use_colors
        self.verbosity = verbosity

        self.options = options
        self.still_alive_runners = set()

    @contextlib.contextmanager
    def on_failure_shutdown_runners(
        self, should_raise, runners_left, log, err_args
    ):
        try:
            yield
        except:
            if should_raise:
                # should_raise is False because we want to raise only the first
                # exception (the current one)
                self.reset_runners(
                    runners_left, should_raise=False, force_shutdown=True
                )

            log.warn(*err_args)

            if should_raise:
                raise

    @profile
    def initialize_runners(self, runners, options):
        # in case of an error, these are the runners initialized so far
        # that we must shutdown
        so_far = []
        for runner in runners:
            with log_with(runner.language) as log:
                if runner in self.still_alive_runners:
                    log.info("Reusing %s", str(runner))
                    so_far.append(runner)
                    continue

                log.info("Initializing %s", str(runner))
                with self.on_failure_shutdown_runners(
                    should_raise=True,
                    runners_left=list(reversed(so_far)),
                    log=log,
                    err_args=("Initialization of %s failed.", str(runner))
                ):
                    runner.initialize(options)
                    self.still_alive_runners.add(runner)
                    so_far.append(runner)

        # or we have all of them or we should not be executing this line
        # because something failed and an exception should be flying around
        assert len(so_far) == len(runners)

        # the 'equal or greater than' is needed because some runners may had
        # been initialized in another round and they are not going to be used
        # in this one
        assert len(self.still_alive_runners) >= len(runners)

    @profile
    def reset_runners(self, runners, should_raise=True, force_shutdown=True):
        # in case of an error, these are the runners that we must shutdown
        left = list(runners)
        for runner in runners:
            with log_with(runner.language) as log:
                assert runner in self.still_alive_runners
                if not force_shutdown:
                    with self.on_failure_shutdown_runners(
                        should_raise=should_raise,
                        runners_left=left,
                        log=log,
                        err_args=("Reset of %s failed.", str(runner))
                    ):
                        if runner.reset():
                            del left[0]
                            log.info("Reset of %s succeeded.", str(runner))
                            continue

                # Reset is not available or it failed, try to shutdown
                # It is ok to try a shutdown if the reset failed because:
                #  - if it is the first failure, the on_failure_shutdown_runners
                #  would already shutdown the runners *AND* raise and exception
                #  so we would *not* be executing this
                #  - if it is the non-first failure, we are in a recursive call
                #  where on_failure_shutdown_runners did *not* shutdown anything
                #  and we have to do it.
                del left[0]
                self.still_alive_runners.remove(runner)

                log.info("Shutting down %s", str(runner))
                with self.on_failure_shutdown_runners(
                    should_raise=should_raise,
                    runners_left=left,
                    log=log,
                    err_args=("Shutdown of %s failed.", str(runner))
                ):
                    runner.shutdown()

        assert not left

    @log_context('byexample.close')
    def close(self):
        # no order is guaranteed
        self.reset_runners(
            list(self.still_alive_runners),
            should_raise=True,
            force_shutdown=True
        )

    def __repr__(self):
        return 'File Executor'

    @log_context('byexample.exec')
    def dry_execute(self, examples, filepath):
        clog().info('File %s, %i examples.', filepath, len(examples))
        for example in examples:
            with enhance_exceptions(example, example.parser, self.use_colors), \
                log_with(example.runner.language):
                # build but ignore any output; even do not use the concerns
                example.parse_yourself(concerns=None)

        return False, False, False, False

    @log_context('byexample.exec')
    def execute(self, examples, filepath):
        options = self.options
        runners = list(set(e.runner for e in examples))

        self.initialize_runners(runners, options)
        try:
            self.concerns.start(examples, runners, filepath, options)
            failed, user_aborted, crashed, broken, timedout = self._exec(
                examples, filepath, options, runners
            )
            self.concerns.finish(
                failed, user_aborted, crashed, broken, timedout
            )
        finally:
            self.reset_runners(runners)

        return failed, (crashed or broken or timedout), user_aborted, False

    @profile
    def _exec(self, examples, filepath, options, runners):
        failing_fast = False
        failed = False
        user_aborted = False
        crashed = False
        timedout = False
        broken = False
        for example in examples:
            try:
                with log_with(example.runner.language):
                    example = self._parse(example, options)

                    if example == None:
                        broken = True
                        break  # cancel if an example couldn't get parsed

                with enhance_exceptions(example, self, self.use_colors), \
                     log_with(example.runner.language), \
                     profile_ctx("inner"):
                    # are we in failing fast mode? if we do, skip all the
                    # examples by default
                    if failing_fast:
                        options.up({'skip': True})

                    # load the example's options here to allow it to override
                    # a 'skip' if the user wants to run this even in failing fast
                    # mode
                    options.up(example.options)
                    example.current_options = options
                    try:
                        # ask to the example if we should fail fast if it fails
                        # no matter what the user said from the command line
                        fail_fast = options['fail_fast']

                        if options['skip']:
                            clog().chat('Skip', example=example)
                            self.concerns.skip_example(example, options)
                            continue

                        clog().chat(
                            'ex:', example=example, disable_prefix=True
                        )
                        self.concerns.start_example(example, options)
                        try:
                            with enhance_exceptions(
                                example, example.runner, self.use_colors
                            ), \
                                    profile_ctx("run"):
                                example.got = example.runner.run(
                                    example, options
                                )
                            self.concerns.finish_example(example, options)
                        except TimeoutException as e:  # pragma: no cover
                            self.concerns.timedout(example, e)
                            timedout = True
                        except Exception as e:  # pragma: no cover
                            self.concerns.crashed(example, e)
                            crashed = True
                        finally:
                            self.concerns.finally_example(example, options)

                        recovered = False
                        if timedout and not options['x']['not_recover_timeout']:
                            # try to recover the control of the runner
                            clog().warn(
                                'Example timed out. Trying to recovering the control (%s)...',
                                example.runner.language
                            )
                            recovered = example.runner.cancel(example, options)
                            clog().warn('Recovering control of %s %s',
                                    example.runner.language,
                                    'succeeded, continuing the execution.' if recovered else \
                                            'failed.')

                        if crashed or (timedout and not recovered):
                            failed = True
                            self.concerns.aborted(example, False, options)
                            break  # cancel, the runner is in an undefined state

                        if timedout and recovered:
                            # we did not get the output from the example,
                            # so we basically "failed"
                            timedout = False
                            failed = True
                        else:
                            # cache this *after* calling finish_example/finally_example
                            # those two may modify the got
                            got = example.got
                            clog().debug(got)

                            # We can pass the test regardless of the output
                            force_pass = options['pass']
                            if force_pass or \
                                    example.expected.check_got_output(example, got, options, self.verbosity):
                                self.concerns.success(
                                    example, got, self.differ
                                )
                            else:
                                self.concerns.failure(
                                    example, got, self.differ
                                )
                                failed = True

                                # start an interactive session if the example fails
                                # and the user wanted this
                                if options['interact']:
                                    self.concerns.start_interact(
                                        example, options
                                    )
                                    ex = None
                                    try:
                                        example.runner.interact(
                                            example, options
                                        )
                                    except Exception as e:
                                        ex = e

                                    self.concerns.finish_interact(ex)

                        # enter in failing fast mode if the user wants and the
                        # example failed
                        if fail_fast and failed:
                            failing_fast = True
                            options.up(
                                {'skip': True}
                            )  # dummy, but it allows a symmetric relationship between failing_fast and an extra up
                    finally:
                        if failing_fast:
                            options.down()

                        # allow the garbage collector to collect the example's got,
                        # do not keep it in memory
                        if hasattr(example, 'got'):
                            del example.got
                        del example.current_options
                        options.down()
            except KeyboardInterrupt:  # pragma: no cover
                self.concerns.aborted(example, True, options)
                failed = user_aborted = True
                break

        return failed, user_aborted, crashed, broken, timedout

    @profile
    def _parse(self, example, options):
        try:
            with enhance_exceptions(example, example.parser, self.use_colors):
                self.concerns.start_parse(example, options)
                example = example.parse_yourself(self.concerns)
                self.concerns.finish_parse(example, options, None)

            return example
        except Exception as e:
            self.concerns.finish_parse(example, options, e)
            return None
