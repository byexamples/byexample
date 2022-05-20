# Concurrency Model

`byexample` can execute the examples of multiple files in parallel (or
concurrently to be more precise).

By default only one file is processed each time but more can be added
with the `--jobs` command line option.

But exactly how this is done was never officially documented.

This documents describes how `byexample` implements `--jobs` and how
that could affect the implementation of the modules/extensions/plugins.

## Some history

Historically, before `byexample 10.0.0`, each file was processed by a
*job* or *worker* that was running in an *independent process*.

So `--jobs 2` involved 3 running programs: the main program and 2
workers.

These workers were exact copies of the main program, `byexample`, and
they were created using
[multiprocessing](https://docs.python.org/3/library/multiprocessing.html).

The copies were done using a `fork` method. This was a very simple
method supported by Linux and MacOS.

But `fork` didn't work well in every case (specially under MacOS)
and in `byexample 10.0.0`
we decided to change the concurrency model from `multiprocessing` to
`multithreading`.

## Multithreading model

Instead of forking/copying the main program, `multithreading` makes the
main program to run several threads without copying (or with a minimal
copy).

This makes `byexample` to startup faster and use significant less
memory.

On the other hand, due how Python works, you may loose a little of
parallelism.

The good news is that this method is well supported in Linux, MacOS and
even in Windows.

## The N+1 creation rule

Exactly how `byexample` handles the concurrency is hidden from the
developer of modules.

If you are developing an `ExampleParser`, `ExampleRunner`, `ExampleFinder`,
`ZoneDelimiter` or a `Concern`, you should not have to worry about this.

The only thing that you need to know is that the extension class you are
developing (let's say an `ExampleRunner`) will be instantiated
*once* in the main program and then *once* in each worker.

So for `--jobs 2`, your class will be instantiated 3 times.

This is the *N+1 creation rule*.

It is guaranteed that the class will be fully created in the main thread
before the creation in the workers; the creation order in the workers is
undefined and it could even happen in parallel.

In general you should not have a problem with the rule unless you want
to *share data among the workers or synchronize them*.

## Sharing data and synchronization

If you are developing, let say a `Concern`, you may want to create a
*shared* data structure that can be accessible among the other instances
of your class in the workers.

Having a shared writable data structure would lead to corruptions so you
probably want to use a *synchronization mechanism* as well.

But the concurrency model is hidden so you cannot use
[multiprocessing](https://docs.python.org/3/library/multiprocessing.html)
or [threading](https://docs.python.org/3/library/threading.html).

Instead `byexample` will give you two objects: a `sharer` and a
`namespace`.

On the *main thread*, your class will be instantiated with a `sharer`
and a `namespace` objects.

The `sharer` has some methods to create shared data structures and
synchronization mechanism that are compatible with the concurrency model
of `byexample`.

Things like `sharer.list()` and `sharer.dict()` are for shared lists and
dictionaries while `sharer.RLock()` and `sharer.Barrier()` are for
synchronization.

These things need to be *passed* to the workers and for that
`byexample` will give you also a `namespace` object.

On the *main thread*, you can store things in the `namespace`; on the
*worker thread* you can only read them (you cannot store).

All of this sounds more complex than it is!

### Example

Imagine that you want a `Concern` to measure the time that each example
takes *and* keep track of the longest time that one example took.

Something like this:

```python
>>> from byexample.concern import Concern

>>> class MeasureTime(Concern):
...     target = 'measure-time'
...
...     def __init__(self, **kargs):
...         Concern.__init__(self, **kargs)
...         self.begin = self.longest = 0
...
...     def start_example(self, *args):
...         self.begin = time.time()
...
...     def end_example(self, *args):
...         elapsed = time.time() - self.begin
...         self.longest = max(self.longest, elapsed)
```

Because `MeasureTime` is instantiated *once per worker*, `self.longest`
will have the elapsed time of the slowest example *of that particular worker*.

But if you want to have a *global* view and see the slowest example of
*all the workers* ?

You need to *share* information among the workers so we need to modify
the `MeasureTime` a little.

First we need a *shared dictionary* to store the slowest example per worker,
a *lock* to synchronize the access and `job_number` will represent each worker.

This is the modified `__init__` of `MeasureTime`:

```python
>>> def __init__(self, sharer, ns, job_number, **kargs):
...     Concern.__init__(self, sharer=sharer, ns=ns, job_number=job_number, **kargs)
...     self.begin = 0
...
...     if sharer is not None:
...         # we are in the main thread, we can use the sharer
...         # and we can **store** things in the namespace
...         ns.elapsed_times_by_worker = sharer.dict()
...         ns.lock = sharer.RLock()
...
...     else:
...         # we are in the worker thread, save the job/worker number
...         self.my_number = job_number
...
...         # keep a private reference to the dictionary and lock
...         # created above
...         # these are *shared* among other instances of MeasureTime
...         # so we must use it with care.
...         #
...         # note that the namespace is **read-only** here
...         self.elapsed_times_by_worker = ns.elapsed_times_by_worker
...         self.lock = ns.lock
```

Now, on the `end_example` we need to store the longest elapsed time
*among* all the workers (among all the instances of `MeasureTime`):

```python
>>> def end_example(self, *args):
...     elapsed = time.time() - self.begin
...     with self.lock:
...         my_longest = self.elapsed_times_by_worker.get(self.my_number, 0)
...         my_longest = max(my_longest, elapsed)
...         self.elapsed_times_by_worker[self.my_number] = my_longest
```

Because `elapsed_times_by_worker` is a *shared dictionary* we need to access it
atomically to avoid race conditions. For this we take the `lock` first.

The standard [byexample/modules/progress.py](https://github.com/byexamples/byexample/tree/master/byexample/modules/progress.py)
is also an example of this: there the `Concern` uses a `RLock` to
synchronize the access to the standard output.

## Multiprocessing model

`byexample 10.0.0` not longer support *"officially"* the
`multiprocessing` model but it is not ruled out entirely.

In a future `multiprocessing` may be re-enabled again.

That's the main reason of using `sharer` and `namespace`: if you use
them in your classes your code will support any concurrency model out of
the box.

## Caveats on using `multiprocessing` **within** an extension/plugin

`byexample` does not impose any restriction on how *your* extension/plugin
may use or not `multithreading` and/or `multiprocessing` **internally**.

How `--jobs` works is **independent** of it.

However, using `multiprocessing` **within** an extension has some
caveats.

When `multiprocessing.Process` (or similar) is used, the main Python
process (`byexample`) spawns a fresh Python process to run whatever you
wanted in parallel.

Take the following `Concern` that runs a class' method in background
while `byexample` is executing an example:

```python
>>> from byexample.concern import Concern
>>> import multiprocessing

>>> class Some(Concern):
...     target = 'some'
...
...     @classmethod
...     def watch_in_bg(cls, num):
...         # this will be executed in background, in parallel
...         pass
...
...     def start_example(self, *args):
...         self.child = multiprocessing.Process(
...                         target=Some.watch_in_bg,
...                         args=(42,)
...                     )
...         self.child.start() # This will fail!!
...
...     def end_example(self, *args):
...         self.child.join()
```

Why would it fail?

This child fresh process will not have the modules that
`byexample` loaded dynamically so it will likely fail even before
executing the class' method `watch_in_bg` because the module where
`Some.watch_in_bg` lives is not loaded.

You may see an error like this:

```python
Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "<...>/multiprocessing/spawn.py", line 116, in spawn_main
    exitcode = _main(fd, parent_sentinel)
  File "<...>/multiprocessing/spawn.py", line 126, in _main
    self = reduction.pickle.load(from_parent)
ModuleNotFoundError: No module named '<...>'
```

> Note: calling `multiprocessing.Process` will not fail if you are in
> Linux, however you should not develop your plugin under that
> assumption. Keep reading!

Since `10.5.1`, `byexample` offers you a mechanism to call
`multiprocessing.Process` safely.

You need to wrap the function with `prepare_subprocess_call`:

```python
>>> from byexample.concern import Concern
>>> import multiprocessing

>>> class Some(Concern):
...     target = 'some'
...
...     @classmethod
...     def watch_in_bg(cls, num):
...         # this will be executed in background, in parallel
...         pass
...
...     def start_example(self, *args):
...         # self.cfg.prepare_subprocess_call takes the 'target' function
...         # and an optional 'args' and 'kwargs' arguments
...         # like multiprocessing.Process does.
...         #
...         # it will return a dictionary that be unpacked
...         # with the double '**' directly into multiprocessing.Process
...         # call
...         self.child = multiprocessing.Process(
...                     **self.cfg.prepare_subprocess_call(
...                             target=Some.watch_in_bg,
...                             args=(42,)
...                         )
...                     )
...         self.child.start() # Start the child process as usual
...
...     def end_example(self, *args):
...         self.child.join()
```

I wrote a
[blog post](https://book-of-gehn.github.io/articles/2022/03/06/Multiprocessing-Spawn-of-Dynamically-Imported-Code.html)
about the issues using `multiprocessing` with dynamically imported code.
If you want to see the dirty details behind `prepare_subprocess_call`,
you can check the [commit b263ba76](
https://github.com/byexamples/byexample/commit/b263ba76271e447a2faed6f0517f71b74d96ab81
).

> *New* in ``byexample 10.5.1``: `prepare_subprocess_call` is a special
> function that is passed to the `__init__` method and can be used to wrap
> code and arguments to be executed in a separated process.

> *New* in ``byexample 11.0.0``: `prepare_subprocess_call` can be
> retrieved from `self.cfg` directly so it is not needed to capture it
> from the `__init__`'s `kargs`

