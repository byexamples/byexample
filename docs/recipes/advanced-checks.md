# Advanced Checks

### <a href="#rich-comp">Rich comparison<a/>

Imagine that you want to check how many words has a file
but you cannot check the *exact* count.

Instead you are ok if the file has *more than x* words.

How to do that in ``byexample``?

Just *combine different runners*
[capturing](/{{ site.uprefix }}/basic/capture-and-paste)
the output of one
and [pasting](/{{ site.uprefix }}/basic/capture-and-paste)
it into another where the comparison that you
want can be much easier to implement.

> For me, Python is my first choice

```shell
$ wc -w test/ds/about-lic.doc
<count> test/ds/about-lic.doc
```

```python
>>> <count> > 50        # byexample: +paste
True
```

### Use the pretty printer

True story: a program logs into a file a set of dictionaries,
something like this:

```shell
$ cat test/ds/log
Sep 30 15:44:01 system: Loaded modules
Sep 30 15:44:01 system: Status {"network": {"eth0": True, "wifi0": False, "wifi1": False, "eth1": True, "eth2": False}, "disk": True, "io": True}
```

Unfortunately the ``Status`` dictionary may be printed with its keys
in an *arbitrary order* so checking it directly will not always work.

We could parse the log and do a more manual check... **or** we could
think out of the box and *combine* different runners again:

```shell
$ cat test/ds/log
Sep 30 15:44:01 system: Loaded modules
Sep 30 15:44:01 system: Status <dict>
```

```python
>>> <dict>              # byexample: +paste +diff=ndiff
{'disk': True,
 'io': True,
 'network': {'eth0': True,
             'eth1': True,
             'eth2': False,
             'wifi0': False,
             'wifi1': False}}
```

Some runners like Python and Ruby enable by default a *pretty printer*:
native objects, specially the deeply nested ones, are printed in a *nice
deterministic human way*.

> Tip: for long and complex outputs like this one, you may want to use
> a [differ](/{{ site.uprefix }}/docs/overview/differences.md)
> that can highlight the small differences in case the example fail.

