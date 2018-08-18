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

## Running in background

``byexample`` executes each example in sequence, one after the other, moving to
the next one only when the previous finished.

That means that you need to relay in the shell's job control to put some
process to work in background.

Moreover you need to make sure that the process doesn't write anything to
the console, otherwise its output will be mixed with the output of the
next examples.

It is easy to this using a redirection:

```shell
$ sleep 1 >/dev/null 2>&1 &
<...>

```

Notice how the ``&`` operator tells the shell to put the process in the
background and the ``>/dev/null 2>&1`` discards both standard output and
error streams.

Then you can get the process id of the process running in background and
its job id to control it later.

```shell
$ echo "$!"
<pid>

$ jobs -l                           # byexample: +paste
[1] + <pid> Running<...>

```

Now there is a catch. Some shells like ``Bash`` output a message
immediately after starting the process and at the end of it.

The former is easier to capture but the later may happen asynchronously
unless you can control, and probably kill the background process, and wait
for it to finish.

Here is an example (the ``%%`` is replaced by the job id by the shell):

```shell
$ kill %% ; wait                    # byexample: +timeout=4
[1] + Terminated<...>

```

### Subshells

If waiting for a process is not an option, you can start the process
in background *inside* of a subshell:

```shell
$ ( sleep 1 & ) >/dev/null 2>&1

```

The ``&`` operator tells the shell to put the process in the background
*and* because we grouped it in a subshell (using the parenthesis), any
job-control message will be suppressed.

The downside of this is that we cannot access to neither the process id
nor the job id.

Therefore the job list will be empty:

```shell
$ jobs -l

```

### Disabling the job monitor

An alternative solution is disabling the monitoring that the shell does.

This basically suppress any message about the end of a process that was
running in background without loosing its process id or job id.

```shell
$ set +m
$ sleep 1 >/dev/null 2>&1 &
<...>

$ echo "$!"
<pid>

$ jobs -l                           # byexample: +paste
[1] + <pid> Running<...>

```

To prove this we can wait enough and see that no asynchronous message is print.

```shell
$ sleep 2                           # byexample: +timeout=4
$ echo "foreground"
foreground

```

You can re-enable it later

```shell
$ set -m                            # byexample: +pass

```

The downside of this solution is that disabling the monitoring also prevent us
to send ``^Z`` and ``^Y`` signals from an interactive session among
other side effects.

See the documentation of your shell.

The following ``stackoverflow`` thread explains all of this in a very concise
manner:
https://stackoverflow.com/questions/11097761/is-there-a-way-to-make-bash-job-control-quiet/11111042#11111042


## Using other shells (long story)

**Warning:** this documentation is about *internal details* that may
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

