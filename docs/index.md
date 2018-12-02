<!--
Check that we have byexample installed first
$ hash byexample                                    # byexample: +fail-fast
-->

<div class="demo">
<img src="https://raw.githubusercontent.com/byexamples/byexample/master/media/demo.gif" alt="Sorry, it seems that you cannot see the demo. Another excuse to install byexample and test it by yourself ;)" width="90%" height="90%">
</div>

## byexample is...

...a literate programming engine where you mix
ordinary text and snippets of code in the same file and then you
execute them as regression tests.

You can always be sure that the examples are correct and your documentation
is up to date!

It lets you to execute the examples written in ``Python``, ``Ruby`` or whatever
in your documentation and validate them.

Currently ``byexample`` supports the following languages:

<div class="logos">
  <div class="row">
    <div class="col-lg-4">
      <img src="https://raw.githubusercontent.com/byexamples/byexample/master/media/logos/python_logo.png" alt="Python Logo" width="64" height="64" />
      <h3><a href="/{{ site.uprefix }}/languages/python">Python</a></h3>
    </div>
    <div class="col-lg-4">
      <img src="https://raw.githubusercontent.com/byexamples/byexample/master/media/logos/ruby_logo.png" alt="Ruby Logo" width="64" height="64" />
      <h3><a href="/{{ site.uprefix }}/languages/ruby">Ruby</a></h3>
    </div>
    <div class="col-lg-4">
      <img src="https://raw.githubusercontent.com/byexamples/byexample/master/media/logos/bash_logo.png" alt="Bash Logo" width="64" height="64" />
      <h3><a href="/{{ site.uprefix }}/languages/shell">Shell</a></h3>
    </div>
  </div>
  <div class="row">
    <div class="col-lg-4">
      <img src="https://raw.githubusercontent.com/byexamples/byexample/master/media/logos/gdb_logo.png" alt="GDB Logo" width="64" height="64" />
      <h3><a href="/{{ site.uprefix }}/languages/gdb">GDB</a></h3>
    </div>
    <div class="col-lg-4">
      <img src="https://raw.githubusercontent.com/byexamples/byexample/master/media/logos/javascript_logo.png" alt="Javascript Logo" width="64" height="64" />
      <h3><a href="/{{ site.uprefix }}/languages/javascript">Javascript</a></h3>
    </div>
    <div class="col-lg-4">
      <img src="https://raw.githubusercontent.com/byexamples/byexample/master/media/logos/cpp_logo.png" alt="C++ Logo" width="64" height="64" />
      <h3><a href="/{{ site.uprefix }}/languages/cpp">C/C++</a></h3>
    </div>
  </div>
</div>

## How do I get started?

First, you need to install it:

```
$ pip install byexample                # install it # byexample: +skip
```

Or if you prefer, you can install it inside a
[virtual env](https://docs.python.org/3/library/venv.html).

If you don't have ``pip`` or ``python`` installed, check the
[download page](https://www.python.org/downloads/).

That's it! Now, write a tutorial, a blog or a how-to and put some examples
in between (like this ``README.md`` that you are reading);
All the snippets and examples will be collected, executed and checked.

```
$ byexample -l python,ruby,shell README.md      # run it    # byexample: +skip
[PASS] Pass: <...> Fail: <...> Skip: <...>
```

## License

This project is licensed under GPLv3

```shell
$ head -n 2 LICENSE     # byexample: +norm-ws
          GNU GENERAL PUBLIC LICENSE
           Version 3, 29 June 2007
```

See [LICENSE](https://github.com/byexamples/byexample/tree/master/LICENSE.md) for more details.

## Versioning

We use [semantic version](https://semver.org/) for the core or engine.

For each module we have the following categorization:

 - ``experimental``: non backward compatibility changes are possible or even
removal between versions (even patch versions).
 - ``unstable``: low impact non backward compatibility changes may occur
between versions; but in general a change like that will happen only between
major versions.
 - ``stable``: non backward compatibility changes, if happen, they will
between major versions.
 - ``deprecated``: it will disappear in a future version.

See the latest [releases and tags](https://github.com/byexamples/byexample/tags)

Current version:

```shell
$ byexample -V
byexample 7.4.3 (Python <...>) - GNU GPLv3
<...>
Copyright (C) Di Paola Martin - https://github.com/byexamples/byexample
<...>
```

