# Define New Zones Where to Find Examples

There are three different ways in which ``byexample`` can be extended:

 - define zones where to find examples
 - support new languages: how to find them and how to run them
 - perform arbitrary actions during the execution

``byexample`` uses the concept of modules: a python file with some extension
classes defined there. Modules can be loaded using ``--modules <dir>``
from the command line.

What extension classes will depend of what you want to extend or customize.

In this ``how-to`` we will see how to define new zones where to
find examples.

Check [how to support new finders and languages](/{{ site.uprefix }}/contrib/how-to-support-new-finders-and-languages)
and [how to hook to events with concerns](/{{ site.uprefix }}/contrib/how-to-hook-to-events-with-concerns)
for a ``how-to`` about the first two items.

## How to define new zones

``byexample`` searches for examples in particular *zones* of a file.
What zones will depend of the kind of file.

For Python files it searches them in the docstrings, in Ruby files it
searches them in the comments.

By default, if no particular zone is defined ``byexample`` searches the
example in the whole file.

But searching in the whole file without any structure could lead to false
positives.

You can define new zones for a type of files just creating a ``ZoneDelimiter``
subclass.

Imagine that you want to find examples in a HTML file and you want to ignore
everything except the code between ``<pre>`` and ``</pre>`` tags.

This is what you need to write:

```python
>>> from byexample import regex as re
>>> from byexample.finder import ZoneDelimiter

>>> class HTMLPreBlockDelimiter(ZoneDelimiter):
...     target = '.html'
...
...     def zone_regex(self):
...         return re.compile(r'<pre>(?P<zone>.*?)</pre>', re.DOTALL | re.UNICODE)
...
...     def get_zone(self, match, where):
...         return ZoneDelimiter.get_zone(self, match, where)
```

That's it.

The ``target`` indicates the file extension of the files
that will be delimited by this code. It can be a string with a single extension
file or a list or set of several extensions.

The ``zone_regex`` method should return a regular expression to find and capture
the zones.

And optionally, the ``get_zone`` can be overridden to post-process the captured
string: use it to remove any spurious string that may had been captured.

> *Changed* in `byexample 10.0.0`. Before `10.0.0` you could return a
> Python regular expression but from `10.0.0` and on, you need to return
> the regular expressions created by `byexample.regex`. The module is
> almost identical to Python's `re` so the required changes are minimal.


## Concurrency model

Each `ZoneDelimiter` instance will be created *once* during the setup of
`byexample` and then it will be created *once per job thread*.

By default there is only one job thread but more threads can be added
with the `--jobs` option.

The instances are independent and therefore thread-safe.

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

## `ZoneDelimiter` initialization

If you extend `ZoneDelimiter` and decide to implement your own `__init__`,
you must ensure that you call `ZoneDelimiter`'s `__init__` method
passing to it all the keyword-only arguments that you received.

Once done that, you can use the `self.cfg` property to access any
configuration set in `byexample` including the flags/options set
(`self.cfg.options`).

In the `__init__` you can also change the value of `target` to something
different. This allows you to change what type of files you are going to
processes based on the configuration or you can disable the zone finder
entirely setting `self.target = None`.

See
[Extension initialization](/{{ site.uprefix }}/contrib/extension-initialization)
for more about this and some troubleshooting.

> *New* in ``byexample 11.0.0``: `self.cfg` was introduced.
