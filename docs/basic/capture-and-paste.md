
# Capture and Paste

Use ``<name>`` to capture some output
and *paste it* in the next examples.

This quite useful if you have some non-deterministic data that
you want to use later:

```python
>>> def gen_number():
...     n = 42
...     print("Generating: %i" % n)
...     return n

>>> a = gen_number()
Generating: <random-number>

>>> a == <random-number>     # byexample: +paste
True
```

You can even paste it in the ``expected`` of the examples that follows:

```python
>>> a                 # byexample: +paste
<random-number>

>>> a                 # byexample: +paste -capture
<random-number>
```

> Disabling the capture with `-tags` or `-capture` you can be sure that
> the tags come from a previous example
> and they are not captured from the current example but it is not mandatory.

Pasting works across languages: this is a very convenient way to copy and
paste some data from one language to another.

```ruby
>> puts "This is not very random: <random-number>"  # byexample: +paste
This is not very random: 42
```

## Capture

``byexample`` will always try to capture the most smaller string first.

If your named tags are capturing more data than you want,
you may want to know what [strategies](/{{ site.uprefix }}/advanced/greedy-lazy-tags)
``byexample`` uses.

Using unamed tags ``<...>`` or adding more context around the named tag fixes
the problem most of the time.

### Valid names

Only alphanumeric characters plus the minus and the dot symbols
are valid characters for a tag name and a name must starts with
a letter or with a dot.

This restricted set prevents unwanted false positives:

```python
>>> def fib():
...     pass

>>> fib
<function fib at <address>>
```

## Disable the tags

With `-tags` all the tags are taken as literal: the capture tags
(`<foo>`) and the unnamed tags (`<...>`).

```python
>>> print("hey <a><...><...><a>")   # byexample: -tags
hey <a><...><...><a>
```

With `-capture` only the capture tags are taken as literal.

```python
>>> print("hey <a><...> <...><a>")   # byexample: -capture
hey <a><...> <...><a>
```

> *New* in `byexample 10.3.0`: the `-capture` flag was added.

## Limitation

If an example fails, its named tags are not captured.

This may lead to other example fail or abort because the tags
that they used cannot be pasted.

This can be a little problematic in the examples that are supposed
to do the [clean up](/{{ site.uprefix }}/basic/setup-and-tear-down) with ``-skip``.
