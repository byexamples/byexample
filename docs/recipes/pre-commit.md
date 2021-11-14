# Pre-Commit

[pre-commit](https://pre-commit.com/) is a framework for managing and
maintaining multi-language pre-commit (git) hooks.

Starting from `10.4.0`, `byexample` supports `pre-commit` so you can
run the tests automatically before each commit.

The proposed configuration that you need to write in
`.pre-commit-config.yaml` in your git repository is:

```yaml
repos:
-   repo: https://github.com/byexamples/byexample
    rev: 10.4.1
    hooks:
    -   id: byexample
        types_or: [markdown, python]
        args: [--no-progress-bar, --jobs=2, -l=python, -l=shell]
```

The configuration above says that `pre-commit` will run `byexample` for
all the `markdown` and `python` files that you modified before the
commit.

You can add more *types* to the list of course! `markdown` and `python`
are just an example.

The `args` are the arguments that are passed as they are to
`byexample`.

The most important ones are the language specification. In the example
above `-l=python` and `-l=shell` means that `byexample` will search and
execute Python and Shell snippets (inside the `markdown` and `python`
files).

`--no-progress-bar` disables the progress bar of `byexample`. It is not
mandatory but it makes the output of `pre-commit` a little nicer.

Any other argument can be passed, in the above example `--jobs=2` makes
`byexample` to process 2 files at the same time.

It is possible to write the arguments for `byexample` in a separated file,
let's name it `boptions`, and load it as follows:

```yaml
repos:
-   repo: https://github.com/byexamples/byexample
    rev: 10.4.1
    hooks:
    -   id: byexample
        types_or: [markdown, python]
        args: ['@boptions']
```

This is perhaps a little cleaner that writing the arguments in
`.pre-commit-config.yaml` but it is a matter of taste.


> *New* in ``byexample 10.4.0``.
