<!--
Check that we have byexample installed first
$ hash byexample                                    # byexample: +fail-fast

$ alias byexample=byexample\ --pretty\ none

--
-->

# Showing the differences

``byexample`` will show the differences between the result that
you are expecting and the result you actually got.

Image that you have a file with the following fragment of the GPL
license:

```
$ cat test/ds/lic.doc
To protect your rights, we need to prevent no-one from denying you
these rights or asking you to surrender the rights.  Therefore, you don't have
certain responsibilities if you distribute copies of the software, or if
you modify it: responsibilities to respect the freedom of others.
```

Now let's image that you also have a document/test about GPL license
that checks that file:

```
$ cat test/ds/about-lic.doc                        # byexample: +rm=~
This example is to show you something about GPL
    ~$ cat test/ds/lic.doc
    To protect your rights, we need to prevent others from denying you
    these rights or asking you to surrender the rights.  Therefore, you have
    certain responsibilities if you distribute copies of the software, or if
    you modify it: responsibilities to respect the freedom of others.
```

We can corroborate that the test passes or not running ``byexample``
(I deliberately added some typos):

```
$ byexample -l shell test/ds/about-lic.doc
<...>
Expected:
To protect your rights, we need to prevent others from denying you
these rights or asking you to surrender the rights.  Therefore, you have
certain responsibilities if you distribute copies of the software, or if
you modify it: responsibilities to respect the freedom of others.
Got:
To protect your rights, we need to prevent no-one from denying you
these rights or asking you to surrender the rights.  Therefore, you don't have
certain responsibilities if you distribute copies of the software, or if
you modify it: responsibilities to respect the freedom of others.
<...>
```

Do you see where are the typos/errors? Hard isn't?

By default ``byexample`` shows the two strings, the *expected* that you
wrote in the example and the *got* from the execution.

For small strings is enough to spot the differences but for larger blobs
like this one is a little harder.

## Change the diff algorithm

For this reason ``byexample`` allows you to change the diff algorithm
with ``--diff``:

```
$ byexample -l shell --diff ndiff test/ds/about-lic.doc   # byexample: +rm= 
<...>
Differences:
- To protect your rights, we need to prevent others from denying you
?                                             ^^ --
 
+ To protect your rights, we need to prevent no-one from denying you
?                                            + ^^^
 
- these rights or asking you to surrender the rights.  Therefore, you have
+ these rights or asking you to surrender the rights.  Therefore, you don't have
?                                                                    ++++++
 
  certain responsibilities if you distribute copies of the software, or if
  you modify it: responsibilities to respect the freedom of others.
<...>
```

Now it is easier: someone replaced 'others' by 'no-one' and put a 'don't' to
negate some sentence.

``ndiff`` is better to spot this kind little typos.

## Guessing the tags

Your example may contain
[tags](/{{ site.uprefix }}/basic/capture-and-paste) like ``<...>`` or ``<foo>``.

Those are used to ignore long uninteresting strings or to capture specific
ones.

So let's change the example adding some tags and see how the
differences are shown:

```
$ cat test/ds/about-lic-with-tags.doc              # byexample: +rm=~
This example is to show you something about GPL
    ~$ cat test/ds/lic.doc
    To protect <protect>, we need to prevent others from <prevent1>
    or <prevent2>.  Therefore, you have
    certain responsibilities if you distribute copies of the software, or if
    you modify it: <responsibilities>.
```

If we run the example again:

```
$ byexample -l shell test/ds/about-lic-with-tags.doc
<...>
Expected:
To protect your rights, we need to prevent others from <prevent1>
or <prevent2>.  Therefore, you have
certain responsibilities if you distribute copies of the software, or if
you modify it: responsibilities to respect the freedom of others.
Got:
To protect your rights, we need to prevent no-one from denying you
these rights or asking you to surrender the rights.  Therefore, you don't have
certain responsibilities if you distribute copies of the software, or if
you modify it: responsibilities to respect the freedom of others.
<...>
Tags replaced by the captured output:
    protect: your rights                responsibilities: responsi ... f others
(You can disable this with '--no-enhance-diff')
<...>
```

The test keeps failing as expected: we didn't fix the typos in the ``lic.doc``.

But what *it is interesting is how* ``byexample`` show us the differences.

Read carefully the ``Expected`` string, notice how the tags ``<prevent1>``
and ``<prevent2>`` are there *exactly* as we defined in the test.

Nothing interesting so far but the ``<protect>`` and ``<responsibilities>``
where replaced by the correct text.

``byexample`` *captured* the fragments ``"your rights"`` and
``"responsibilities to respect the freedom of others"``
and *replaced* the tags by the captured text.

These *guesses* makes the differences shorter and more easy to spot:

