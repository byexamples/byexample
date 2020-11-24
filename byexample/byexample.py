from __future__ import unicode_literals
import os, sys

if sys.version_info < (3, 0):
    print(
        "Are you using Python 2.x? Byexample no longer runs in that version. Please upgrade your Python environment."
    )
    sys.exit(1)

from .cache import RegexCache
from .jobs import Jobs, Status
from .log import init_log_system


def execute_examples(filename, harvester, executor):
    global cache, dry
    from .common import human_exceptions

    with human_exceptions("processing the file '%s'" % filename) as exc, \
            cache.synced(label=filename):
        examples = harvester.get_examples_from_file(filename)
        if dry:
            return executor.dry_execute(examples, filename)
        else:
            return executor.execute(examples, filename)

    user_aborted = isinstance(exc.get('exc'), KeyboardInterrupt)
    error = not user_aborted
    return True, True, user_aborted, error


def main(args=None):
    global cache, dry

    init_log_system()

    cache_disabled = os.getenv('BYEXAMPLE_CACHE_DISABLED', "1") != "0"
    cache_verbose = os.getenv('BYEXAMPLE_CACHE_VERBOSE', "0") != "0"
    if sys.version_info > (3, 7):
        # The feature is not supported for Python 3.8
        cache_disabled = True
    cache = RegexCache('0', cache_disabled, cache_verbose)

    with cache.activated(auto_sync=True, label="0"):
        from .cmdline import parse_args
        from .common import human_exceptions
        from .init import init_byexample

        args = parse_args(args)

        dry = args.dry
        with human_exceptions('initializing byexample') as exc:
            testfiles, cfg = init_byexample(args)

        if exc:
            sys.exit(Status.error)

        jobs = Jobs(args.jobs)
        return jobs.run(
            execute_examples, testfiles, cfg['options']['fail_fast'], cfg
        )
