# Ruby

Run the `Ruby` examples calling `byexample` as:

```shell
$ byexample -l ruby your-file-here                # byexample: +skip
```

You need the default interpreter ``irb`` installed first.
Check its [download page](https://www.ruby-lang.org/en/downloads/)

> **Stability**: ``provisional`` - low impact non backward compatibility
> changes may occur between versions; but in general a change like that
> will happen only between major versions.

### Versions tested

We tested `byexample` with the following versions of the language
and the underlying runner or interpreter:

<!-- matrix CI begin -->

| Language   | Runner/Interpreter   |
|:----------:|:--------------------:|
| 2.4        | 0.9.6                |
| 2.5        | 0.9.6                |
| 2.6        | 1.0.0                |
| 2.7        | 1.2.6                |
| 3.0        | 1.3.5                |
| 3.1        | 1.4.1                |

<!-- matrix CI end -->

## Find interactive examples

For ``Ruby``, ``byexample`` uses the ``>>`` string as the primary prompt
and ``..`` as the secondary prompt.


```ruby
>> a = 1
>> b = 2
>> a + b
=> 3

>> def g(a, b, c)
..     c += a
..     c += b
..
..     return c
.. end

>> g(1, 2, 3)
=> 6
```

## Pretty print

``byexample`` changes the default IRB's ``inspector`` and uses ``pp``
(pretty print).

If you want, you can use the IRB's default one with
the option ``-ruby-pretty-print``

```ruby
>> {3=>{5=>Array(0..20), 4=>"aaaaaaaa"}, 1 => 2}
=> {1=>2,
 3=>
  {4=>"aaaaaaaa",
   5=>
    [0,
     1,
     <...>
     19,
     20]}}
```

> **Changed** in ``byexample 8.0.0``: make sure that a ``Hash``
> is printed in a deterministic way with its keys sorted.
> Before ``byexample 8.0.0`` the order was undefined.

> **Changed** in `byexample 10.0.4`: IRB `> 1.2.2` adds a newline
> between the `=>` marker and the output if it spans more than one line.
> To maintain backward compatibility `byexample` will suppress that
> newline by default.
> If you don't want that you can pass `+ruby-start-large-output-in-new-line`
> flag in the [command line](/{{ site.uprefix }}/basic/options) with `-o`.

### The object returned

Because everything in Ruby is an expression, everything returns a result.

This is annoying if you want to write several ``Ruby`` lines without checking
the results.

For this reason, ``byexample`` suppress the representation of the object
returned unless the example has a ``=>``.

In the following case, the result of each expression is not printed and
therefor they are not checked:

```ruby
>> 1 + 2

>> puts "hello"
hello
```

Now, compare it with this. It is the same example but the objects returned
are checked too.

```ruby
>> 1 + 2
=> 3

>> puts "hello"
hello
=> nil
```

If you want to check all the expressions, you can force to print all the
objects returned using the ``+ruby-expr-print=true``.

On the other hand, you can disable it forever
with ``+ruby-expr-print=false``.

The default is ``+ruby-expr-print=auto``.

## Ruby specific options

```
$ byexample -l ruby --show-options       # byexample: +norm-ws
<...>
ruby's specific options
-----------------------
<...>:
  +ruby-pretty-print    enable the pretty print enhancement.
  +ruby-expr-print {auto,true,false}
                        print the expression's value (true); suppress it
                        (false); or print it only if the example has a =>
                        (auto, the default)
  +ruby-start-large-output-in-new-line
                        add a newline after the => if the output that follows
                        does not fit in a single line. (irb >= 1.2.2)
<...>
```
