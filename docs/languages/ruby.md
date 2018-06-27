# Ruby

``byexample`` can execute ``Ruby``

You need the default interpreter ``irb`` installed first.
Check its [download page](https://www.ruby-lang.org/en/downloads/)

## Find interactive examples

For ``Ruby``, ``byexample`` uses the ``>>`` string as the primary and
secondary prompts.

Because of this, all the consecutive lines that start with ``>>`` will belong
to the same example and they will be executed together.

The ``=>`` marker is written by the Ruby interpreter and not by ``byexample``.
It is left as is as this is quite common in the Ruby examples and literature.

```ruby
>> a = 1;
>> b = 2;
>> a + b
=> 3

>> def g(a, b, c)
>>     c += a
>>     c += b
>>
>>     return c
>> end;

>> g(1, 2, 3)
=> 6

```

## The object returned

``>>`` is the only prompt the ``byexample`` uses.

As said before the ``=>`` marker is written by the Ruby interpreter
and not by ``byexample``.

```ruby
>> 1 + 2
=> 3

```

Because everything in Ruby is an expression, everything returns a result.

This is annoying if you want to write several ``Ruby`` lines without checking
the results.

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

An alternative could be group all the expression and run the example
with the ``pass`` option to ignore the intermediate results.

```ruby
>> a = 1       # byexample: +pass
>> b = 2

>> a + b
=> 3

```
