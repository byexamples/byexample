<!--
Check that we have byexample installed first
$ hash byexample                                    # byexample: +fail-fast

$ alias byexample=byexample\ --pretty\ none

--
-->

# Setup and Tear Down

Sometimes you need to handle resources in the tests: you need to make
sure that you have them before running any test and you need to release
them at the end.

Think in a web server, a virtual machine, a database connection.

Let's take the last one.

Imagine that you want to show how to interact with your database to explain
the underlying model and relationships. You obviously need to *setup* the
database first with some dataset in order to show how to interact with it.

It is also reasonable to *tear down* the database connection at the end.

You could write:

```
$ cat test/ds/db-stock-model.md                         # byexample: +rm=~
This is a quick introduction to the database schema.
~    >>> import sqlite3
~    >>> c = sqlite3.connect(':memory:')
~    >>> _ = c.executescript(open('test/ds/stock.sql').read())  # ---> # byexample: +fail-fast
~
Get the stocks' prices
~    >>> _ = c.execute('select price from stocks')
~
Do not forget to close the connection
~    >>> c.close()                         # ---> # byexample: -skip
~
```

In a happy and perfect world this should run smoothly:

```
$ byexample -l python test/ds/db-stock-model.md
<...>
File test/ds/db-stock-model.md, 5/5 test ran in <...> seconds
[PASS] Pass: 5 Fail: 0 Skip: 0
```

Now, if for some reason you cannot load the initial dump, it makes sense
to stop the whole execution: this is known as ``fail fast`` and it is
archived with the ``+fail-fast`` flag.

This should *skip* all the examples, however no matter what happen,
you always want to leave a clean environment and close the connection:
you can force this saying that the example must *not* be skipped (``-skip``).

Check what happen if we delete the sql file: the example ``c.executescript``
should fail and because ``+fail-safe`` is in effect for, the rest of the
example should be *skippped* except the last one because explicitly
says *do not skip* me with ``-skip``.

```
$ mv test/ds/stock.sql test/ds/renamed.sql

$ byexample -l python test/ds/db-stock-model.md
<...>
File test/ds/db-stock-model.md, 5/5 test ran in <...> seconds
[FAIL] Pass: 3 Fail: 1 Skip: 1
```

<!--
Revert the dump rename
$ mv test/ds/renamed.sql test/ds/stock.sql      # byexample: -skip +pass
-->

> *Note:* If the example fails due a timeout or if it crashes, the execution
> will abort immediately *without* executing any example even if
> they have ``-skip``. This is because these kind of failures may had left the
> interpreter in a invalid state and the execution cannot be resumed.
>
> The best strategy would be create a [concern module](docs/contrib/how-to-hook-to-events-with-concerns.md)
> and hook to the ``finish`` event and perform there all the clean up, if any.


