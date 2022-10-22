<!--
Check that we have byexample installed first
$ hash byexample                                    # byexample: +fail-fast

$ alias byexample=byexample\ --pretty\ none

--
-->

# Environment Variables

`byexample` passes the environment variables to the
interpreters and they are available from the examples and modules.

This is the default and quite handy if you want to make your
documentation *configurable* for *scripting*.

Let's say you have a [shell](/{{ site.uprefix }}/languages/shell.md)
example:

```shell
$ if [ "$PWD" != "/root" ]; then
>   echo "You must run this script from /root"
> fi
You must run this script from /root
```


## Pasting a captured environment variable

But what if we want to *capture* their value and
[paste them](/{{ site.uprefix }}/basic/capture-and-paste.md) as part of
an example?

Consider an example where a Python example *depends* on the current
directory.

Because you could be running `byexample` from *anywhere*, such example
would likely fail: the output is not deterministic.

However you could [paste](/{{ site.uprefix
}}/basic/capture-and-paste.md) the environment variable `$PWD` which has
the current directory as the expected output.

```shell
$ cat test/ds/capture-env.doc               # byexample: +rm=  -tags
    >>> import os
    >>> assert '<PWD>' == os.getcwd()    # byexample: +paste
```

You just need to pass which variables from the environment will be in
the clipboard of `byexample` so they can be pasted.

```shell
$ byexample -l python --capture-env-var PWD test/ds/capture-env.doc
<...>
[PASS] Pass: 2 Fail: 0 Skip: 0
```

You can capture as many environment variables as you want:

```shell
$ byexample -l python --capture-env-vars PWD,HOME,USER test/ds/capture-env.doc
<...>
[PASS] Pass: 2 Fail: 0 Skip: 0
```

## Conditional execution on a captured environment variable

Perhaps the most useful combination is with
[conditionals](/{{site.uprefix }}/advanced/conditional-execution.md).

Consider the following toy-example that it is executed *unless* the
given environment variable is passed:

```shell
$ cat test/ds/capture-bomb.doc               # byexample: +rm= 
    $ echo 'Booom!'    # byexample: +unless=bomb_disabled
    The bomb should not explode!
```

Running the example with an empty or unset variable `bomb_disabled` will
make the example to run and fail (as expected, the bomb exploded).

```shell
$ echo $bomb_disabled  # empty, it is not set
$ byexample -l shell --capture-env-var bomb_disabled test/ds/capture-bomb.doc
<...>
Expected:
The bomb should not explode!
Got:
Booom!
<...>
[FAIL] Pass: 0 Fail: 1 Skip: 0
```

But setting anything to the variable we can *skip* the execution of the
example.

```shell
$ export bomb_disabled=some
$ byexample -l shell --capture-env-var bomb_disabled test/ds/capture-bomb.doc
<...>
[PASS] Pass: 0 Fail: 0 Skip: 1
```

> **Note:** in both cases `bomb_disabled` was put in the clipboard, this
> is required because `+unless` will complain if the variable is not
> there (empty or not empty).

> *New* in ``byexample 10.1.0``. This feature is marked as ``experimental``.
