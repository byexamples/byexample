<!--
Check that we have byexample installed first
$ hash byexample                                    # byexample: +fail-fast

$ alias byexample=byexample\ --pretty\ none

--
-->
# Normalize Whitespace

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
>> Array(0...20)				# byexample: +norm-ws
=> [0,   1,  2,  3,  4,  5,  6,  7,  8,  9,
   10,  11, 12, 13, 14, 15, 16, 17, 18, 19]
```

## Empty lines at the begin are ignored by default


Consider the following `"\n  \nSome line"` output. The following three
examples matches because by default `byexample` discards any empty line
at the begin of the output.

```python
>>> someline = "\n  \nSome line"

>>> print(someline)  # OK: <...> captures the empty lines
<...>
Some line

>>> print(someline)  # OK too: the same reason above
<...>Some line

>>> print(someline)  # OK: byexample ignores the empty lines "as if" a <...> was there
Some line
```

`byexample` understands as "empty lines" lines made entirely of spaces
and tabs ended with a new line. It is subtle but such definition does
not include indentation.

Consider the following `"\n  \n  Some indented line"`:

```python
>>> someindented = "\n  \n  Some indented line"

>>> print(someindented)  # FAIL: the example is not expecting indentation    # byexample: +pass
<...>
Some indented line

>>> print(someindented)  # OK: <...> captures all including the indentation
<...>Some indented line

>>> print(someindented)  # FAIL: byexample ignores the empty lines but not the indentation   # byexample: +pass
Some indented line
```

When `+norm-ws` is enabled, those two `FAIL` examples will work because
`byexample` relaxes the definition of empty lines and replaces by
"any whitespace" which the indentation gets included:

```python
>>> print(someindented) # byexample: +norm-ws
<...>
Some indented line

>>> print(someindented)  # byexample: +norm-ws
Some indented line
```

<!--

Test a few more combinations

>>> print(someindented) # byexample: +norm-ws
<...>Some indented line

Test the incorrect combinations and check that they are actually failing

$ byexample -l python test/bad-empty-line.md
<...>
[FAIL] Pass: 0 Fail: 2 Skip: 0

-->
