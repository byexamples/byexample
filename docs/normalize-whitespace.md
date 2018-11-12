# Normalize whitespace

Replace any sequence of whitespace by a single one.

It is particular useful if the output is a little messy:
you can put extra spaces and new lines and it will
still be valid.

Consider this example that prints a table but, for
some reason, it uses only a single space as separator:

```python
>>> print("Name Age kev 22 luc 23")
Name Age kev 22 luc 23
```

It looks ugly, does it?

We can add extra spaces and new lines to write a better
example and combine it with ``+norm-ws`` so those extra spaces
do not count.

```python
>>> print("Name Age kev 22 luc 23")     # byexample: +norm-ws
Name    Age
kev     22
luc     23
```

Here is another example, this time written in ``Ruby``:

```ruby
Array(0...20)				# byexample: +norm-ws

out:
=> [0,   1,  2,  3,  4,  5,  6,  7,  8,  9,
   10,  11, 12, 13, 14, 15, 16, 17, 18, 19]
```

