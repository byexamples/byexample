# Greedy and Lazy Tags

A tag is marked with the symbols ``<`` and ``>`` and can be either of two types:
named like ``<foo-name>`` or unnamed like ``<...>``.

Both kinds of tags can match anything but there is a small difference.

Because the named tags are used to [capture](/{{ site.uprefix }}/basic/capture-and-paste)
a given string and [paste](/{{ site.uprefix }}/basic/capture-and-paste) it later,
it is assumed that a named tag is intended to
match a small string, therefore the regex used is non-greedy or lazy (``.*?``).

The usage of unnamed tags is more diffuse: they can be used to ignore
small portions or large multiline ones.

The heuristic is that the unnamed tags are non-greedy by
default but the unamed tags *at the end of a line* are greedy (``.*``).

Here are some examples of the implications of this difference.

Consider the following string.

```python
>>> a = '''x 1 oneline
... x 2 twoline
... x 3 fooline
... x 4 barline'''
```

If we are interested in only the last two numbers we could write
something like this:

```python
>>> print(a)
<...>
x <foo> fooline
x <bar> barline

>>> print("""foo: '<foo>'\nbar: '<bar>'""")       # byexample: +paste
foo: '3'
bar: '4'
```

This works because the unnamed tag is at the end of the line and therefore
its regex is greedy.

If this wasn't the case, the named tag below will probably be forced to
capture more strings than intended.

Here is the same example but instead of using an unnamed tag, we use
a named tag to force it to be non-greedy. See what happens with the ``foo``
and ``bar`` captures:

```python
>>> print(a)
<ignore-me>
x <foo> fooline
x <bar> barline

>>> print("""foo: '<foo>'\nbar: '<bar>'""")       # byexample: +paste
foo: '2 twoline
x 3'
bar: '4'
```

Consider now another example. It works because the unnamed tags are non-greedy
except on the end (in this example we want to capture Joe's token)

```python
>>> print('{user=john,attr=2,token=53,age=33;user=joe,attr=3,token=111,age=33;user=jane,attr=12,token=153,age=3}')
<...>user=joe,<...>,token=<token>,<...>

>>> print("""token: '<token>'""")       # byexample: +paste
token: '111'
```
