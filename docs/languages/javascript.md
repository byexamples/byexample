# Javascript

Run the `Javascript` examples calling `byexample` as:

```shell
$ byexample -l javascript your-file-here                # byexample: +skip
```

``byexample`` can execute ``Javascript`` code using ``nodejs``.

You can get the `nodejs` interpreter from [here](https://nodejs.org/en/download/).

> **Stability**: ``experimental`` - non backward compatibility changes are
> possible or even removal between versions (even patch versions).

### Versions tested

We tested `byexample` with the following versions of the language
and the underlying runner or interpreter:

<!-- matrix CI begin -->

| Language   | Runner/Interpreter   |
|------------|----------------------|
| 10.x       | 10.24.1              |
| 12.x       | 12.22.10             |
| 14.x       | 14.19.0              |
| 15.x       | 15.14.0              |
| 16.x       | 16.14.0              |

<!-- matrix CI end -->

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

## Pretty print

``byexample`` uses the default *pretty printer* of ``nodejs``.


### Definitions with and without var

An object definition without ``var`` will print itself:

```javascript
> var o1 = 1
> o2 = 2
2
```

### Trailing whitespace

Some objects are printed with a trailing whitespace but this should be
inoffensive.

> **Note:** for ``7.x.x`` versions of ``byexample`` you need to use ``+norm-ws``
> to [ignore the whitespace](/{{ site.uprefix }}/basic/normalize-whitespace)
> explicitly.

> **Changed** in ``byexample 8.0.0``: the trailing whitespace is not
> a problem anymore unless you are using the ``as-is``
> [terminal emulation](/{{ site.uprefix }}/advanced/terminal-emulation) mode.

### Too deep nested objects

If an object is too nested, ``nodejs`` will just say ``[Object]``, this
may or may not be a problem, just keep it in mind:

```javascript
> {a: {b: {c: {d: {}}}}}
{ a: { b: { c: [Object] } } }
```

### Undefined is not printed

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


## Known limitations

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

### Unexpected outputs

I didn't expect this:

```javascript
> var j = 2;
> for (var i = 0; i < 4; ++i) {
.    j += i;
. };
8
```

Also, creating a *readline* interface (`readline` module, `createInterface`
function) may enable the `echo` mode so all the code that `byexample` types
will be reflected in the output.

You can avoid this passing `false` to `terminal` option of `createInterface`
(see the [reference](https://nodejs.org/api/readline.html)) but
still there may be *spurious* outputs.

### Abort on a timeout

If a `Javascript` example takes too long and
[timeout](/{{ site.uprefix }}/basic/timeout), the whole execution
timeout.

### Type text

The [type](/{{ site.uprefix }}/basic/input)
feature (`+type`) is not supported.

## Javascript specific options

```
$ byexample -l javascript --show-options       # byexample: +norm-ws
<...>
javascript's specific options
-----------------------------
  None.
<...>
```
