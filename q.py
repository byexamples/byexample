import sys, os, contextlib
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
            from byexample.huff import main
            sys.exit(main())

    else:
        from byexample.huff import main
        sys.exit(main())

