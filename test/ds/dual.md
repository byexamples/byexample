This `.md` test file should work even if `+py-doctest` is enabled or not
form the command line so the following should not be altered by that
as `<...>` (aka `+tags`) should work by default regardless of
`+py-doctest`.

```shell
$ echo "foo"
f<...>
```

Run `+py-doctest +ELLIPSIS` which enables `+tags` for this example:

```python
>>> print("foo")   # byexample: +py-doctest +ELLIPSIS
f...
```

This example is not affected by `+py-doctest` which disables `+tags`
because `+py-doctest` was applied to the example above.

```shell
$ echo "foo"
f<...>
```

