# Django Integration

Starting from `byexample` 9.0.1, we have integration with
[Django](https://www.djangoproject.com/).

When you are developing an *app* in Django it is common
to explore it using a Python shell with all the settings
needed by Django already loaded.

You probably do:

```shell
$ python manage.py shell            # byexample: +skip
```

To run `byexample` inside the same environment having all
the settings preloaded you just need a *custom*
[shebang](/{{ site.uprefix }}/advanced/shebang)

```shell
$ byexample -l python -x-shebang 'python:%p %a manage.py shell -i python' <your files> # byexample: +skip
```

That's too much to type!

Remember that you can save part of the command line in a file:

```shell
$ cat - > test/ds/django.conf <<EOF
> -x-shebang=python:%p %a manage.py shell -i python
> EOF

$ byexample -l python @test/ds/django.conf <your files>       # byexample: +skip
```

## How it works?

`-x-shebang 'python:%p %a manage.py shell -i python'` tells `byexample` to
use `%p %a manage.py shell -i python` as the interpreter to execute
the examples written in Python.

`%p %a manage.py shell -i python` will run something similar
to `python manage.py shell` except that some extra flags are needed
to customize the interpreter (hidden behind the magic `%a`).

Check [shebang](/{{ site.uprefix }}/advanced/shebang) for more details.

Other difference is that `manage.py` will use the more human friendly
`ipython` interpreter.

Currently `byexample` has no support for it
([pull requests](https://github.com/byexamples/byexample/tree/master/CONTRIBUTING.md) are welcome!) so
the extra flag `-i python` tells `manage.py` to use the classic
`python` interpreter.

<!--
$ rm -f test/ds/django.conf     # byexample: +pass -skip
-->
