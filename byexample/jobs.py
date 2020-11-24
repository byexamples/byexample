from __future__ import unicode_literals
from threading import Thread
from queue import Queue

import signal, contextlib
from .log import clog, CHAT
from .init import init_worker


class Status:
    ok = 0
    failed = 1
    aborted = 2
    error = 3


def worker(func, input, output, cfg):
    ''' Generic worker: call <func> for each item pulled from
        the <input> queue until a None gets pulled.

        For each result obtained from calling <func>, push the
        result into <output> queue.

        After receiving a None, close the <output> queue.
        '''
    harvester, executor = init_worker(cfg)
    for item in iter(input.get, None):
        output.put(func(item, harvester, executor, cfg['dry']))


class Jobs(object):
    def __init__(self, njobs):
        self.njobs = njobs

    def spawn_jobs(self, func, items, cfg):
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

        self.input = Queue()
        self.output = Queue()

        self.processes = [
            Thread(
                target=worker,
                name=str(n),
                args=(func, self.input, self.output, cfg)
            ) for n in range(njobs)
        ]
        for p in self.processes:
            p.start()

        # feed the workers with enough data so all of them can start to work
        for item in items[:njobs]:
            self.input.put(item)

        if clog().isEnabledFor(CHAT):
            for p in self.processes:
                clog().chat("Worker %s (PID %i).", p.name, p.pid)

        return items[njobs:]

    def ignore_sigint(self):
        return signal.signal(signal.SIGINT, signal.SIG_IGN)

    def send_next_item_from(self, rest):
        self.input.put(rest[0])
        del rest[0]

    def stop_workers(self):
        for _ in range(self.njobs):
            self.input.put(None)

    def join_jobs(self):
        ''' Call me after sending the sentinels (stop_workers)
            and fetching all the results (loop) to avoid a deadlock.'''
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
            with allow_sigint(self.interrupt_handler):
                try:
                    failed, aborted, user_aborted, error = self.output.get()
                except KeyboardInterrupt:
                    clog().note("User aborted. Closing...")
                    failed = aborted = error = False
                    user_aborted = True

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

        with allow_sigint(self.interrupt_handler):
            self.join_jobs()
        return exit_status

    def run(self, func, items, fail_fast, cfg):
        ''' Process all the <items> in background, aborting earlier
            if one fails and <fail_fast> is True (see loop()).
            '''
        self.interrupt_handler = self.ignore_sigint()
        rest = self.spawn_jobs(func, items, cfg)
        return self.loop(len(items), rest, fail_fast)


@contextlib.contextmanager
def allow_sigint(handler):
    try:
        signal.signal(signal.SIGINT, handler)
        yield
    finally:
        signal.signal(signal.SIGINT, signal.SIG_IGN)
