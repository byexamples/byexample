`byexample` requires `+force-echo-filtering` and still it gets some
unwanted whitespace.

Unhappy

```python
>>> import questionary

>>> print('Hello', questionary.text("What's your first name?").ask())  # byexample: +type +term=ansi -x-byexample-brk 1
? What's your first name? [john]
Hello john
```
