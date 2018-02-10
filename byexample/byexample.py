from .cmdline import parse_args
from .init import init

def main(args=None):
    args = parse_args(args)
    testfiles, harvester, executor, options = init(args)

    exit_status = 0
    for filename in testfiles:
        examples = harvester.get_examples_from_file(filename)
        if args.dry:
            continue

        result = executor.execute(examples, filename)
        failed, aborted_or_crashed = result

        if failed:
            exit_status = max(exit_status, 1)

        if aborted_or_crashed:
            exit_status = max(exit_status, 2)

        if (failed or aborted_or_crashed) and options['fail_fast']:
            break

    return exit_status
