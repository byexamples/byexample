# Javascript

``byexample`` can execute ``Javascript`` code using ``nodejs``.

You can get it the interpreter from [here](https://nodejs.org/en/download/).

## Find interactive examples

For ``Javascript``, ``byexample`` uses the ``>`` string as the primary prompt
and ``.`` as the secondary prompt.

```javascript
> function mul(a, b) {
.   return a * b;
. }

> mul(4, 2)
8
```

The snippets can be inside of a ``Javascript`` comment as well.

The examples are detected as long as they
begin with the correct prompts and they are separated by a blank line
or has a lower indentation level:

```javascript
/*
  Javascript comment here, now and example:
  > 1 + 2
  3

  More comments. Notice the extra blank line between this text and
  the previous example.

  Here is another example, indented this time:
    > 4 + 4
    8
  More comments. Notice there is no need for a blank line this time
  because this text has a lower indentation level.
*/
```

## Undefined is not printed

Functions definitions and other expression returns ``undefined``
which can be annoying to keep checking for it each time.

``byexample`` will not print them:

```javascript
> var o = {}
> o.noexistent
```

If you want to check for an ``undefined`` value, use ``===``

```javascript
> o.noexistent === undefined
true
```

This affects only the return value, not the value of a more
complex object, like an array with ``undefined`` values:

```javascript
> [1, undefined, 2]
[ 1, undefined, 2 ]
```

## Observations

### Definitions with and without var

An object definition without var will print itself:

```javascript
> var o1 = 1
> o2 = 2
2
```

### Comments may affect the output

This may sound crazy but I found that if you add a ``// comment``
or a ``/* comment */`` at the end of an example of a literal object
(like a nested object), the output may not be the full object.

This is important because ``byexample`` uses the ``// comment`` as a
way to pass options and flags to the example.

The best solution seems to use a temporal variable:

```javascript
> var tmp = [1, 2, 3];
> tmp   // some comment
[ 1, 2, 3 ]
```

### Anonymous functions

Functions can be created but the cannot be anonymous, this is
a ``nodejs`` limitation.

This would fail:

```
function () {
  return 1 + 1;
}
```

Anonymous functions can be *created as part of* a larger example.

```javascript
> var a = [1, 2, 3]
> a.map(function (i) { return i * 2; })
[ 2, 4, 6 ]
```

### Trailing whitespace

Some objects are printed with a trailing whitespace.

This is not a problem unless you are using a ``as-is``
[terminal emulation](docs/advanced/terminal-emulation.md).

### Too deep nested objects

If an object is too nested, ``nodejs`` will just say ``[Object]``, this
may or may not be a problem, just keep it in mind:

```javascript
> {a: {b: {c: {d: {}}}}}
{ a: { b: { c: [Object] } } }
```

