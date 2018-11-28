# How to Hook to Events with Concerns

There are three different ways in which ``byexample`` can be extended:

 - how to find examples
 - how to support new languages
 - how to perform arbitrary actions during the execution

``byexample`` uses the concept of modules: a python file with some classes
defined there and it can be loaded using ``--modules <dir>`` from the command
line.

What classes will depend of what you want to extend or customize.

In this ``how-to`` we will see how to hook to events and perform arbitrary
actions during the execution.

Check [how to support new finders and languages](docs/contrib/how-to-support-new-finders-and-languages.md)
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


