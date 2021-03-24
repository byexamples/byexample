# What's new?

This is a short list of the most important features and exciting
things in the last releases.

You can visit the
[changelog](https://github.com/byexamples/byexample/releases)
for a more complete overview.

## 10.0.0

This is another major upgrade which brings some improvements,
a lot of internal refactor, profiling and optimizations.

The good thing is no changes to your examples will be needed as
all the modifications are internal and backward compatible.

The bad thing is the changes will require some adjustments
to your `byexample` *modules* if you have one. This only affects to the
developers of modules then.

Finally, with this release we drop the support for Python 3.5 which it
is already at its *end of life* since a few months.

### `doctest` compatibility improvements

The compatibility layer with Python's `doctest` was increased with the
introduction of `FAIL_FAST` and `REPORT_ONLY_FIRST_FAILURE` flags.

### Profiling

A new profiling system was implemented for the internals of `byexample`
and it is possible to be used in a module. It is *not* a replacement
for standard tools like `cProfile` and `kernprof`; it is just another
way to look.

See `byexample/prof.py` file for the documentation.

### New `byexample.regex`

We use a home-made regex module as replacement for `re`, the regex
implementation of Python.

It is mostly backward-compatible with `re` so the transition should be
trivial.

Most of the cases you need to replace the import:

```python
>>> import re
```

by

```python
>>> import byexample.regex as re
```

and that's all.

The new `byexample.regex` aims to centralize the regex
construction so it does *not* offer global functions like `re.sub(..)`.
Instead you need to call explicitly the `compile` function like
`re.compile(..).sub(..)`

You are **highly** recommended to use `byexample.regex` instead of `re`
which now it is considered deprecated.

Note that `byexample 10.0.0` will continue to work with `re` and it will
not enforce the use of `byexample.regex` however this will change in the
next versions.

You had been warned!


### Runner's `reset`

The `Runner.reset()` is introduced. In `byexample 9.x.x` and before, the
engine called `Runner`'s `initialize` and `shutdown` methods at the
begin and end of each round of examples, coming from the same file.

Now and only if it is enabled, `byexample` calls `reset` instead of
`shutdown` and if the method returns `True` the `initialize` will *not*
be called on the next round.

In an ideal world a runner should support a way to *reset to a clean*
internal state, implemented in the `reset` method so the same runner
can be reused for different files without having to call
`initialize`/`shutdown` a bunch of times.

If the feature is not enabled or `reset` returns `False` (the default),
`byexample` behaves as in `9.x.x`.

It is an opportunistic optimization, not a mandatory one. So if you
cannot do the optimization, no problem.

### Replace multiprocessing with threading

In `byexample 9.x.x` each `Runner`, `Parser`, `Finder` and `Concern` was
instantiated **once** before spawning the workers.

These workers were `multiprocessing`'s workers, copies of the process
created by the `fork` method (see `multiprocessing` documentation).

The `fork` allowed a trivial copy of the process image but it is
supported only in Linux and partially in MacOS.

To avoid the need of `fork`, `byexample 10.0.0` makes explicit the
copies: it creates **once in the main thread** each  `Runner`, `Parser`,
`Finder` and `Concern` but then it creates **once per worker/job
thread** each of those.

So a particular `Runner` like the standard `PythonRunner` will be
created `N+1` times: 1 in the main thread and 1 per worker/job (assuming
`N` jobs)

This **may break** your module implementation if you depend on that
and you **must** make the code *thread safe* (like not using global
or class variables without a synchronization mechanism like a lock or
queue).

If you need to share data among the workers you can use `sharer` and
namespaces.

### Sharer and namespaces

Each module's objects (parsers, runners, concerns and others) will
receive in the constructor a `sharer` object.

Then you can request to it the creation of data structures that will be
shared among the workers. Things like `list`, `dict` and `queue`.

The `sharer` can also create synchronization mechanisms like `RLock`.

The objects that you created need to be saved in a place that it is
shared itself.

For this each constructor will receive a namespace object named `ns`
where you can store your shared objects:

```python
def __init__(self, sharer, ns, **others):
    if sharer is not None:
        # we are in the main thread, ns is writeable
        ns.mylist = sharer.list()
        ns.mylock = sharer.RLock()

    # we may be in the main thread or in a worker thread,
    # so ns may not be writeable (we can read only)
    with ns.mylock:
        ns.mylist.append("cool")

```

`sharer` will be available in the main thread not in the workers
threads and the namespace will be only writeable in the main thread as
well, being read-only later.

### API modification to PexpectMixing

A few bits were changed in `PexpectMixing`. This will affect only the
developers of runners.

## 9.2.2 - 9.2.6

Several bug fixing:
 - improved the search for examples in a `.py` Python file.
 - bundled `byexample-repl.js` next with `byexample` to run Javascript
examples
 - better logs on a timeout and added a `troubleshooting` page section.

Note: this 9.2.5 is meant to override the previous 9.2.3/9.2.4 which
were tagged from master by mistake. These two are not available anymore
and you are recommended to upgrade at least to 9.2.5.

## 9.2.1

Patch version to support MacOS with the newer version of Python.

Windows is also supported but only if the Windows Subsystem for Linux is
used.

## 9.2.0

Minor release that brings support for Python 3.8 and 3.9
and it close the distance to have `byexample` running in MacOS and
Windows.

An important fix was done also. For Python files, now the examples
are searched only in docstrings.

These docstrings follow the definition of docstring of Python: a string
that it is immediately after a function or class definition (see
https://docs.python.org/3/library/ast.html).

Because it was tradition to put some initialization code in a string at
the module level without being a module's docstring, the zone finder
will also find zones and examples there (but only in the module's
strings).

Without this change, the previous finder was too naive and it could
confuse a normal string with a docstring breaking the finder.

## 9.1.0

This minor release brings one of the oldest feature requested:
the ability to *type text* in a running example like a human would do.

This is specially useful in `shell` scripts that are use to ask the
user for things.

```shell
$ profile() {
>    read -p "name: " NAME
>    read -p "email: " EMAIL
>
>    echo "Profile for $EMAIL created. Welcome $NAME!"
> }

$ profile               # byexample: +input
name: [John Doe]
email: [jdoe@example.com]
Profile for jdoe@example.com created. Welcome John Doe!
```

`+input` allows you to type one or more phrases delimited by `[...]`.
Check [its documentation](/{{ site.uprefix }}/basic/input).

See the full
[9.1.0 changelog](https://github.com/byexamples/byexample/releases/tag/9.1.0)

## 9.0.0

Along several fixes and minor enhancements, this major release drops
support for Python 2.x.

Since `2.1.1` `byexample` had dual support for both
main lines of Python 2.x and 3.x but the compatibility had a cost
and prevented us to move forward and use more handy features of Python.

January 1st, 2020 marked the *end of life* of Python 2.x and with it,
we our support for it.

If you are using `byexample` in an environment that still is stuck in
Python 2.x, the `byexample` 8.x series will be still support Python 2.x
but do not expect much activity.

9.0.0 also brings two more languages:
[PHP](/{{ site.uprefix }}/languages/php)
and [Elixir](/{{ site.uprefix }}/languages/elixir).
Both are still a little *experimental* but they should work.

Remember to [open an issue](https://github.com/byexamples/byexample/issues)
if they don't!

An much more: logging improvements, performance and documentation
(thanks @matt17r)

See the full
[9.0.0 changelog](https://github.com/byexamples/byexample/releases/tag/9.0.0)

## 8.1.3

Patch release: the license is bundled with the code and fixed some
compatibilities issue with Windows-like environments

See the full
[8.1.3 changelog](https://github.com/byexamples/byexample/releases/tag/8.1.3)

## 8.1.0

This minor release defines `bash` as the default `shell` and allows
the user to change it using the new `+shell`
[option](/{{ site.uprefix }}/languages/shell).

Before `8.1.0` using `shell` used `sh` which it is commonly a symbolic
link to `bash`, `dash` and who-knows-else. So this release *may*
break some examples but the impact should be minimal.

Also, a lot of improvements in how we show the diff including an option
to use a custom external diff program (`--difftool`)

See the full
[8.1.0 changelog](https://github.com/byexamples/byexample/releases/tag/8.1.0)

## 8.0.0

Several changes were added:
 - a [terminal ANSI emulator](/{{ site.uprefix }}/advanced/terminal-emulation)
(enabled with `+term=ansi`), specially useful
for those examples that are designed with a cli.
 - deterministic output for Ruby examples
 - cancellation of runs (performance improvement)
 - capture greedy/non-greedy (heuristic): named tags are non-greedy as they
are used to capture interesting, typically short strings; unnamed tags are
non-greedy too except at the end of a line where typically capture
longer uninteresting outputs.

And much more!
 - fixes in `+stop-on-silence` / `+stop-on-timeout`
 - Ruby support: 2.0, 2.1, 2.2, 2.3, 2.4, 2.5 and 2.6; RVM environments too
 - recovery on timeout: try to keep running the examples if one timeout

With this we marked as *provisional* the Ruby and the Clipboard modules.

On the other hand, this release *may* break some examples due how we
changed the capture semantics and some option renames.

Probably the major impact comes from the zone delimiter: now `byexample`
will *not* find examples anywhere, instead, it will find them in very
specific places or zones that depends of the file extension.

For [C/C++ examples](/{{ site.uprefix }}/languages/cpp), now we use ``?:`` and ``::`` as the primary and
secondary prompts.

And a lot of more little enhancements, fixes and improvements.

See the full
[8.0.0 changelog](https://github.com/byexamples/byexample/releases/tag/8.0.0)

## 7.4.0

This release comes with an *experimental* support for
[Javascript/Nodejs](/{{ site.uprefix }}/languages/javascript)
and the ability to run examples in parallel.

See the full
[7.4.0 changelog](https://github.com/byexamples/byexample/releases/tag/7.4.0)
