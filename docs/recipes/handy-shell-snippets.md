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
>   for port in {1500..65000}; do netstat -tan | grep -q ":$port " || echo "Port $port" && break; done
> }

$ free_port     # byexample: +fail-fast
Port <port>
```

Like before you may want to combine this with a
[fail fast](/{{ site.uprefix }}/basic/setup-and-tear-down) option and you
can use the
[capture and paste](/{{ site.uprefix }}/basic/capture-and-paste) functionality
to save and use the port later without parsing the output yourself.

### Lock a file

Use ``flock`` to synchronize your programs and avoid a race condition.

Combine this with a
[fail fast](/{{ site.uprefix }}/basic/setup-and-tear-down) to fail quickly
if the lock cannot be obtained and with a
[skip](/{{ site.uprefix }}/basic/setup-and-tear-down) to make your that
you unlock the file at the end:

```shell
$ # try to get the lock, fail fast if we cannot
$ exec {fd}>>test/ds/f && flock -n $fd || echo "Lock failed"  # byexample: +fail-fast

$ # your code here

$ # release the lock, do not skip these steps to avoid deadlocks
$ flock -u $lockfd              # byexample: -skip +pass
$ exec {lockfd}>&-              # byexample: -skip +pass
$ rm -f test/ds/f               # byexample: -skip +pass
```
