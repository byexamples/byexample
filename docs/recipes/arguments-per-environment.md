<!--
Check that we have byexample installed first
$ hash byexample                                    # byexample: +fail-fast
$ hash j2                                           # byexample: +fail-fast

$ alias byexample=byexample\ --pretty\ none\ --dry

-->
# Dynamic options based on the environment

Imagine that you want to executes some documents/source codes but
want to skip some of them **if** you are running in, let's say, MacOS.

You could do something like this:

```shell
$ cat test/ds/for-mac.args
-l=python,shell
--skip
byexample/prof.py
docs/overview/good-practices.md
--
byexample/*.py
docs/overview/*.md

$ cat test/ds/for-linux.args
-l=python,shell
--
byexample/*.py
docs/overview/*.md

$ if [ "$(uname)" = "Darwin" ]; then
>   byexample @test/ds/for-mac.args
> else
>   byexample @test/ds/for-linux.args
> fi
```

Indeed `$(uname)` will return `"Darwin"` on MacOS and yes, `byexample`
then will be executed with the additional arguments from
`test/ds/for-mac.args`.

But if your skills with shell scripting are a little rusted, or you have
a much complicated situation that depends on a lot on the environment,
you may want to try something else.

Consider `test/ds/for-mac.args` and `test/ds/for-linux.args`, they are quite
similar and only differ but just a little.

You could use a *templating* system to generate the argument file from a
template:

```shell
$ cat test/ds/template.args
-l=python,shell
{% if osname == "Darwin" %}
    --skip
    byexample/prof.py
    docs/overview/good-practices.md
{% endif %}
--
byexample/*.py
docs/overview/*.md
```

Then:

```shell
$ osname=$(uname) j2 test/ds/template.args > test/ds/good.args
$ byexample @test/ds/good.args
```

`j2` is one of many engines based on
[Jinja2](https://jinja.palletsprojects.com/en/3.1.x/).
I used [kolypto/j2cli](https://github.com/kolypto/j2cli)
 but other implementations exist like
[mattrobenolt/jinja2-cli](https://github.com/mattrobenolt/jinja2-cli).

Of course, using a template engine is just an idea. See if it helps
you!!

<!--
$ rm -f test/ds/good.args       # byexample: +pass -skip
-->

