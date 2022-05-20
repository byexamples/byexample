# Module Loading and Extension Initialization

There are three different ways in which ``byexample`` can be extended:

 - [define zones](/{{ site.uprefix }}/contrib/how-to-define-new-zones-where-to-find-examples) where to find examples
 - support new languages: [how to find them and how to run them](/{{ site.uprefix }}/contrib/how-to-support-new-finders-and-languages)
 - perform [arbitrary actions](/{{ site.uprefix }}/contrib/how-to-hook-to-events-with-concerns) during the execution

You can see a more-in-depth documentation in each section above but all the
extensions are classes that inherit one for the main extension classes:
`ZoneDelimiter`, `ExampleFinder`, `ExampleParser`, `ExampleRunner` and `Concern`

```python
>>> from byexample.finder import ZoneDelimiter, ExampleFinder
>>> from byexample.parser import ExampleParser
>>> from byexample.runner import ExampleRunner
>>> from byexample.concern import Concern
```

One or more of these extension classes (your classes) must be written
in one or more Python module, as any other Python code.

`byexample` will load all the modules located in the folder defined in
the command line.


## Error on module load

`byexample` will catch any error during the loading of a module,
typically a `SyntaxError` or an `ImporError`, and it will print a nice
message:

```shell
$ byexample -m test/ds/bad/syntax/ -l python --dry docs/languages/python.md   # byexample: +norm-ws
[!] From '<...>test/ds/bad/syntax' loading module 'm' failed. Skipping.
invalid syntax (m.py, line 2)
<...>
Rerun with -vvv to get a full stack trace.
```

Running with `-vvv`, you will get the full stack too:

```shell
$ byexample -m test/ds/bad/syntax/ -l python --dry -vvv docs/languages/python.md   # byexample: +norm-ws
[!] From '<...>test/ds/bad/syntax' loading module 'm' failed. Skipping.
Traceback (most recent call last):
<...>
  File "<...>test/ds/bad/syntax/m.py", line 2
<...>
SyntaxError: <...>
<...>
```

When a module fails to load, `byexample` will skip it and continue with
the loading of the rest of the modules (other files).

## Extension initialization

Once a module is loaded, `byexample` will search for any class that
inherits from one of the extension classes (or a subclass of them).

For each class found, it is initialized calling its `__init__` method
passing several keyword-only arguments.

Among them your class will receive `ns`, `sharer` and `cfg`.

The namespace `ns` and the `sharer` are used for managing concurrency in the
case of your extension requires coordination between the workers
and it is documented in the
[concurrency model](/{{ site.uprefix }}/contrib/concurrency-model).

The `cfg` is a `Config` object that holds all the configuration of
`byexample`.

All the keyword-only arguments that your `__init__` will receive will be
also an attribute of `cfg` (with the exception of `ns` and `sharer`).

The following two `__init__` are equivalent:

```python
>>> class MyParserOldStyle(ExampleParser):
...     def __init__(self, verbosity, encoding, **kargs):
...         ExampleParser.__init__(self, verbosity=verbosity, encoding=encoding, **kargs)
...
...         # Use these two config directly, "captured" by __init__
...         # as keyword-only arguments
...         print(verbosity)
...         print(encoding)

>>> class MyParserNewStyle(ExampleParser):
...     def __init__(self, cfg, **kargs):
...         ExampleParser.__init__(self, cfg=cfg, **kargs)
...
...         # Use these two config from the "captured" cfg
...         print(cfg.verbosity)
...         print(cfg.encoding)
```

Moreover, once the extension parent class is initialized, the extension
acquires a cfg property that can be used to read the configuration so
the following `__init__` is also equivalent (and simpler).


```python
>>> class MyParserNewStyle(ExampleParser):
...     def __init__(self, **kargs):
...         ExampleParser.__init__(self, **kargs)
...
...         # Use these two config from the self.cfg property
...         print(self.cfg.verbosity)
...         print(self.cfg.encoding)
...
...     def other_method(self):
...         # self.cfg property is available during the whole lifetime
...         # of the extension
...         print(self.cfg.verbosity)
```

> *New* in ``byexample 11.0.0``: before `11.0.0`, the only way to read
> the configuration was "capturing" them in the `__init__` and optionally
> stored manually like `self.encoding = encoding` (see `MyParserOldStyle`)
> From `11.0.0`, the `cfg` is available and you can use it directly
> (see `MyParserNewStyle`)

