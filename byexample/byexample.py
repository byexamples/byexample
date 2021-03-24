from __future__ import unicode_literals
import os, sys

if sys.version_info < (3, 0):
    print(
        "Are you using Python 2.x? Byexample no longer runs in that version. Please upgrade your Python environment."
    )
    sys.exit(1)

from .jobs import Jobs, Status
from .log import init_log_system, shutdown_log_system


def execute_examples(filename, harvester, executor, dry):
    from .common import human_exceptions

    with human_exceptions("processing the file '%s'" % filename) as exc:
        examples = harvester.get_examples_from_file(filename)
        if dry:
            return executor.dry_execute(examples, filename)
        else:
            return executor.execute(examples, filename)

    user_aborted = isinstance(exc.get('exc'), KeyboardInterrupt)
    error = not user_aborted
    return True, True, user_aborted, error


def main(args=None):
    init_log_system()

    from .cmdline import parse_args
    from .common import human_exceptions
    from .init import init_byexample

    args = parse_args(args)

    jobs = Jobs(args.jobs, 'multithreading')
    with jobs.start_sharer() as sharer:
        with human_exceptions('initializing byexample') as exc:
            testfiles, cfg = init_byexample(args, sharer)

        if exc:
            sys.exit(Status.error)

        ret = jobs.run(
            execute_examples, testfiles, cfg['options']['fail_fast'], cfg
        )

    shutdown_log_system()
    return ret
