from .common import log, build_exception_msg, print_example, print_execution

class TimeoutException(Exception):
    pass

class ExampleRunner(object):
    def __init__(self, concerns, checker, verbosity, use_colors, **unused):
        self.concerns   = concerns
        self.checker    = checker
        self.use_colors = use_colors
        self.verbosity  = verbosity

    def initialize_interpreters(self, interpreters, examples, options):
        log("Initializing %i interpreters..." % len(interpreters),
                                                    self.verbosity-1)
        for interpreter in interpreters:
            log(" - %s" % str(interpreter), self.verbosity-1)
            interpreter.initialize(examples, options)

    def shutdown_interpreters(self, interpreters):
        log("Shutting down %i interpreters..." % len(interpreters),
                                                    self.verbosity-1)
        for interpreter in interpreters:
            log(" - %s" % str(interpreter), self.verbosity-1)
            interpreter.shutdown()

    def run(self, examples, options, filepath):
        interpreters = list(set(e.interpreter for e in examples))

        self.initialize_interpreters(interpreters, examples, options)
        self.concerns.start_run(examples, interpreters, filepath)

        fail_fast = options['FAIL_FAST']

        failed = False
        user_aborted = False
        crashed = False
        timedout = False
        for example in examples:
            options.up(example.options)
            try:
                if options['SKIP']:
                    self.concerns.skip_example(example, options)
                    continue

                print_example(example, True, self.verbosity-3)
                self.concerns.start_example(example, options)
                try:
                    got = example.interpreter.run(example, options)
                except TimeoutException as e:  # pragma: no cover
                    got = "**Execution timed out**\n" + str(e)
                    timedout = True
                except KeyboardInterrupt:      # pragma: no cover
                    self.concerns.user_aborted(example)
                    user_aborted = True
                except Exception as e:         # pragma: no cover
                    self.concerns.crashed(example, e)
                    crashed = True

                if user_aborted or crashed:    # pragma: no cover
                    failed = True
                    break # always fail fast if the user aborted or code crashed

                print_execution(example, got, self.verbosity-3)

                # We can pass the test regardless of the output
                # however, a Timeout is always a fail
                force_pass = options['PASS']
                if not timedout and \
                        (force_pass or self.checker.check_output(example, got, options)):
                    self.concerns.success(example, got, self.checker)
                else:
                    self.concerns.failure(example, got, self.checker)
                    failed = True

                    # start an interactive session if the example failes
                    # and the user wanted this
                    if options['INTERACT'] and not timedout:
                        self.concerns.start_interact(example, options)
                        ex = None
                        try:
                            example.interpreter.interact(example, options)
                        except Exception as e:
                            ex = e

                        self.concerns.finish_interact(ex)

                    # fail fast if the user want this or
                    # if we got a Timeout
                    if fail_fast or timedout:
                        break
            finally:
                options.down()

        self.concerns.end_run(failed, user_aborted, crashed)
        self.shutdown_interpreters(interpreters)

        return failed, (user_aborted or crashed)

