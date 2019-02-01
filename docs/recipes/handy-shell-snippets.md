# Handy Shell Snippets

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

Check that a given tcp port is free to use. Like before you may
want to combine this with a
[fail fast](/{{ site.uprefix }}/basic/setup-and-tear-down) option.

```shell
$ nc -z 127.0.0.1 8080 && echo "Port 8080 in use. Abort."  # byexample: +fail-fast
```
