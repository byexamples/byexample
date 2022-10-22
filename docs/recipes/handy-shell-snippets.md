<!--
$ uname | grep -i darwin
<on-macos>
-->

# Handy Shell Snippets

### Wait for a tcp port

Wait for a tcp port is open and accepting connections.
You may want to combine this with a
[timeout](/{{ site.uprefix }}/basic/timeout) and with a
[fail fast](/{{ site.uprefix }}/basic/setup-and-tear-down).

```shell
$ wait_port() {
>     while ! nc -z 127.0.0.1 $1 >/dev/null 2>&1; do sleep 0.5; done
> }

$ wait_port 80  # byexample: +fail-fast +timeout=5              +skip
```

> Ignore the ``+skip`` option.

If instead you want to pick a free port do something like this:

```shell
$ free_port() {
>   for port in {1500..65000}; do ss -tln | grep -q ":$port " || echo "Port $port" && break; done
> }

$ free_port     # byexample: +fail-fast +unless=on-macos
Port <port>
```

Like before you may want to combine this with a
[fail fast](/{{ site.uprefix }}/basic/setup-and-tear-down) option and you
can use the
[capture and paste](/{{ site.uprefix }}/basic/capture-and-paste) functionality
to save and use the port later without parsing the output yourself.

> Note: `ss` is an "utility to investigate sockets". You may use
> the older `netstat -tan` of the same purpose.

### Lock a file

Use ``flock`` to synchronize your programs and avoid a race condition.

Combine this with a
[fail fast](/{{ site.uprefix }}/basic/setup-and-tear-down) to fail quickly
if the lock cannot be obtained and with a
[skip](/{{ site.uprefix }}/basic/setup-and-tear-down) to make your that
sure unlock the file at the end:

```shell
$ # try to get the lock, fail fast if we cannot
$ exec {fd}>>test/ds/f && flock -n $fd || echo "Lock failed"  # byexample: +fail-fast +unless=on-macos

$ # your code here

$ # release the lock, do not skip these steps to avoid deadlocks
$ flock -u $lockfd              # byexample: -skip +pass
$ exec {lockfd}>&-              # byexample: -skip +pass
$ rm -f test/ds/f               # byexample: -skip +pass
```

### Keep tracking a log

You have a program that logs something of your interest *asynchronously*.

Use ``tail -f`` (or ``tailf``) to keep track of
the log file *in the background*, only then run your program and
lastly bring the ``tail`` back to the foreground to do the check.

<!--
# create and wipe the log
$ > test/ds/some.log
-->

Here we do the first part using
[+stop-on-silence](/{{ site.uprefix }}/languages/shell.md) to send it
to the background:

```shell
$ tail -f test/ds/some.log      # byexample: +stop-on-silence
```

Then we run the asynchronous command (here you put *your* command)

```shell
$ (sleep 0.5 ; echo "very important message!" >> test/ds/some.log) &
[<job-id>] <pid>
```

And finally, we bring back the ``tail`` and check. We extend the
[timeout](/{{ site.uprefix }}/basic/timeout)
to give the ``echo`` an opportunity to complete and log.

```shell
$ fg %1                         # byexample: +stop-on-timeout +timeout=1
tail -f test/ds/some.log
very important message!
```

> Did you notice the difference between ``+stop-on-silence`` and
> ``+stop-on-timeout``? The former sends the program to the background
> if ``byexample`` does not detect any output from it after a small
> fraction of time (aka silence). The latter does the same but when
> the timeout is over.

Because ``fg %1`` will never end we *need* to
send it the background again and not fail with a timeout (that's why
we use `+stop-on-timeout`).

To finish it, we can kill it like any other process. You typically
do not want to [skip](/{{ site.uprefix }}/basic/setup-and-tear-down) this.

```shell
$ kill %% ; fg ; wait       # byexample: -skip
tail -f test/ds/some.log
Terminated
```

### No POSIX-conformant Bash

By default, `byexample` uses `bash` in POSIX-conformant mode.

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

