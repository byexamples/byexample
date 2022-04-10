# Running with `sudo`

In general it is a bad idea to run arbitrary programs with `sudo`,
specially programs that are for verification like `byexample`.

However there are cases that it is required.

## Running a single command with `sudo` (passwordless version)

For example you may need to run some code in a **privileged** `shell`,
like the following:

```shell
$ sudo test/ds/script-requires-root.sh                  # byexample: +skip
Checking <...>
Done.
```

That will work only if `sudo` does not ask a password.

You can achieve this making `test/ds/script-requires-root.sh`
passwordless editing you `sudoers` file with `visudo` and adding the
following line:


```
john ALL=(root) NOPASSWD: /home/john/full-path-here/test/ds/script-requires-root.sh
```

This tells `sudo` to not ask for a password (`NOPASSWD`) when the user
`john` is trying to execute the program
`/home/john/full-path-here/test/ds/script-requires-root.sh` to run it as
`root`.

## Running a single command with `sudo` (password version)

Now you *could* run `sudo` and let it to ask for a password and you
*could* type the password in from `byexample` using
[+type](/{{ site.uprefix }}/basic/input) but you need to realize that
that would mean that you are typing your password in from of all your
readers:

```shell
$ sudo test/ds/script-requires-root.sh                  # byexample: +type +skip
<...>password for john: [your-plain-text-password-here]
Checking <...>
Done.
```

A preferible approach could have the password in an environment variable
named `PASS` and *paste it* with
[+paste](/{{ site.uprefix }}/basic/capture-and-paste):


```shell
$ sudo test/ds/script-requires-root.sh                  # byexample: +paste +type +skip
<...>password for user: [<PASS>]
Checking <...>
Done.
```

Then, you should run `byexample` passing that `PASS` variable and
[capturing the environment](/{{ site.uprefix }}/advanced/capture-environment-variables)
so the variable is available in the example and be pasted into.

Something like this:

```shell
$ PASS=johnpasswordhere byexample -l shell --capture-env-var PASS test/ds/doc-with-sudo.md      # byexample: +skip
[PASS] Pass: 1 Fail: 0 Skip: 0
```

### Uncertainty due `sudo` caching the password

Passing a password will work but **beware**.

The example where you are typing the password (with or without having it
pasted from `PASS`) *depends* on `sudo` *asking* the password in the first
place.

`sudo` caches the password and subsequent calls to `sudo` will not
ask for the password again. But this cache expires after a while (in my
system is after 15 minutes).


If you have a long running examples, this may cause you some troubles
as you could not tell when a call to `sudo` will or will not ask for a
password.

To be certain you could call `sudo -k` to clean up the cache and be sure
that the next call to `sudo` will ask you a password.

## Running the entire shell with `sudo`

If instead of having to run a few commands as root you need an entire
shell session, you can pass `sudo` in the
[shebang](/{{ site.uprefix }}/advanced/shebang):

```shell
$ byexample -l shell -x-shebang 'shell:%e sudo %p %a' test/ds/doc-without-sudo.md      # byexample: +skip
[PASS] Pass: 1 Fail: 0 Skip: 0
```

This simplifies your documentation avoiding all the `sudo` calls but
there is a catch.

At the moment `byexample` does not support passing passwords to the
shebang so you will have to make the shell program (typically `bash`)
*passwordless*.

If making **any** `sudo bash` passwordless scares you (and it should!),
we can lower slightly the risk with an auxiliary script that opens `bash` (or other
shell [supported by `byexample`](/{{ site.uprefix }}/languages/shell)):

```
#!/bin/sh
bash "$@"
```

We make the auxiliary script `open-bash.sh` passwordless editing
`sudoers`:

```
john ALL=(root) NOPASSWD: /home/john/full-path-here/test/ds/open-bash.sh
```

With this only `sudo test/ds/open-bash.sh` will be passwordless, other
calls to `sudo bash` will require a password as usual.

Finally we tell `byexample` to use that script instead of `bash`:

```shell
$ byexample -l shell -x-shebang 'shell:%e sudo test/ds/open-bash.sh %a' test/ds/doc-without-sudo.md      # byexample: +skip
[PASS] Pass: 1 Fail: 0 Skip: 0
```

The advantage is that we can create
`/home/john/full-path-here/test/ds/open-bash.sh` before running
`byexample` and delete it after. Assuming that you don't allow anyone
else to create the file, this is relatively safe.

If you have trouble with this or you feel that `byexample` is missing a
feature, don-t be afraid and [open an issue in Github](https://github.com/byexamples/byexample/issues).
