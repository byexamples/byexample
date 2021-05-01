from __future__ import unicode_literals

import signal, contextlib
from .log import clog, CHAT
from .init import init_worker

from .concurrency import load_concurrency_engine


class Status:
    ok = 0
    failed = 1
    aborted = 2
    error = 3


def worker(func, input, output, cfg, job_num):
    ''' Generic worker: call <func> for each item pulled from
        the <input> queue until a None gets pulled.

        For each result obtained from calling <func>, push the
        result into <output> queue.

        After receiving a None, close the <output> queue.
        '''
    harvester, executor = init_worker(cfg, job_num)
    for item in iter(input.get, None):
        output.put(func(item, harvester, executor, cfg['dry']))

    harvester.close()
    executor.close()


class Jobs(object):
    def __init__(self, njobs, concurrency_model):
        if concurrency_model not in ('multithreading', 'multiprocessing'):
            raise ValueError(
                "Unexpected concurrency model '%s'. Expected multithreading or multiprocessing."
                % concurrency_model
            )

        if concurrency_model == 'multiprocessing':
            raise NotImplementedError("Not supported yet")

        if njobs == 1:
            concurrency_model = 'singlethreading'

        self.njobs = njobs

        self.Process, self.Manager, self.Queue = load_concurrency_engine(
            concurrency_model
        )

    @contextlib.contextmanager
    def start_sharer(self):
        with self.Manager() as sharer:
            yield sharer

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

        self.input = self.Queue()
        self.output = self.Queue()

        self.processes = [
            self.Process(
                target=worker,
                name=str(n),
                args=(func, self.input, self.output, cfg, n)
            ) for n in range(njobs)
        ]
        for p in self.processes:
            p.start()

        # feed the workers with enough data so all of them can start to work
        for item in items[:njobs]:
            self.input.put(item)

        if clog().isEnabledFor(CHAT):
            for p in self.processes:
                clog().chat("Worker %s.", p.name)

        return items[njobs:]

    def ignore_sigint(self):
        return signal.signal(signal.SIGINT, signal.SIG_IGN)

    def restore_sigint(self, handler):
        return signal.signal(signal.SIGINT, handler)

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
        keyboard_interrupt_received = False
        while nitems:
            with allow_sigint(self.interrupt_handler):
                try:
                    failed, aborted, user_aborted, error = self.output.get()
                except KeyboardInterrupt:
                    keyboard_interrupt_received = True

            if keyboard_interrupt_received:
                clog().note(
                    "User aborted. Waiting to finish the current active executions..."
                )
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

        keyboard_interrupt_received = False
        with allow_sigint(self.interrupt_handler):
            try:
                self.join_jobs()
            except KeyboardInterrupt:
                keyboard_interrupt_received = True

        if keyboard_interrupt_received:
            clog().warn(
                "Not waiting for the current active executions to finish...\n" +\
                "Pressing more times Ctrl-C will force an immediate shutdown\n" +\
                "but it will leave resources uncleaned (dangerous/unsafe)."
            )

        return exit_status

    def run(self, func, items, fail_fast, cfg):
        ''' Process all the <items> in background, aborting earlier
            if one fails and <fail_fast> is True (see loop()).
            '''
        self.interrupt_handler = self.ignore_sigint()
        try:
            rest = self.spawn_jobs(func, items, cfg)
            return self.loop(len(items), rest, fail_fast)
        finally:
            self.restore_sigint(self.interrupt_handler)


@contextlib.contextmanager
def allow_sigint(handler):
    try:
        signal.signal(signal.SIGINT, handler)
        yield
    finally:
        signal.signal(signal.SIGINT, signal.SIG_IGN)