```
$ byexample -l shell --diff ndiff test/ds/about-lic-with-tags.doc   # byexample: +rm= 
<...>
Differences:
- To protect your rights, we need to prevent others from <prevent1>
?                                             ^^ --      ^^^^^  ^^^
 
+ To protect your rights, we need to prevent no-one from denying you
?                                            + ^^^       ^  ^^^^^^^^
 
- or <prevent2>.  Therefore, you have
+ these rights or asking you to surrender the rights.  Therefore, you don't have
  certain responsibilities if you distribute copies of the software, or if
  you modify it: responsibilities to respect the freedom of others.
<...>
Tags replaced by the captured output:
    protect: your rights                responsibilities: responsi ... f others
(You can disable this with '--no-enhance-diff')
<...>
```

``byexample`` sees that there is enough text surrounding the tags ``<protect>``
and ``<responsibilities>`` therefore it has confidence that the captured string
are correct and can be used to update the diff.

Keep in mind that the test is failing therefore, the captured strings
may not be correct.

You can disable this with the ``--no-enhance-diff`` from the command line.
You will see a much harder to interpreter diff with more errors:

```shell
$ byexample -l shell --diff ndiff --no-enhance-diff test/ds/about-lic-with-tags.doc   # byexample: +rm= 
<...>
Differences:
- To protect <protect>, we need to prevent others from <prevent1>
- or <prevent2>.  Therefore, you have
+ To protect your rights, we need to prevent no-one from denying you
+ these rights or asking you to surrender the rights.  Therefore, you don't have
  certain responsibilities if you distribute copies of the software, or if
- you modify it: <responsibilities>.
+ you modify it: responsibilities to respect the freedom of others.
<...>
```

> *Advanced tweak:* why ``<protect>`` was replaced but not ``<prevent1>``?
> This is because the tag ``<prevent1>`` was too near of a mismatch and
> ``byexample`` had not enough confidence to *guess* what text should be
> captured by the ``<prevent1>`` tag.
>
> If the resulting diff is still too hard to read, you can *tweak* the minimum
> distance between a tag and the first mismatch with ``-x-min-rcount <n>``:
> shorter values will make ``byexample`` to guess more aggressively
> at the expense of some false positives.

<!--
$ byexample -xh | grep -q 'x-min-rcount <n>' ; echo $?
0
-->

## Diff algorithms

In addition to the default diff algorithm (``none``) and
the ``ndiff`` algorithm, ``byexample`` implements two more.

```
$ byexample -h                      # byexample: +norm-ws
usage: <byexample> [-d {none,unified,ndiff,context,tool}] <...>
```

The ``unified`` diff algorithm:

```
$ byexample -l shell --diff unified test/ds/about-lic-with-tags.doc
<...>
Differences:
@@ -1,4 +1,4 @@
-To protect your rights, we need to prevent others from <prevent1>
-or <prevent2>.  Therefore, you have
+To protect your rights, we need to prevent no-one from denying you
+these rights or asking you to surrender the rights.  Therefore, you don't have
 certain responsibilities if you distribute copies of the software, or if
 you modify it: responsibilities to respect the freedom of others.
<...>
Tags replaced by the captured output:
    protect: your rights                responsibilities: responsi ... f others
(You can disable this with '--no-enhance-diff')
<...>
```

And the ``context`` diff algorithm:

```
$ byexample -l shell --diff context test/ds/about-lic-with-tags.doc
<...>
Differences:
*** 1,4 ****
! To protect your rights, we need to prevent others from <prevent1>
! or <prevent2>.  Therefore, you have
  certain responsibilities if you distribute copies of the software, or if
  you modify it: responsibilities to respect the freedom of others.
--- 1,4 ----
! To protect your rights, we need to prevent no-one from denying you
! these rights or asking you to surrender the rights.  Therefore, you don't have
  certain responsibilities if you distribute copies of the software, or if
  you modify it: responsibilities to respect the freedom of others.
<...>
Tags replaced by the captured output:
    protect: your rights                responsibilities: responsi ... f others
(You can disable this with '--no-enhance-diff')
<...>
```

### External diff program

If ``--diff tool`` is selected, ``byexample`` will delegate the diff creation
to an external program set with ``--difftool <cmd>``.

Use this to call your favorite diff program like ``diff``, ``meld``,
``git diff`` and ``vimdiff``.

```shell
$ byexample -l shell --diff tool --difftool 'diff %e %g' test/ds/about-lic-with-tags.doc
<...>
External diff tool
1,2c1,2
< To protect your rights, we need to prevent others from <prevent1>
< or <prevent2>.  Therefore, you have
---
> To protect your rights, we need to prevent no-one from denying you
> these rights or asking you to surrender the rights.  Therefore, you don't have
Return code: 1
<...>
```

The ``%e`` and ``%g`` tokens are replaced with the file names with
the content of the expected and the got outputs.
