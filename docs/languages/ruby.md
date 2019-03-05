# Ruby

``byexample`` can execute ``Ruby``

You need the default interpreter ``irb`` installed first.
Check its [download page](https://www.ruby-lang.org/en/downloads/)

> **Stability**: ``provisional`` - low impact non backward compatibility
> changes may occur between versions; but in general a change like that
> will happen only between major versions.

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
> is printted in a deterministic way with its keys sorted.
> Before ``byexample 8.0.0`` the order was undefined.

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

