from .cache import RegexCache, cache_filepath
import os

class Status:
    ok = 0
    failed = 1
    aborted = 2
    error = 3

def main(args=None):
    cache_disabled = os.getenv('BYEXAMPLE_CACHE_DISABLED', "1") != "0"
    with RegexCache(cache_filepath('0', 're'), cache_disabled):
        from .cmdline import parse_args
        from .common import human_exceptions
        from .init import init

        args = parse_args(args)
        human_args = (args.verbosity, args.quiet, Status.error)
        with human_exceptions('During the initialization phase:', *human_args):
            testfiles, harvester, executor, options = init(args)

    exit_status = Status.ok
    for filename in testfiles:
        with RegexCache(cache_filepath(filename, 're'), cache_disabled), \
                human_exceptions("File '%s':" % filename, *human_args):
            examples = harvester.get_examples_from_file(filename)
            if args.dry:
                executor.dry_execute(examples, filename)
                continue

            result = executor.execute(examples, filename)
            failed, aborted = result

            if failed:
                exit_status = max(exit_status, Status.failed)

            if aborted:
                exit_status = max(exit_status, Status.aborted)

            if (failed or aborted) and options['fail_fast']:
                break

    return exit_status
