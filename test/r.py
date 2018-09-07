import sys, os

if __name__ == '__main__':
    home = os.path.join(os.path.dirname(__file__), "../")
    sys.path.append(home)
    del sys.path[0]
    if os.environ.get('BYEXAMPLE_COVERAGE_TEST'):
        try:
            import contextlib
            from coverage import Coverage

            @contextlib.contextmanager
            def coverage_measure():
                cov = Coverage(source=['byexample'], auto_data=True)
                cov.start()
                try:
                    yield
                finally:
                    cov.stop()

            with coverage_measure():
                from byexample.byexample import main
                sys.exit(main())

        except ImportError as e:
            print("ImportError:\n%s" % str(e))
            print("Warning: coverage is not installed -> pip install coverage")
            sys.exit(-1)

    else:
        from byexample.byexample import main
        sys.exit(main())

