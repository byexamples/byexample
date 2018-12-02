# Skip and Pass

``skip`` will skip the example completely while ``pass`` will execute it
normally but it will not check the output.

See the difference between those two in these ``Python`` examples:

```python
>>> def f():
...    print("Choosing a random number...")
...    return 42

>>> a = 1
>>> a = f() # this assignment will not be executed # byexample: +skip

>>> a
1

>>> a = f() # execute the code but ignore the output # byexample: +pass

>>> a
42

>>> a = f() # the output is not ignored so we must check for it
Choosing a random number...
```

See how to use ``-skip`` to support
[clean ups](/{{ site.uprefix }}/basic/setup-and-tear-down).
