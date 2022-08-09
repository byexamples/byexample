# How to use a docker image

Imagine that you want to use an interpreter that it is not installed in
your system but it is in a docker image.

For example, the C++ interpreter
[cling](https://github.com/root-project/cling) is available in the
[eldipa/cling](https://hub.docker.com/r/eldipa/cling) docker image.

Let's say that you want to use that.

First, of course, you need to download the image from the docker
registry:

```shell
$ sudo docker pull eldipa/cling              # byexample: +skip
```

Now, create a script to run `cling` in the container:

```shell
#!/bin/bash
docker run --rm -it -v "$(pwd):/mnt" -w /mnt eldipa/cling cling "$@"
```

Call the script `docker-cling.sh`.

Assuming it is saved in `/home/john/`, give it execution permissions with
`chmod u+x /home/john/docker-cling.sh`.

The script will start a temporal interactive docker container and run
inside `cling` and it will mount the current directory from your host to
`/mnt`.

When the script is executed by `byexample`, the current directory will
be the same of `byexample`.

Finally, run `byexample` with a custom
[shebang](/{{ site.uprefix}}/advanced/shebang) and an extra timeout
(running docker is a little slow):

```shell
$ byexample -l cpp -x-shebang="cpp:sudo /home/john/docker-cling.sh %a" -x-dfl-timeout 30 <files>    # byexample: +skip
```

If you prefer you can write this long command line in a file for easy
reuse:

```shell
# boptions.args file
-l=cpp
-x-shebang=cpp:sudo /home/john/docker-cling.sh %a
-x-dfl-timeout=30
```

So you can then run `byexample` as follows:

```shell
$ byexample @boptions.args <files>    # byexample: +skip
```

Shorter, isn't?

Of course this example for C++ can be applied to any
language/interpreter and used in combination with interpreters that
don't require of docker.

The following combines C++ (in a docker) and Python (in the host)
without a problem:

```shell
$ byexample @boptions.args -l python <files>    # byexample: +skip
```

## Make `sudo` passwordless to avoid timeouts

In the example above I use `sudo` to run `docker-cling.sh`.
This is in general required because running `docker` is a privileged
operation.

Unfortunately this makes `sudo` to ask for a password
and `byexample` currently does not support that.

The solution is to make `sudo` passwordless for `docker-cling.sh`
editing your `sudoers` file with `visudo`.

Run `sudo visudo` and add the following line:

```
john ALL=(root) NOPASSWD: /home/john/docker-cling.sh
```

This tells `sudo` to not ask for a password (`NOPASSWD`) when the user
`john` is trying to execute the program
`/home/john/docker-cling.sh` to run it as
`root`.

Of course you will have to put *your* username and the full path of
`docker-cling.sh` in that line.

You can test that the `sudoers` rule is properly working running
`sudo /home/john/docker-cling.sh` by hand. It should open the `cling`
shell without asking a password.

### Issue: `sudo` still requires a password / prompt not found

If you see something like

```shell
$ byexample @boptions.args <files>    # byexample: +skip
[w] Initialization of Cpp Runner failed.
[!] Something went wrong processing the file <...>:
Prompt not found: the code is taking too long to finish or there is a syntax error.

Last 1000 bytes read:
[sudo] password for john:

Rerun with -vvv to get a full stack trace.
```

That indicates that `sudo` is not passwordless for `docker-cling.sh` yet.

Check that you used the correct full path to the `docker-cling.sh`
script in both `byexample` and in the `sudoers` file. (Something like
`/home/john/docker-cling.sh`).

Check also that you correctly typed the username.

Then, run `sudo /home/john/docker-cling.sh` and it should not require a
password.

Ensure also that the script does not call `sudo` itself (the script
should run `docker run...` and not `sudo docker run...`).

`sudo` will not give you a hint of what it is the problem. If something
does not match perfectly, `sudo` will fallback and ask a password.

### Issue: docker permission denied

If you get something like

```
docker: Got permission denied
```

That means that you need to use `sudo` as explained above.
