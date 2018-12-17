from __future__ import unicode_literals
from .cache import RegexCache
from .jobs import Jobs, Status, allow_sigint
import os, sys

def execute_examples(filename, sigint_handler):
    global cache, harvester, executor, options, human_args, dry
    from .common import human_exceptions

    with human_exceptions("File '%s':" % filename, *human_args) as exc, \
            cache.synced(label=filename), \
            allow_sigint(sigint_handler):
        examples = harvester.get_examples_from_file(filename)
        if dry:
            return executor.dry_execute(examples, filename)
        else:
            return executor.execute(examples, filename)

    user_aborted = isinstance(exc.get('exc'), KeyboardInterrupt)
    error = not user_aborted
    return True, True, user_aborted, error

def main(args=None):
    global cache, harvester, executor, options, human_args, dry

    cache_disabled = os.getenv('BYEXAMPLE_CACHE_DISABLED', "1") != "0"
    cache_verbose  = os.getenv('BYEXAMPLE_CACHE_VERBOSE', "0") != "0"
    cache = RegexCache('0', cache_disabled, cache_verbose)

    with cache.activated(auto_sync=True, label="0"):
        from .cmdline import parse_args
        from .common import human_exceptions
        from .init import init

        args = parse_args(args)
        dry = args.dry
        human_args = [args.verbosity, args.quiet]
        with human_exceptions('During the initialization phase:', *human_args) as exc:
            testfiles, harvester, executor, options = init(args)

        if exc:
            sys.exit(Status.error)

        jobs = Jobs(args.jobs, args.verbosity)
        return jobs.run(execute_examples, testfiles, options['fail_fast'])