> Note: Python's `super` is not supported. Your subclasses should call
> the parent class' method explicitly like `ExampleParser.__init__(self,
> **kargs)` instead of `super().__init__(**kargs)`

## Errors on initialization

`byexample` will capture any exception during the initialization and it
will display an error.

Here, this extension access non-set attribute and `byexample` will tell
you:

```python
>>> class BadInit(Concern):
...    def __init__(self, **kargs):
...        Concern.__init__(self, **kargs)
...
...        # XXX This will fail and we expect the exception to be caught
...        # by byexample initialization process
...        print(self.noattr)
```

```shell
$ byexample -m test/ds/bad/init/ -l python --dry docs/languages/python.md   # byexample: +norm-ws
[!] Something went wrong initializing byexample:
From '<...>test/ds/bad/init' module 'init_failed'
Instantiation of BadInit failed: 'BadInit' object has no attribute 'noattr'
<...>
```

## Missing to initialize parent class

You are required to call parent class' `__init__` passing
all the keyword arguments received by your subclass.

`byexample` will check that and it will complain if you didn't
initialized the parent class.


```python
>>> class BadConcernOldStyle(Concern):
...     def __init__(self, verbosity, encoding, **kargs):
...         # XXX Not calling Concern.__init__ is an error
...         # This code will not fail but byexample will detect
...         # and emit the error
...         print(verbosity)
...         print(encoding)
```

```shell
$ byexample -m test/ds/bad/init_not_called/chk/ -l python --dry docs/languages/python.md   # byexample: +norm-ws
[!] Something went wrong initializing byexample:
From '<...>test/ds/bad/init_not_called/chk' module 'badconcernoldstyle'
The object of class BadConcernOldStyle did not call the constructor of Concern.
<...>
```

In the case of the new style extension (since `byexample 11.0.0`), accessing to
the `cfg` property will fail even before `byexample` has a chance to do
the check.

```python
>>> class BadConcernNewStyle(Concern):
...     def __init__(self, **kargs):
...         # XXX Not calling Concern.__init__ is an error
...         # Because cfg is not properly initialized, you will get
...         # an error here
...         print(self.cfg.verbosity)
...         print(self.cfg.encoding)
```

```shell
$ byexample -m test/ds/bad/init_not_called/cfg/ -l python --dry docs/languages/python.md   # byexample: +norm-ws
[!] Something went wrong initializing byexample:
From '<...>test/ds/bad/init_not_called/cfg' module 'badconcernnewstyle'
Instantiation of BadConcernNewStyle failed: The cfg property is not set.
Did you forget to call __init__ on an extension parent class?
<...>
```

### `PexpectMixin` initialization on `ExampleRunner`

If you are implemented an `ExampleRunner` subclass (perhaps, while you are [supporting a new language](/{{ site.uprefix }}/contrib/how-to-support-new-finders-and-languages)),
chances are that you are using the `PexpectMixin`.

This *mixin* heavily simplify the code needed to interact with an
interpreter/runner and it is designed to work together with
`ExampleRunner`.

Therefore, the `PexpectMixin` cannot be used by classes that don't
inherit from `ExampleRunner` (directly or indirectly):

```python
>>> from byexample.runner import PexpectMixin
>>> from byexample.concern import Concern

>>> class BadNonRunner(Concern, PexpectMixin):
...     def __init__(self, **kargs):
...         Concern.__init__(self, **kargs)
...
...         # XXX We cannot inherit from PexpectMixin if we don't
...         # inherit from ExampleRunner too
...         PexpectMixin.__init__(
...             self, PS1_re=r'\(gdb\)[ ]', any_PS_re=r'\(gdb\)[ ]'
...         )
```

```shell
$ byexample -m test/ds/bad/pexpect_not_runner/ -l python --dry docs/languages/python.md   # byexample: +norm-ws
[!] Something went wrong initializing byexample:
From '<...>test/ds/bad/pexpect_not_runner' module 'non_runner'
Instantiation of BadNonRunner failed: The class
BadNonRunner that inherits from PexpectMixin must also inherit from ExampleRunner.
<...>
```

`PexpectMixin` must be initialized after `ExampleRunner` otherwise you
will receive an error:


```python
>>> from byexample.runner import ExampleRunner, PexpectMixin

