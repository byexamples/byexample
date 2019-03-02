<!--
Check that we have byexample installed first
$ hash byexample                                    # byexample: +fail-fast

$ alias byexample=byexample\ --pretty\ none

--
-->

# Conditional Execution

``byexample`` allows the *conditional execution* of an example.

Consider the following real situation:

``byexample`` supports the execution of shell commands using different
shells: ``dash``, ``ksh`` and ``bash``.

To prove this I should write three examples using each one a different
shell.

But what happen if the environment where ``byexample`` is running does not
have one of the shells?

Failing is not fun, forcing to the user to have installed all the shells
just to run the documentation/test is not fun either.

For this ``byexample`` allows to execute an example only if
a condition matches.

First, we test if a given shell exists and we
[capture](/{{ site.uprefix }}/basic/capture-and-paste.md) the output:

```shell
$ hash ksh 2>/dev/null && echo "installed"
<ksh-installed>
```

The ``<ksh-installed>`` tag will contain the *non-empty string* ``installed``
if the ``ksh`` shell is installed in the system or it will be *empty* if not.

Then we can write the conditional example:

```shell
$ byexample -l shell -o '+shell=ksh' test/ds/shell-example  # byexample: +if=ksh-installed
<...>
[PASS] Pass: 14 Fail: 0 Skip: 0
```

The ``+if`` option receives the name of a tag: if this capture tag is empty, the
example is [skipped](/{{ site.uprefix }}/basic/skip-and-pass.md),
it is executed as usual otherwise.

The ``+on`` is an alias of ``+if``; ``+unless`` works the same but
it negates the condition.

```shell
$ echo non-empty-string
<good>

$ echo executed         # byexample: +if=good
executed

$ echo executed         # byexample: +on=good
executed

$ echo not-executed     # byexample: +unless=good
this-will-never-run
```

> *New* in ``byexample 8.1.0``. This feature is marked as ``experimental``.
