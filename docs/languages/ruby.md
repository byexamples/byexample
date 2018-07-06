# Ruby

``byexample`` can execute ``Ruby``

You need the default interpreter ``irb`` installed first.
Check its [download page](https://www.ruby-lang.org/en/downloads/)

## Find interactive examples

For ``Ruby``, ``byexample`` uses the ``>>`` string as the primary prompt
and ``..`` as the secondary prompt.


```ruby
>> a = 1;
>> b = 2;
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

## The object returned

Because everything in Ruby is an expression, everything returns a result.

This is annoying if you want to write several ``Ruby`` lines without checking
the results.

For this reason, ``byexample`` suppress the representation of the object
returned unless the example has a ``=>``.

In the following case, no object returned is not printed and there for
it is not checked:

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

On the other hand, you can disable it for never see an object's print
with ``+ruby-expr-print=false``.

The default is ``+ruby-expr-print=auto``.

## Semicolon side effect

The semicolon ``;`` at the end of each expression will suppress the print of
the returned object.

But it has also a *side effect*: all the expressions that end with ``;`` are not
executed until an expression without ``;`` is written.

This is how ``irb`` works behind scenes, so be careful with the use of
semicolons. It is easy to get confused with this weird effect.

```ruby
>> a = 1;
>> b = 2;
>> a + b     # nice without side effects
=> 3

>> puts '4'; # nothing is printed (what a surprise!)

>> nil       # this dummy expression is enough to flush the previous one
4
=> nil

```

# Pretty print

``byexample`` changes the default IRB's ``inspector`` and uses ``pp``
(pretty print).

If you want, you can use the IRB's default one with
the option ``-ruby-pretty-print``


