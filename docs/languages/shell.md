# Shell (sh, bash)

``byexample`` can execute shell commands using by default ``sh``.

## Find interactive examples

For ``Shell``, we use the simple ``$`` marker as the primary prompt
and ``>`` as the secondary prompt to found examples in a document.

```shell
$ g () {
>     c=$3
>     c=$(( $c + $1 ))
>     c=$(( $c + $2 ))
>
>     echo $c
> }

$ g 1 2 3
6

```

## Using other shells (long story)

**Warning:** this documentantion is about *internal details* that may
not be honored between releases.

There is no problem in spawning another shell even if the shell is not
``sh``

The only caveat is that the spawned shell *must* use the same prompts
that ``byexample`` uses internally.

Exporting all the prompts to the other subshell should be enough.

For example to use ``bash`` instead of ``sh``

```shell
$ export PS1
$ export PS2
$ export PS3
$ export PS4

$ echo $0
sh

$ /usr/bin/env bash --norc -i
$ echo $0
bash

$ exit
exit

```

The ``--norc`` flag is to make sure that ``bash`` will not load any ``.bashrc``
configuration script. It is quite common that on those scripts the prompts
are changed, overriding ours.

If you are sure that it is ok, you can remove the flag.

## Using other shells (short story)

``byexample`` allows you to use ``--shebang`` to control how to spawn
a runner, in this case, the shell.

See [usage](../usage.md) to see how ``--shebang`` is used.

We support currently ``sh`` and ``bash``. It will probably work with others.

Open an issue if not or even better, do a Pull Request for adding support to
other shells!

