<!--
$ hash ksh 2>/dev/null && echo "installed"
<ksh-installed>

$ hash dash 2>/dev/null && echo "installed"
<dash-installed>


$ hash byexample                                    # byexample: +fail-fast
$ alias byexample=byexample\ --pretty\ none

--
-->

# Shell

``byexample`` can execute shell commands using by default ``bash`` configured
to be POSIX-conformant
but other shells are supported like ``dash`` and ``ksh``.

Run the `Shell` examples calling `byexample` as:

```shell
$ byexample -l shell your-file-here                   # byexample: +skip
$ byexample -l shell -o '+shell=dash' your-file-here  # byexample: +skip
```

> **Stability**: ``provisional`` - low impact non backward compatibility
> changes may occur between versions; but in general a change like that
> will happen only between major versions.

### Versions tested

We tested `byexample` with the following versions of the language
and the underlying runner or interpreter:

<!-- matrix CI begin -->

| Language   | Runner/Interpreter   |
|------------|----------------------|
| latest     | 5.0.17               |

<!-- matrix CI end -->

## POSIX-conformant

`byexample` configures ``bash`` to run in POSIX-conformant by default.

If you execute an shell example and you get a syntax error, you may be
using a non-POSIX syntax.

You can disable the POSIX-conformant from *within* `bash` with `set
+o posix`:

```shell
$ echo $POSIXLY_CORRECT  # this Bash's variable says yes if we are in POSIX
y

$ set +o posix
$ echo $POSIXLY_CORRECT  # we are not longer in POSIX mode, happy hacking

$ set -o posix
$ echo $POSIXLY_CORRECT  # back to the default of byexample
y
```

<!--
$ set -o posix           # byexample: +pass -skip
-->

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

It is easy to do this using a redirection:

```shell
$ sleep 2 >/dev/null 2>&1 &
[<job-id>] <pid>
```

Notice how the ``&`` operator tells the shell to put the process in the
background and the ``>/dev/null 2>&1`` discards both standard output and
error streams.

> Depending of the underlying shell when you send a process to the background
> the job control may print the job id and process id linked to that process.
>
> ``bash`` and ``ksh`` do this always but others like ``dash`` does not.

You can get the process id of the process running in background and
its job id to control it later.

```shell
$ echo "$!"                         # byexample: +paste
<pid>

$ jobs -l                           # byexample: +paste +norm-ws
[<job-id>]+ <pid> Running <...>
```

When a process finishes (or dies), the shell will print
a message.

It may happen *asynchronously*
unless you control, and probably kill the background process, and *wait*
for it to finish.

Here is an example (the ``%%`` is replaced by the job id by the shell):

```shell
$ kill %% ; wait                    # byexample: +timeout=4 +norm-ws +paste
[<job-id>]+ Terminated <...>
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
[<job-id>] <pid>

$ echo "$!"                         # byexample: +paste
<pid>

$ jobs -l                           # byexample: +paste +norm-ws
[<job-id>]+ <pid> Running <...>
```

To prove this we can wait enough and see that no asynchronous message is print.

```shell
$ sleep 2                           # byexample: +timeout=4
$ echo "foreground"
foreground
```

You can re-enable it later

```shell
$ set -m                            # byexample: +pass -skip
```

The downside of this solution is that disabling the monitoring also prevent us
to send ``^Z`` and ``^Y`` signals from an interactive session among
other side effects.

See the documentation of your shell.

> The following ``stackoverflow`` thread explains all of this in a very concise
> manner:
> https://stackoverflow.com/questions/11097761/is-there-a-way-to-make-bash-job-control-quiet/11111042#11111042

### Killing any background process

This has nothing to do with ``byexample`` but I found quite useful this trick.

To kill any running background process you can write:

```shell
$ kill -9 $(jobs -p) && wait        # byexample: -skip +pass
```

The ``-skip`` will [make sure](/{{ site.uprefix }}/basic/setup-and-tear-down)
that this example gets executed while the ``+pass``
will [ignore any output](/{{ site.uprefix }}/basic/skip-and-pass)
so it will work even if there is no process to kill.

## Stopping a process on inactivity or silence

Sometimes is useful to run a long-running process in foreground
and after some period of inactivity or silence, stop it and get
back the control of the shell.

For example, imagine that we want to read the new entries of a log
file as soon as they are saved in the log file.

```shell
$ echo "some log line" > w/msg.log
```

We could use ``tail -f`` for this. But if we do that, ``tail`` will never end,
*blocking the whole execution*.

In these cases we can use the ``+stop-on-silence`` option.
After some period of inactivity of the process, ``byexample`` will stop it
returning back the control of the shell.

```shell
$ tail -f w/msg.log             # byexample: +stop-on-silence
some log line
```

The process will be *stopped*, if you want that the process keeps running
in background execute ``bg``.

Or you can resume it in foreground with ``fg``, this enable us
to keep reading the new entries in the log.

```shell
$ echo "another log line" >> w/msg.log

$ fg                            # byexample: +stop-on-silence
tail -f w/msg.log
another log line
```

By default, ``+stop-on-silence`` waits for ``0.2`` seconds of inactivity.
If your process is a little slower and sends data to the output
less frequently you can increase the wait time:

```shell
$ (sleep 0.4 ; echo "a slow line" >> w/msg.log) &
[2] <pid>

$ fg %1                           # byexample: +stop-on-silence=0.5
tail -f w/msg.log
a slow line

$ jobs
[1]<...>Stopped<...>
```

> **Note:** ``+stop-on-silence`` requires the job control and monitoring to be
> enabled (``set -m``). This should be the default in your shell.

