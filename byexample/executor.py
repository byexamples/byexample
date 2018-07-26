from .common import log, print_example, print_execution, enhance_exceptions

class TimeoutException(Exception):
    pass

class FileExecutor(object):
    def __init__(self, concerns, differ, verbosity, use_colors, options, **unused):
        self.concerns   = concerns
        self.differ    = differ
        self.use_colors = use_colors
        self.verbosity  = verbosity

        self.options = options

    def initialize_runners(self, runners, options):
        log("Initializing %i runners..." % len(runners),
                                                    self.verbosity-1)
        for runner in runners:
            log(" - %s" % str(runner), self.verbosity-1)
            runner.initialize(options)

    def shutdown_runners(self, runners):
        log("Shutting down %i runners..." % len(runners),
                                                    self.verbosity-1)
        for runner in runners:
            log(" - %s" % str(runner), self.verbosity-1)
            runner.shutdown()

    def __repr__(self):
        return 'File Executor'

    def dry_execute(self, examples, filepath):
        for example in examples:
            with enhance_exceptions(example, example.parser, self.use_colors):
                # build but ignore any output; even do not use the concerns
                example.parse_yourself(concerns=None)

    def execute(self, examples, filepath):
        options = self.options
        runners = list(set(e.runner for e in examples))

        self.initialize_runners(runners, options)
        try:
            self.concerns.start(examples, runners, filepath)
            failed, user_aborted, crashed, broken = self._exec(examples, filepath,
                                                               options, runners)
            self.concerns.finish(failed, user_aborted, crashed, broken)
        finally:
            self.shutdown_runners(runners)

        return failed, (user_aborted or crashed or broken)

    def _exec(self, examples, filepath, options, runners):
        fail_fast = options['fail_fast']

        failed = False
        user_aborted = False
        crashed = False
        timedout = False
        broken = False
        for example in examples:
            example = self._parse(example, options)

            if example == None:
                broken = True
                break   # always fail fast if an example couldn't get parsed

            with enhance_exceptions(example, self, self.use_colors):
                options.up(example.options)
                try:
                    if options['skip']:
                        self.concerns.skip_example(example, options)
                        continue

                    print_example(example, True, self.verbosity-3)
                    self.concerns.start_example(example, options)
                    try:
                        with enhance_exceptions(example, example.runner, self.use_colors):
                            example.got = example.runner.run(example, options)
                        self.concerns.finish_example(example, options)
                    except TimeoutException as e:  # pragma: no cover
                        example.got = "**Execution timed out**\n" + str(e)
                        timedout = True
                    except KeyboardInterrupt:      # pragma: no cover
                        self.concerns.user_aborted(example)
                        user_aborted = True
                    except Exception as e:         # pragma: no cover
                        self.concerns.crashed(example, e)
                        crashed = True
                    finally:
                        self.concerns.finally_example(example, options)

                    if user_aborted or crashed:    # pragma: no cover
                        failed = True
                        break # always fail fast if the user aborted or code crashed

                    # cache this *after* calling finish_example/finally_example
                    # those two may modify the got
                    got = example.got

                    print_execution(example, got, self.verbosity-3)

                    # We can pass the test regardless of the output
                    # however, a Timeout is always a fail
                    force_pass = options['pass']
                    if not timedout and \
                            (force_pass or example.expected.check_got_output(example, got, options, self.verbosity)):
                        self.concerns.success(example, got, self.differ)
                    else:
                        self.concerns.failure(example, got, self.differ)
                        failed = True

                        # start an interactive session if the example fails
                        # and the user wanted this
                        if options['interact'] and not timedout:
                            self.concerns.start_interact(example, options)
                            ex = None
                            try:
                                example.runner.interact(example, options)
                            except Exception as e:
                                ex = e

                            self.concerns.finish_interact(ex)

                        # fail fast if the user want this or
                        # if we got a Timeout
                        if fail_fast or timedout:
                            break
                finally:
                    # allow the garbage collector to collect the example,
                    # do not keep it in memory
                    del example
                    options.down()

        return failed, user_aborted, crashed, broken

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
