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
    <div class="col-4">
      <img src="https://raw.githubusercontent.com/byexamples/byexample/master/media/logos/python_logo.png" alt="Python Logo" width="64" height="64" />
      <h3><a href="/{{ site.uprefix }}/languages/python">Python</a></h3>
    </div>
    <div class="col-4">
      <img src="https://raw.githubusercontent.com/byexamples/byexample/master/media/logos/ruby_logo.png" alt="Ruby Logo" width="64" height="64" />
      <h3><a href="/{{ site.uprefix }}/languages/ruby">Ruby</a></h3>
    </div>
    <div class="col-4">
      <img src="https://raw.githubusercontent.com/byexamples/byexample/master/media/logos/bash_logo.png" alt="Bash Logo" width="64" height="64" />
      <h3><a href="/{{ site.uprefix }}/languages/shell">Shell</a></h3>
    </div>
  </div>
  <div class="row">
    <div class="col-4">
      <img src="https://raw.githubusercontent.com/byexamples/byexample/master/media/logos/gdb_logo.png" alt="GDB Logo" width="64" height="64" />
      <h3><a href="/{{ site.uprefix }}/languages/gdb">GDB</a></h3>
    </div>
    <div class="col-4">
      <img src="https://raw.githubusercontent.com/byexamples/byexample/master/media/logos/javascript_logo.png" alt="Javascript Logo" width="64" height="64" />
      <h3><a href="/{{ site.uprefix }}/languages/javascript">Javascript</a></h3>
    </div>
    <div class="col-4">
      <img src="https://raw.githubusercontent.com/byexamples/byexample/master/media/logos/cpp_logo.png" alt="C++ Logo" width="64" height="64" />
      <h3><a href="/{{ site.uprefix }}/languages/cpp">C/C++</a></h3>
    </div>
  </div>
    <!-- <div class="col-6"> -->
  <div class="row">
    <div class="col-6">
      <img src="https://raw.githubusercontent.com/byexamples/byexample/master/media/logos/java_logo.png" alt="Java Logo" width="64" height="72" />
      <h3><a href="/{{ site.uprefix }}/languages/java">Java</a></h3>
    </div>
    <div class="col-6">
      <img src="https://raw.githubusercontent.com/byexamples/byexample/master/media/logos/powershell_logo.png" alt="PowerShell Logo" width="70" height="70" />
      <h3><a href="/{{ site.uprefix }}/languages/powershell">PowerShell</a></h3>
    </div>
  </div>
  <div class="row">
    <div class="col-4">
      <img src="https://raw.githubusercontent.com/byexamples/byexample/master/media/logos/iasm_logo.png" alt="iasm Logo" width="90" height="64" />
      <h3><a href="/{{ site.uprefix }}/languages/iasm">iasm</a></h3>
    </div>
    <div class="col-4">
      <img src="https://raw.githubusercontent.com/byexamples/byexample/master/media/logos/go_logo.png" alt="Go Logo" width="90" height="64" />
      <h3><a href="/{{ site.uprefix }}/languages/go">Go</a></h3>
    </div>
    <div class="col-4">
      <img src="https://raw.githubusercontent.com/byexamples/byexample/master/media/logos/rust_logo.png" alt="Rust Logo" width="64" height="64" />
      <h3><a href="/{{ site.uprefix }}/languages/rust">Rust</a></h3>
    </div>
  </div>
</div>

## Usage

You [write your documentation with examples](https://byexamples.github.io/byexample/overview/where-should-I-write-the-examples)
in a Markdown or other text file.

Then, you run `byexample` from the command line selecting which
language or languages you want to run:
[Python](https://byexamples.github.io/byexample/languages/python),
[Ruby](https://byexamples.github.io/byexample/languages/ruby),
[Shell](https://byexamples.github.io/byexample/languages/shell) and
[C/C++](https://byexamples.github.io/byexample/languages/cpp) to
mention a few.

And yes, you can write examples in different languages in the same
file. [Combine them to combine their
strengths](https://byexamples.github.io/byexample/recipes/advanced-checks)
and make your life easier.

That's all. `byexample` will compare the output of the examples with the
expected ones and it will [show any
difference](https://byexamples.github.io/byexample/overview/differences).


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
in between (like this web page that you are reading);
All the snippets and examples will be collected, executed and checked.

```
$ byexample -l python,ruby,shell README.md      # run it    # byexample: +skip
[PASS] Pass: <...> Fail: <...> Skip: <...>
```

## Platforms supported

Linux is the preferable choice as it is very well tested.

Since `9.2.1` MacOS is also supported`*` for the testing is more limited
and it is expected to have little variations from Linux.

You can even run `byexample` in Windows`**` using
[Windows Subsystem for Linux](https://docs.microsoft.com/en-us/windows/wsl/install-win10)
but keep in mind that the testing is even more limited;
a native execution in Windows (outside of WSL) is currently not
supported.

<div class="logos">
  <div class="row">
    <div class="col-4">
      <img src="https://raw.githubusercontent.com/byexamples/byexample/master/media/logos/linux_logo.png" alt="Linux Logo" width="64" height="64" />
      <h3><a href="/{{ site.uprefix }}/languages/python">Linux</a></h3>
    </div>
    <div class="col-4">
      <img src="https://raw.githubusercontent.com/byexamples/byexample/master/media/logos/macos_logo.png" alt="MacOS Logo" width="64" height="64" />
      <h3><a href="/{{ site.uprefix }}/languages/ruby">MacOS*</a></h3>
    </div>
    <div class="col-4">
      <img src="https://raw.githubusercontent.com/byexamples/byexample/master/media/logos/windows_logo.png" alt="Windows Logo" width="64" height="64" />
      <h3><a href="/{{ site.uprefix }}/languages/shell">Windows**</a></h3>
    </div>
  </div>
</div>

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
 - ``provisional``: low impact non backward compatibility changes may occur
between versions; but in general a change like that will happen only between
major versions.
 - ``stable``: non backward compatibility changes, if happen, they will
between major versions.
 - ``deprecated``: it will disappear in a future version.
 - ``unsupported``: it may work but currently it is not possible to offer
*any* guarantees. [Contributions from the community are needed!](https://github.com/byexamples/byexample/tree/master/CONTRIBUTING.md)

See the latest [releases and tags](https://github.com/byexamples/byexample/tags)
and the
[changelog](https://github.com/byexamples/byexample/releases)

Current version:

```shell
$ byexample -V
byexample 10.3.0 (Python <...>) - GNU GPLv3
<...>
Copyright (C) Di Paola Martin - https://byexamples.github.io
<...>
```

