# Rust

Run the `Rust` examples calling `byexample` as:

```shell
$ byexample -l rust your-file-here                # byexample: +skip
```

You need the have installed `evcxr`, an interactive interpreter
for `Rust`.

Check its [download page](https://github.com/google/evcxr)

> **Note**: current versions of `evcxr` (0.10.0) has a high run time:
> around 20 seconds for starting up the runner and around 2 seconds per
> example. There is [an ongoing work](https://github.com/google/evcxr/issues/184)
> to improve this.

> **Stability**: ``experimental`` - non backward compatibility changes are
> possible or even removal between versions (even patch versions).

> *New* in ``byexample 10.2.0``.

<!-- matrix CI begin -->
<!-- matrix CI end -->

## Find interactive examples

For ``Rust``, ``byexample`` uses the ``>>`` string as the primary prompt
and ``::`` as the secondary prompt.


```rust
>> 1 + 2
3

>> fn hello() {
::    println!("hello bla world"); // classic
:: }

>> hello();           // byexample: +norm-ws
hello   <...>   world
```

> Currently the flags/options can only be set in the single-line
> comments (`//`)

### The object returned

As you may know in `Rust` almost everything is an expression and
`byexample` will take and print the value of the expression.

```rust
>> 1 + 2
3
```

These expressions can be turn into a statement appending a semicolon
in which case `byexample` will not print anything.

```rust
>> 1 + 2;
```

## Pretty print

`byexample` uses the default *pretty print* of Rust with the format
`"{:?}"`.

This works quite well out of the box for native objects and objects with
the `#[derive(Debug)]`:

```rust
>> #[derive(Debug)]
:: struct Point {
::   x: f32,
::   y: f32,
:: }

>> let p1 = Point { x: 2.0, y: 3.0 };
>> p1
Point { x: 2.0, y: 3.0 }

>> let array = [1, 2, 3];
>> let tuple = (1, true, 2.3);

>> array
[1, 2, 3]
>> tuple
(1, true, 2.3)
```

> **Note**: pretty print for arrays and tuple are supported but only
> up to 12 elements. This is a restriction of Rust.

## Known limitations


### Runtime performance

`evcxr` has a high runtime cost. `byexample` waits up to 30 seconds for
the interpreter to be up and up to 8 seconds per example.

If you want to increase these timeouts you can do it with
`-x-dfl-timeout` and `--timeout`.

### Output arrives late

`evcxr` *may* tell `byexample` that an example finished
*before* it really did. `byexample` works around this and waits a little
after each example execution.

You can control how much time `byexample` will wait with
`-x-delayafterprompt`. The default is a quarter of a second.

If you run an example and this fails because the last part of the
expected output is missing **and** that output appears at the begin
of the *next* example, you are hitting this limitation.

Try to increment the wait time with `-x-delayafterprompt`.

### Slices and closures

Slices are not supported if they are written in the main scope
but there is no problem if the slices are defined in the scope of a
function

```rust
>> let array = [1, 2, 3];

>> // this will not work
>> let slice: &[i32] = &array[0..2];      // byexample: +skip

>> // but this is perfectly fine
>> fn bar(slice: &[i32]) {
::    println!("{:?}", slice);
:: }

>> bar(&array[0..2]);
[1, 2]
```

The same limitation happens with closures: they are not supported in the
main scope but in the functions are okay.

```rust
>> let i = 4;

>> // this will not work
>> let closure_implicit = |j| i + j;  // byexample: +skip

>> // but this is perfectly fine
>> fn baz() {
::    let i = 4;
::    let closure_implicit = |j| i + j;
::    println!("{:?}", closure_implicit(2));
:: }

>> baz();
6
```

### Type text

The [type](/{{ site.uprefix }}/basic/input)
feature (`+type`) is not supported.

## Rust specific options

```
$ byexample -l rust --show-options       # byexample: +norm-ws
<...>
rust's specific options
-----------------------
  None.
```
