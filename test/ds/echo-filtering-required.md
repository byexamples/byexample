<!--
$ stty echo
$ uname | grep -i darwin
<on-macos>

-->

`stty echo` will turn the echo on so the example requires an active echo
filtering

```shell
$ stty echo

$ echo "normal output"
normal output
```

But for Python we don't require the filtering so we must not activate it

```python
>>> print(1)    # byexample: +unless=on-macos
1
```

```shell
$ stty echo

$ echo "normal output"  # byexample: +force-echo-filtering
normal output
```