>>> class BadRunner(ExampleRunner, PexpectMixin):
...     def __init__(self, **kargs):
...         # XXX Calling PexpectMixin before ExampleRunner.__init__ is an error
...         PexpectMixin.__init__(
...             self, PS1_re=r'\(gdb\)[ ]', any_PS_re=r'\(gdb\)[ ]'
...         )
...
...         ExampleRunner.__init__(self, **kargs)
```

```shell
$ byexample -m test/ds/bad/pexpect_init/ -l python --dry docs/languages/python.md   # byexample: +norm-ws
[!] Something went wrong initializing byexample:
From '<...>test/ds/bad/pexpect_init' module 'badrunner'
Instantiation of BadRunner failed: You need to call
ExampleRunner.__init__ (or its subclass) before calling PexpectMixin.__init__ in BadRunner.
<...>
```

## Extension's `target` (or `language`)

Each `ZoneDelimiter`, `ExampleFinder` and `Concern` defines
a `target` and in the case of `ExampleParser` and `ExampleRunner` a `language`.

The exact meaning of each depends on the extension class. See their
documentation.

Before `11.0.0` this attribute (`target` or `language`) was required to
be defined even before the initialization of the extension. If an
extension class didn't have it, it was just skipped by `byexample`

Since `11.0.0` such attribute could not exist before the initialization
but it *must* exist after and `byexample` will complain if it isn't.

```python
>>> class BadTarget(Concern):
...    def __init__(self, **kargs):
...        Concern.__init__(self, **kargs)
...
...        # XXX 'target' attribute is missing,
...        # byexample will complain about this
...        assert not hasattr(self, 'target')
```

```shell
$ byexample -m test/ds/bad/target/missing/ -l python --dry docs/languages/python.md   # byexample: +norm-ws
[!] Something went wrong initializing byexample:
From '<...>test/ds/bad/target/missing' module 'bad'
The object of class BadTarget did not define a 'target' attribute.
<...>
```

`byexample` also will check the type of `target` / `languages`.
Depending on the extension class that you are extending, the type must be
a string (single-valued) or a list-like strings (multi-valued).

For a `Concern` for example it must be a string: `byexample` will complain
if it is set to other thing:

```python
>>> class BadTarget(Concern):
...    # XXX This is wrong, a target cannot be a list.
...    target = ['bogusmodule']
...
...    def __init__(self, **kargs):
...        Concern.__init__(self, **kargs)
```

```shell
$ byexample -m test/ds/bad/target/invalid/ -l python --dry docs/languages/python.md   # byexample: +norm-ws
[!] Something went wrong initializing byexample:
From '<...>test/ds/bad/target/invalid' module 'bad'
The attribute 'target' of BadTarget must be a single string-like value but it is of type <class 'list'>.
<...>
```

> *New* in ``byexample 11.0.0``: before `11.0.0`, a class was ignored by
> `byexample` if it didn't have a `target` / `language` attribute even if
> the class inherited from an extension class like `ExampleParser` or
> `Concern`.
> Since `11.0.0`, any class the inherit from an extension class will be
> loaded and its `target` / `language` will be checked *after* the
> initialization and if an error is found, `byexample` will make it
> explicit.

For `ZoneDelimiter`, its `target` can be multivalued, like a `list` or
`set`. Empty targets or with duplicated are not considered errors but a
warning is issued.

```python
>>> class MultiTargetDuplicated(ZoneDelimiter):
...    # This is not an error but clearly a typo.
...    target = ['foo', 'foo']

>>> class MultiTargetEmpty(ZoneDelimiter):
...    # This is not an error but setting to None is better
...    # to make explicit the intention
...    target = []
```

```shell
$ byexample -m test/ds/bad/target/multi/ -l python --dry docs/languages/python.md   # byexample: +norm-ws
[w] Extension MultiTargetDuplicated has duplicated entries in its
'target' attribute.
[w] Extension MultiTargetEmpty has no entries in its 'target' attribute.
If is intentional, prefer to set None instead.
```

## Disabling an extension dynamically

An extension can disable itself by setting its `target` / `language` to
`None` during its initialization (`__init__` call).

This is handy because `__init__` will receive the configuration (`cfg`
parameter) and the extension will have the opportunity to check flags
and options (`cfg.options`) and decide if it should run or not.
