from multiprocessing import Queue, Process
import signal, contextlib

class Status:
    ok = 0
    failed = 1
    aborted = 2
    error = 3

def worker(func, sigint_handler, input, output):
    ''' Generic worker: call <func> for each item pulled from
        the <input> queue until a None gets pulled.

        For each result obtained from calling <func>, push the
        result into <output> queue.

        After receiving a None, close the <output> queue.
        '''
    for item in iter(input.get, None):
        output.put(func(item, sigint_handler))
    output.close()
    output.join_thread()

class Jobs(object):
    def __init__(self, njobs, verbosity):
        self.njobs = njobs
        self.verbosity = verbosity

    def spawn_jobs(self, func, items):
        ''' Spawn <njobs> jobs to process <items> in parallel/concurrently.

            The processes are started and feeded with the first <njobs> items
            in <items>, the rest of them need to be pushed manually
            calling send_next_item_from; the result of each file processed can
            be fetched from the <output>.

            Return the <rest> of the <items> not sent,
            and the <output> queue.
            '''
        njobs = self.njobs
        assert njobs <= len(items)

        self.sigint_handler = self.ignore_sigint()

        self.input = Queue()
        self.output = Queue()

        self.processes = [Process(target=worker, name=str(n),
                                             args=(func, self.sigint_handler, self.input, self.output))
                                             for n in range(njobs)]
        for p in self.processes:
            p.start()

        # feed the workers with enough data so all of them can start to work
        for item in items[:njobs]:
            self.input.put(item)

        if self.verbosity >= 1:
            for p in self.processes:
                print("Worker %s (PID %i)." % (p.name, p.pid))

        return items[njobs:]

    def ignore_sigint(self):
        return signal.signal(signal.SIGINT, signal.SIG_IGN)

    def send_next_item_from(self, rest):
        self.input.put(rest[0])
        del rest[0]

    def stop_workers(self):
        for _ in range(self.njobs):
            self.input.put(None)
        self.input.close()

    def join_jobs(self):
        ''' Call me after sending the sentinels (stop_workers)
            and fetching all the results (loop) to avoid a deadlock.'''
        self.input.join_thread()
        for p in self.processes:
            p.join()

    def loop(self, nitems, rest, fail_fast):
        ''' Loop <nitems> times fetching from <output> the
            result of each processed file done in background.

            For each fetch, send (feed) to the workers the next
            item in <rest>.

            The loop will close the workers at the end; it will
            return the exit status (see Status).

            Cancel the loop earlier if a run fails and <fail_fast>
            is True (keep in mind that because several jobs are running
            in background, it is possible that some extra files gets
            processed before closing the loop).
            '''
        exit_status = Status.ok
        end_sentinels_sent = False
        while nitems:
            failed, aborted, user_aborted, error = self.output.get()
            nitems -= 1

            if failed:
                exit_status = max(exit_status, Status.failed)

            if aborted or user_aborted:
                exit_status = max(exit_status, Status.aborted)

            if error:
                exit_status = max(exit_status, Status.error)

            if ((failed or aborted) and fail_fast) or user_aborted or error:
                nitems -= len(rest)
                rest = []

            if rest:
                self.send_next_item_from(rest)

            if not rest and not end_sentinels_sent:
                end_sentinels_sent = True
                self.stop_workers()

        self.join_jobs()
        return exit_status

    def run(self, func, items, fail_fast):
        ''' Process all the <items> in background, aborting earlier
            if one fails and <fail_fast> is True (see loop()).
            '''
        rest = self.spawn_jobs(func, items)
        return self.loop(len(items), rest, fail_fast)

@contextlib.contextmanager
def allow_sigint(handler):
    try:
        signal.signal(signal.SIGINT, handler)
        yield
    finally:
        signal.signal(signal.SIGINT, signal.SIG_IGN)
