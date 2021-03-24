# Concurrency Model

`byexample` can execute the examples of the given file in parallel (or
concurrently to be more precise).

By default only one files is processed each time but more can be added
with the `--jobs` command line option.

But exactly how this is done was never officially documented.


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

But `fork` didn't work well in every case in MacOS in `byexample 10.0.0`
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

The good news is that this method is will supported in Linux, MacOS and
even in Windows.

## The N+1 creation rule

Exactly how `byexample` handles the concurrency is hidden from the
developer of modules.

If you are developing an `ExampleParser`, `ExampleRunner`, `ExampleFinder`,
`ZoneDelimiter` or a `Concern`, you should not have to worry about this.

The only thing that you need to know is that the class you are
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
...         self.begin = self.longest = 0
...
...     def start_example(self, *args):
...         self.begin = time.time()
...
...     def end_example(self, *args):
...         elapsed = time.time() - self.begin
...         self.longest = max(self.longest, elapsed)
```

Ended, `self.longest` will have the elapsed time of the slowest example
*for each worker*.

But if you want to have a global view and see the slowest example of
*all the workers* ?

You need to *share* information among the workers so we need to modify
the `MeasureTime` a little.

First we need a *shared dictionary* to store per worker, a *lock* to
synchronize the access and `job_number` will represent each worker.

```python
>>> def __init__(self, sharer, ns, job_number, **kargs):
...     self.begin = 0
...
...     if sharer is not None:
...         # we are in the main thread, we can use the sharer
...         # and we can store things in the namespace
...         ns.elapsed_times_by_worker = sharer.dict()
...         ns.lock = sharer.RLock()
...
...     else:
...         # we are in the worker thread, save the job/worker number
...         # and keep a private reference to the dictionary and lock
...         # note that the namespace is read-only here
...         self.my_number = job_number
...         self.elapsed_times_by_worker = ns.elapsed_times_by_worker
...         self.lock = ns.lock
```

Now, on the `end_example` we need to store the longest elapsed time:

```python
>>> def end_example(self, *args):
...     elapsed = time.time() - self.begin
...     with self.lock:
...         my_longest = self.elapsed_times_by_worker.get(self.my_number, 0)
...         my_longest = max(my_longest, elapsed)
...         self.elapsed_times_by_worker[self.my_number] = my_longest
```

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
