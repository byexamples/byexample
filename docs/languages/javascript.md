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

The snippets can be inside of a ``Javascript`` comment.

The examples are detected as long as they
begin with the correct prompts and they are separated by a new line
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

## Undefinied is not printed

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

### Anonymous functions

Functions can be created but the cannot be annonimous, this is
a ``nodejs`` limitation.

```
function () {
  return 1 + 1;
}
```

Anonymous function can be created as part of an larger example.

```javascript
> var a = [1, 2, 3]
> a.map(function (i) { return i * 2; })
[ 2, 4, 6 ]
```

### Trailing whitespace

Some objects are printed with a trailing whitespace. If you don't want to
check them, use ``+rtrim``:

```javascript
> {a: {b: {c: 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', d: 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'}}}
{ a: 
   { b: 
      { c: 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
        d: 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' } } }
```

### Too deep nested objects

If an object is too nested, ``nodejs`` will just say ``[Object]``, this
may or may not be a problem, just keep it in mind:

```javascript
> {a: {b: {c: {d: {}}}}}
{ a: { b: { c: [Object] } } }
```

