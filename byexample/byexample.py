from .cache import RegexCache, cache_filepath
from .jobs import Jobs, Status
import os

def execute_examples(filename):
    global cache_disabled, harvester, executor, options, human_args, dry
    from .common import human_exceptions

    human_args[-1] = None # exitcode == None
    with RegexCache(cache_filepath(filename, 're'), cache_disabled), \
            human_exceptions("File '%s':" % filename, *human_args):
        examples = harvester.get_examples_from_file(filename)
        if dry:
            return executor.dry_execute(examples, filename)
        else:
            return executor.execute(examples, filename)

    return True, True

def main(args=None):
    global cache_disabled, harvester, executor, options, human_args, dry

    cache_disabled = os.getenv('BYEXAMPLE_CACHE_DISABLED', "1") != "0"
    with RegexCache(cache_filepath('0', 're'), cache_disabled):
        from .cmdline import parse_args
        from .common import human_exceptions
        from .init import init

        args = parse_args(args)
        dry = args.dry
        human_args = [args.verbosity, args.quiet, Status.error]
        with human_exceptions('During the initialization phase:', *human_args):
            testfiles, harvester, executor, options = init(args)

    jobs = Jobs(args.jobs)
    return jobs.run(execute_examples, testfiles, options['fail_fast'])
