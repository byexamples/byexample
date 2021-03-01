from __future__ import unicode_literals
from .common import enhance_exceptions
from .log import clog, log_context, log_with


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


class FileExecutor(object):
    def __init__(
        self, concerns, differ, verbosity, use_colors, options, **unused
    ):
        self.concerns = concerns
        self.differ = differ
        self.use_colors = use_colors
        self.verbosity = verbosity

        self.options = options

    def initialize_runners(self, runners, options):
        tmp = []
        for runner in runners:
            with log_with(runner.language) as log:
                log.info("Initializing %s", str(runner))
                try:
                    runner.initialize(options)
                    tmp.append(runner)
                except:
                    self.shutdown_runners(tmp, stop_on_failure=False)
                    log.warn("Initialization of %s failed.", str(runner))
                    raise

    def shutdown_runners(self, runners, stop_on_failure=True):
        tmp = list(runners)
        for runner in runners:
            with log_with(runner.language) as log:
                log.info("Shutting down %s", str(runner))
                try:
                    runner.shutdown()
                    del tmp[0]
                except:
                    del tmp[0]
                    if stop_on_failure:
                        self.shutdown_runners(tmp, stop_on_failure=False)

                    log.warn("Shutdown of %s failed.", str(runner))

                    if stop_on_failure:
                        raise

    def __repr__(self):
        return 'File Executor'

    @log_context('byexample.exec')
    def dry_execute(self, examples, filepath):
        for example in examples:
            with enhance_exceptions(example, example.parser, self.use_colors), \
                log_with(runner.language):
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
            self.shutdown_runners(runners)

        return failed, (crashed or broken or timedout), user_aborted, False

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
                     log_with(example.runner.language):
                    # are we in failing fast mode? if we do, skip all the
                    # examples by default
                    if failing_fast:
                        options.up({'skip': True})

                    # load the example's options here to allow it to override
                    # a 'skip' if the user wants to run this even in failing fast
                    # mode
                    options.up(example.options)
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
                            ):
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
                                    'succeded, continuing the execution.' if recovered else \
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
                        options.down()
            except KeyboardInterrupt:  # pragma: no cover
                self.concerns.aborted(example, True, options)
                failed = user_aborted = True
                break

        return failed, user_aborted, crashed, broken, timedout

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