> **Changed** in ``byexample 8.0.0``: before the ``+stop-on-silence`` had the
> same behaviour than ``+stop-on-timeout`` stopping the process always on
> timeout. But in ``8.0.0`` this option was fixed and the old behaviour can
> be achieved using ``+stop-on-timeout``.

<!--
$ kill -9 $(jobs -p) && wait        # byexample: -skip +pass
-->

### Stopping on timeout

``+stop-on-silence`` will stop a process if this one times out, which
it is basically another kind of inactivity.

But sometimes you have a process that it is continually sending data
and you want to stop it after some period of time.

``+stop-on-silence`` will work, but it is not the correct tool for this job.

Instead, ``+stop-on-timeout`` is the correct one: instead of checking
periodically if there is activity or not, ``byexample`` will wait for the process
to timeout and it will stop it later.

> *New* in ``byexample 8.0.0``.

> **Note:** ``+stop-on-timeout`` requires the job control and monitoring to be
> enabled (``set -m``). This should be the default in your shell.

### Stop signal

`+stop-on-timeout` and `+stop-on-silence` *stop* the running process but
what does it mean?

By default `byexample` sends a `suspend` signal (`SIGTSTP` or `^Z` in
Linux parlance) which stops the process and sends it to background.

The signal used can be changed with `+stop-signal`.

If you want to *interrupt* the process and very likely finish it, send
an `interrupt` signal (`SIGINT` or `^C`):

```shell
$ sleep 300      # byexample: +stop-on-silence +stop-signal=interrupt
```

If the process is waiting for input perhaps *closing* the standard
input is more adequate than interrupting the process.

For that send an `eof` signal (`^D`):

```shell
$ cat -      # byexample: +stop-on-silence +stop-signal=eof
```

> *New* in ``byexample 10.1.0``.

Signals like `SIGTERM` and `SIGKILL` cannot be used from
`+stop-signal`; the closest thing is the `quit` signal (`SIGQUIT` or `^\`):

```shell
$ cat -      # byexample: +stop-on-silence +stop-signal=quit
```

> *New* in ``byexample 10.5.2``.

### Arbitrary signals on stop

If you want to *kill* a process with `SIGKILL` or `SIGTERM`
you will have to stop the process first with a `suspend` signal (the
default for `+stop-signal`), capture the process' id or job's id and
kill it calling `kill`:

```shell
$ cat -      # byexample: +stop-on-silence

$ # The following sends a SIGTERM. Replace the -15 by -9 to send
$ # a SIGKILL. See signal(7).
$ kill -15 %%
<...>
```

In fact, you can use this trick to send any signal like `SIGUSR1`.
In some cases you will have to bring the process to foreground (with
`fg` to give it a chance to receive the signal).

```shell
$ fg         # byexample: +pass
```

## Using other shells

``byexample`` supports ``bash``, ``dash`` and ``ksh`` and the shell
by default is set to ``bash`` in POSIX-conformant mode.

> *Changed* in ``byexample 8.1.0``: before the default shell was ``sh``.
> However different Linux distros have different shells behind the name
> of ``sh``: in Debian it is ``dash`` while in Red Hat it is ``bash``.
> And this changed over the time: Ubuntu had ``bash`` but in Ubuntu 6.10
> it changed the shell to ``dash``.
>
> To have a stable shell, since ``byexample 8.1.0`` it is explicitly set
> to ``bash``.

You can change the default shell from the command line with the
``+shell`` option.

```shell
$ byexample -l shell -o '+shell=bash' test/ds/shell-example  # byexample: +timeout=8
<...>
[PASS] Pass: 14 Fail: 0 Skip: 0

$ byexample -l shell -o '+shell=dash' test/ds/shell-example  # byexample: +if=dash-installed +timeout=8
<...>
[PASS] Pass: 14 Fail: 0 Skip: 0

$ byexample -l shell -o '+shell=ksh' test/ds/shell-example   # byexample: +if=ksh-installed +timeout=8
<...>
[PASS] Pass: 14 Fail: 0 Skip: 0
```

The option can only be set from the command line and it will affect
all the shell examples (you cannot change the shell only for a single
example)

> *New* in ``byexample 8.1.0``.
>
> For backward compatibility with ``byexample 8.0.0`` and earlier versions,
> you can use ``+shell=sh``; however, we encourage to you to set a
> more specific shell.

If another shell is needed, ``byexample`` allows
you to use ``-x-shebang`` to control
[how to spawn a runner](/{{ site.uprefix }}/advanced/shebang), in this case,
a shell.

You could run `ssh` to have a remote shell for example.

Or you could run ``bash`` without the constraint to be POSIX-conformant
by default (but see `set +o posix` as mentioned above before trying to do this):

```shell
$ byexample -l shell -x-shebang 'shell:%e bash --norc --noprofile --noediting' test/ds/shell-example
<...>
[PASS] Pass: 14 Fail: 0 Skip: 0
```

<!--
$ kill %% ; fg ; wait    # byexample: +pass -skip
-->

## Shell specific options

```
$ byexample -l shell --show-options       # byexample: +norm-ws
<...>
shell's specific options
------------------------
<...>:
  +stop-on-timeout      stop the process if it timeout.
  +stop-on-silence [secs]
                        stop the process if no output is read in the last
                        <secs> seconds (0.2 secs by default).
  +stop-signal {suspend,eof,interrupt,quit}
                        signal to send when stop-on-timeout/stop-on-silence is
                        used (suspend ^Z by default).
  +shell {bash,dash,ksh,sh}
                        shell to use with default settings ('bash' by
                        default). For full control use -x-shebang)
<...>
```
