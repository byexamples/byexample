# How to Hook to Events

There are three different ways in which ``byexample`` can be extended:

 - define zones where to find examples
 - support new languages: how to find them and how to run them
 - perform arbitrary actions during the execution

``byexample`` uses the concept of modules: a python file with some extension
classes defined there. Modules can be loaded using ``--modules <dir>``
from the command line.

What extension classes will depend of what you want to extend or customize.

In this ``how-to`` we will see how to hook to events and perform arbitrary
actions during the execution.

Check [how to define new zones where to find examples](/{{ site.uprefix }}/contrib/how-to-define-new-zones-where-to-find-examples)
and [how to support new finders and languages](/{{ site.uprefix }}/contrib/how-to-support-new-finders-and-languages)
for a ``how-to`` about the first two items.

Let's show this by example.

## How to perform arbitrary actions during the execution: Concern

During the execution of the whole set of examples, ``byexample`` will execute
some callbacks or *hooks* at particular moments like before running an example or
after it failed.

The set of hooks are collected into the ``Concern`` interface (also known as
Cross-Cutting ``Concern``).

You can create and add your own to extend the capabilities of ``byexample``:

 - show the progress of the execution
 - log / report generation for export
 - log execution time history for future execution time prediction (estimate)
 - turn on/off debugging, coverage and profile facilities
 - others...

### Eg: Dump the Script

Let's imagine that we want to save in a file all the examples' code without
the expected strings nor anything else.

```python
>>> from byexample.concern import Concern

>>> class DumpScript(Concern):
...     target = 'dump-script'
...
...     def start_run(self, examples, runners, filepath):
...         self.f = open(filepath + ".script")
...
...     def end_run(self, failed, user_aborted, crashed):
...         self.f.close()
...
...     def start_example(self, example, options):
...         self.f.write(example.source)
```

See the documentation of the class ``Concern`` in
[byexample/concern.py](https://github.com/byexamples/byexample/tree/master/byexample/concern.py) to get a description of all the
possible hooks and when they are called.

``byexample`` uses this mechanism to generate a progress bar in
[byexample/modules/progress.py](https://github.com/byexamples/byexample/tree/master/byexample/modules/progress.py).


## Concurrency model

Each `Concern` instance will be created *once* during the setup of
`byexample` and then it will be created *once per job* thread.

By default there is only one job thread but more threads can be added
with the `--jobs` option.

If you want to *share* data among them you will have to use a
thread-safe structures created by a `sharer` and store them
in a `namespace`.

In the [concurrency model](/{{ site.uprefix }}/contrib/concurrency-model)
documentation it is explained and in
[byexample/modules/progress.py](https://github.com/byexamples/byexample/tree/master/byexample/modules/progress.py)
you can see a concrete example.

> *Changed* in `byexample 10.0.0`. Before `10.0.0` you were forced to
> use `multiprocessing` by hand but in `10.0.0` the concurrency model
> is hidden so you cannot relay on `multiprocessing` because `byexample`
> may not use processes at all!
> `sharer` and `namespace` are objects that hide the details while
> allowing you to have the same power.

## `Concern` initialization

If you extend `Concern` and decide to implement your own `__init__`,
you must ensure that you call `Concern`'s `__init__` method
passing to it all the keyword-only arguments that you received.

Once done that, you can use the `self.cfg` property to access any
configuration set in `byexample` including the flags/options set
(`self.cfg.options`).

In the `__init__` you can also change the value of `target` to something
different. For a `Concern` this is typically used to enable/disable
the concern object based on the configuration by just setting
`self.target = "some string"` (enable) or `self.target = None`
(disable).

See
[Extension initialization](/{{ site.uprefix }}/contrib/extension-initialization)
for more about this and some troubleshooting.

> *New* in ``byexample 11.0.0``: `self.cfg` was introduced.
