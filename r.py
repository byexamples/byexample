import sys, os, contextlib
from byexample.byexample import main

try:
    import coverage

    @contextlib.contextmanager
    def coverage_measure():
        cov = coverage.Coverage(source=['byexample'], auto_data=True)
        cov.start()
        try:
            yield
        finally:
            cov.stop()

except ImportError:
    @contextlib.contextmanager
    def coverage_measure():
        yield

if __name__ == '__main__':
    if os.environ.get('BYEXAMPLE_COVERAGE_TEST'):
        with coverage_measure():
            sys.exit(main())

    else:
        sys.exit(main())

