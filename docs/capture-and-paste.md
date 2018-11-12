
# Capture and Paste

As we mentioned before, you can use ``<name>`` to capture some output
and *paste it* in the next examples.

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

You can even paste it in the ``expected`` of the next examples:

```python
>>> a                 # byexample: +paste
<random-number>

>>> a                 # byexample: +paste -tags
<random-number>
```

Disabling the capture you can be sure that the tags come from a previous example
and they are not captured from the current example but it is not mandatory.

Pasteing works across languages: this is a very convenient way to copy and
paste some data from one language to another.

```ruby
>> puts "This is not very random: <random-number>"  # byexample: +paste
This is not very random: 42
```

