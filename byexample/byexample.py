from .cmdline import parse_args
from .common import human_exceptions
from .init import init

class Status:
    ok = 0
    failed = 1
    aborted_or_crashed = 2
    error = 3

def main(args=None):
    args = parse_args(args)
    human_args = (args.verbosity, args.quiet, Status.error)
    with human_exceptions('During the initialization phase:', *human_args):
        testfiles, harvester, executor, options = init(args)

    exit_status = Status.ok
    for filename in testfiles:
        with human_exceptions("File '%s':" % filename, *human_args):
            examples = harvester.get_examples_from_file(filename)
            if args.dry:
                executor.dry_execute(examples, filename)
                continue

            result = executor.execute(examples, filename)
            failed, aborted_or_crashed = result

            if failed:
                exit_status = max(exit_status, Status.failed)

            if aborted_or_crashed:
                exit_status = max(exit_status, Status.aborted_or_crashed)

            if (failed or aborted_or_crashed) and options['fail_fast']:
                break

    return exit_status
