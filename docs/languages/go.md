# Go

Run the `Go` examples calling `byexample` as:

```shell
$ byexample -l go your-file-here                # byexample: +skip
```

You need the have installed `yaegi`, an interactive interpreter
for `Go`.

Check its [download page](https://github.com/traefik/yaegi)

> **Stability**: ``experimental`` - non backward compatibility changes are
> possible or even removal between versions (even patch versions).

> *New* in ``byexample 10.2.0``.

<!-- matrix CI begin -->

| Language   | Runner/Interpreter   |
|------------|----------------------|
| 1.19       | v0.14.0              |
| 1.18       | v0.14.0              |
| 1.17       | v0.13.0              |
| 1.16       | v0.13.0              |

<!-- matrix CI end -->

## Find interactive examples

For ``Go``, ``byexample`` uses the ``>`` string as the primary prompt
and ``.`` as the secondary prompt.


```go
> a := 1
> b := 2
> a + b
: 3

> func g(a, b, c int) int {
.   c += a
.   c += b
.
.   return c
. }

> g(1, 2, 3)
: 6
```

### The object returned

Because everything in `yaegi`, the interpreter of `Go`, is evaluated
as an expression, everything returns something.

This is annoying if you want to write several ``Go`` lines without checking
the results.

For this reason, ``byexample`` suppress the representation of the object
returned unless the example has a ``:``.

In the following case, the first example is executed but the value of
its expression evaluated is not checked while in the second example
it is checked.

```go
> 1 + 2

> 1 + 2
: 3
```

Notice how the second example has a `:` to mark the value of the
expression to be compared. This mark is used by `byexample` to know when
or when not suppress the value.

This affects only the value of the expression, it has no effect on the
output of the example in general.

For example the prints are not suppressed:

```go
> fmt.Println("hello")
hello
```

You can change the behavior of `byexample` with:

 - `+go-expr-print=true` to print always the expression, disabling the
suppression
 - `+go-expr-print=false` to never print the expression.
 - `+go-expr-print=auto` to let `byexample` decide when to suppress or
not based on the mark `:`. This is the default.

This and any other flag/option can be set in the example's comment.

```go
> fmt.Println("hello      world")       // byexample: +norm-ws
hello world
```

> Currently the flags/options can only be set in the single-line
> comments (`//`); block comments are not supported (`/* .. */`).

## Known limitations

`yaegi` may sometime *crash or panic*. In general this is because you are
trying to run a code using undefined variables.

If you find a crash/panic, review the example. Make sure that the
**previous** examples also worked.

However there are some things that `yaegi` does not currently support.
Here are all the ones that `byexample` is aware of.

### Pointers and slices

Pointers in the main space are not supported but pointers in a function
are okay

```go
> sum := 1

> // not supported
> var p *int = &sum  // byexample: +skip

> // supported
> func bar(p *int) {
.    *p = 37
. }

> bar(&sum)
> sum
: 37
```

The same limitation happens with slices: they are not supported in the
main space but in the functions are okay.

```go
> primes := [6]int{2, 3, 5, 7, 11, 13}

> // not supported
> var subprimes[]int = primes[1:4]    // byexample: +skip

> // supported
> func chunk(primes *[6]int) {
.    var subprimes[]int = primes[1:4]
.    fmt.Println(subprimes)
. }

> chunk(&primes)
[3 5 7]
```

Slices in the main space can be created using `make`:

```go
> mem := make([]int, 5)
> mem
: [0 0 0 0 0]
```

### Type assertions and switches

*Type assertions* are not supported but you can use *type switches*
in a function

```go
> var iface interface{} = "hello"

> // not supported
> s := i.(string)     // byexample: +skip

> // supported
> func do(i interface{}) {
.       switch v := i.(type) {
.       case int:
.               fmt.Printf("Twice %v is %v\n", v, v*2)
.       case string:
.               fmt.Printf("%q is %v bytes long\n", v, len(v))
.       default:
.               fmt.Printf("I don't know about type %T!\n", v)
.       }
. }

> do(21)
Twice 21 is 42
> do("foo")
"foo" is 3 bytes long
> do(3.1416)
I don't know about type float64!
```

### Type text

The [type](/{{ site.uprefix }}/basic/input)
feature (`+type`) is not supported.

## Go specific options

```
$ byexample -l go --show-options       # byexample: +norm-ws
<...>
go's specific options
---------------------
<...>:
  +go-expr-print {auto,true,false}
                        print the expression's value (true); suppress it
                        (false); or print it only if the example has a colon
                        (auto, the default)
```
