# Define New Zones Where to Find Examples

There are three different ways in which ``byexample`` can be extended:

 - define zones where to find examples
 - support new languages: how to find them and how to run them
 - perform arbitrary actions during the execution

``byexample`` uses the concept of modules: a python file with some classes
defined there and it can be loaded using ``--modules <dir>`` from the command
line.

What classes will depend of what you want to extend or customize.

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
>>> import byexample.regex as re
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
that will be delimited by this code. It can be a single extension or a list
or set of several extensions.

The ``zone_regex`` method should return a regular expression to find and capture
the zones.

While you can use the standard
[``re`` module](https://docs.python.org/3/library/re.html) it is
recommended to use ``byexample.regex`` which has some built-in
optimizations.

And optionally, the ``get_zone`` can be overridden to post-process the captured
string: use it to remove any spurious string that may had been captured.


## Concurrency model

Each `ZoneDelimiter` instance will be created once during the setup of
`byexample` and then it will be created once per job thread.

By default there is only one job thread but more threads can be added
with the `--jobs` option.

The instances are independent and therefore thread-safe.

If you want to *share* data among them you will have to use a
thread-safe structure in a shared place (like mutexes plus class
variables which are shared among the instances).

``byexample`` uses this mechanism to synchronize the jobs progress
reports in
[byexample/modules/progress.py](https://github.com/byexamples/byexample/tree/master/byexample/modules/progress.py).
