def load_concurrency_engine(concurrency_model):
    if concurrency_model in ('singlethreading', 'multithreading'):
        from multiprocessing.dummy import Process
        from multiprocessing.dummy import Manager as _Threading_Manager
        from multiprocessing.dummy import Queue

        # multiprocessing.dummy.Manager is not a context manager so
        # it cannot be used exactly like a multiprocessing.Manager
        # this class closes the gap between those
        class Manager:
            def __enter__(self):
                return _Threading_Manager()

            def __exit__(self, *args):
                pass

        return (Process, Manager, Queue)

    elif concurrency_model == 'multiprocessing':
        from multiprocessing import Process
        from multiprocessing import Manager
        from multiprocessing import Queue
        from multiprocessing import set_start_method

        set_start_method('fork')  # or 'spawn' or 'forkserver'
        return (Process, Manager, Queue)

    else:
        raise ValueError(
            "Unexpected concurrency model '%s'. Expected singlethreading, multithreading or multiprocessing."
            % concurrency_model
        )


class _DummyLock(object):
    def __enter__(self):
        return

    def __exit__(self, *args):
        pass

    def acquire(self, *args, **kargs):
        pass

    def release(self, *args, **kargs):
        pass
