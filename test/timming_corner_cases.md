<!--
Check that we have byexample installed first
$ hash byexample                                    # byexample: +fail-fast

$ alias byexample=byexample\ --pretty\ none

--
-->

## Shutdown

Ensure that if the program is slow and takes some reasonable time to
shutdown, don't raise a Timeout after stopping it

```shell
$ test/ds/sleepy/c.sh          # byexample: +timeout=10 +stop-on-silence +stop-signal=interrupt
Start
```

Run three very slow tests and send `byexample` to the background
as soon as possible.

```shell
$ byexample -l python test/ds/sleepy/{s1,s2,s3}.md  # byexample: +stop-on-silence 7
```

Now send a Ctrl-C (SIGINT) to abort the execution. It is expected that
the shutdown will take time to finish the current jobs (20 secs) but it
will not take the full time to run (60 secs) because it was aborted.

```shell
$ sleep 1 ; kill -2 %%    # byexample: +pass +timeout=3
$ fg            # byexample: +timeout 25 +rm=~
byexample --pretty none -l python test/ds/sleepy/{s1,s2,s3}.md
[i] User aborted. Waiting to finish the current active executions...
~
File test/ds/sleepy/s1.md, 2/2 test ran in <...> seconds
[PASS] Pass: 2 Fail: 0 Skip: 0
```

Forcing a shutdown doing a Ctrl-C (SIGINT) twice and more will
start breaking all the code but it will abort the execution faster.

Note how the timeouts sum up less than 20 secs proving that `byexample`
didn't complete any execution (it was aborted by hard) and finished.

```shell
$ byexample -l python test/ds/sleepy/{s1,s2,s3}.md  # byexample: +stop-on-silence 7

$ sleep 1 ; kill -2 %%    # byexample: +pass +timeout=3
$ fg            # byexample: +rm=~ +stop-on-silence 3
byexample --pretty none -l python test/ds/sleepy/{s1,s2,s3}.md
[i] User aborted. Waiting to finish the current active executions...

$ sleep 1 ; kill -2 %%    # byexample: +pass +timeout=3
$ fg            # byexample: +rm=~ +stop-on-silence 3
byexample --pretty none -l python test/ds/sleepy/{s1,s2,s3}.md
[w] Not waiting for the current active executions to finish...
Pressing more times Ctrl-C will force an immediate shutdown
but it will leave resources uncleaned (dangerous/unsafe).

$ sleep 1 ; kill -2 %%    # byexample: +pass +timeout=3
$ fg            # byexample: +timeout 3 +rm=~
<...>
KeyboardInterrupt<...>
```
