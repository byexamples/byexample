```python
>>> print("\n  \n  Some line") # should fail (missing indentation)
<...>
Some line

>>> print("\n  \n  Some line") # should fail (missing indentation)
Some line

>>> print("\n  \nSome line")  # should fail because we are using pre-11.0.0 behavour  # byexample: -ignore-first-empty-lines
Some line
```
