# Introduction

First off, thanks for using and considering contributing to ``byexample``.

``byexample`` is an open source project that aims other projects to have
high quality documentation and tests.

It is for the community and we love to receive contributions from our
community.

This guideline will help you to go through the process of contributing
from forking and reviewing the code to doing your first pull request.

## It is not just contribute code

Supporting a new language or extending one already there is always welcome.
Check this [how to](docs/how_to_support_new_finders_and_languages.md).

But it is not just contribute code.

Is ``byexample`` producing a hard-to-debug diff or did you found a bug?
[Creating an issue](https://github.com/byexamples/byexample/issues) in
github is as important as writing new code.

Do you like to write? Write a blog or post in the social medias (I hope for the good :)

Do you want to contribute but you are not sure where to start?
Pick an issue from [here](https://github.com/byexamples/byexample/issues);
the issues with the label ``good first issue`` is what you are looking for.


## Modules: the preferred way

We love to extend ``byexample`` adding new ``modules``.

Instead of editing the internal ``Parser`` class, extend it through a
parser that can be loaded on the fly using ``modules`` (read this
[how to](docs/how_to_support_new_finders_and_languages.md) if you
didn't)

Instead of editing the internal ``Runner`` class, try to a ``Concern``.

If you find that a feature would be cool and the current ``Concern``'s interface
(a set of hooks) is not enough, open an issue and propose an extension
for ``Concern``.

In this way we your contributions can be merged and shipped in the next
release without worrying to be incompatible with previous versions.

But if you have the feeling that something cool is missing, don't be afraid
and talk about it.

# Warming up

Got to ``github`` and make a [fork](https://guides.github.com/activities/forking/).

Then, you clone it in your computer:

```shell
$ git clone https://github.com/<your github username>/byexample.git     # byexample: +skip

```

## Regression tests

Now, run a small regression tests to make sure you have a good baseline.

```shell
$ make lib-test     # byexample: +skip
<...>
[PASS] <...>

```

You can run all the examples in the documentation (this will require ``Ruby``
installed for the examples written in ``Ruby``)

```shell
$ make docs-test     # byexample: +skip
<...>
[PASS] <...>

```

The full set of test can be executed with a single command but you may need to
have installed ``gcc``, ``gdb`` and more. You may want to tweak the Makefile
configuration to disable some languages)

```shell
$ make test     # byexample: +skip
<...>
[PASS] <...>

```

### Run a single test case

Use ``byexample`` of course!

To run the examples of in a doc or source file, just point to it.

For example, if you want are fixing a bug the Parser and you want to check
that you are not introducing any issue, run its tests in this way:

```shell
$ byexample -l python byexample/parser.py     # byexample: +skip

```

# How to submit a contribution

If your contribution is quite small, open a pull request directly.

If you think that you need some brainstorming first before working on it
or you may have some question, open a ticket first. Leave the pull request
for later.

Try to give as much as context as you can.

If it is a bug, explain what you did and what should be the correct answer.
If it is a new idea, explain why do you think it would be cool? Extra points
if you provide examples!

No one knows everything so it is ok to ask but expect some delay in the answer,
sometimes some questions are not as easier as you think!

Be patient and respectful in both sides: if you are doing the question or you
are answering.

And don't forget, before asking, try to see if you can figure out by your own.
It is ok not to know things, but people will appreciate you efforts.

