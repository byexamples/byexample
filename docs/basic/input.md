<!--
Check that we have byexample installed first
$ hash byexample                                    # byexample: +fail-fast

$ alias byexample=byexample\ --pretty\ none\ -x-not-recover-timeout\ --timeout\ 0.2

-->

# Type Text

There are cases when an example requires input from the user
like when you are running an *interactive* code or command.

Starting from 9.1.0, `byexample` allows you to *type* text.

This is enabled with `+input` and starting from 10.0.3 you
can enable it with `+type`.

Imagine the following scenario where an example requests your
name:

```python
>>> name = input("your name please: ")      # byexample: +type
your name please: [john]
```

The example works as usual with two peculiarities: first we
enable the typing mode with `+type` and second we write between
brackets the text that we want to type like `[john]`.

`byexample` will run the example and when it find the moment it will
write `john` to the standard input.

```python
>>> print(name)
john
```

Here is an example that ask several things at once:

```python
>>> def ask():
...     n = input("name: ")
...     print("Nice to meet you %s!" % n)
...     a = input("age: ")
...     print("%s years old" % a)

>>> ask()               # byexample: +type
name: [john]
Nice to meet you john!
age: [42]
42 years old
```

> **Note:** `byexample` will only recognize inputs that are at
> the end of a line. If an input appears in other place `byexample`
> will let you know and issue a warning.

> **Warning:** typing something when the example is not waiting for
> an input is *undefined*. Most probably the typed text will be forwarded
> to the underlying runner or interpreter, it may be partially executed
> and most likely will *break* the synchronization with `byexample`.
> Not fun.

And here is an example that read three lines in a row: this is
how you need to input a text that spans *more than one* line.

```python
>>> import sys
>>> def read_lines(num):
...     lines = []
...     for cnt, line in enumerate(sys.stdin, 1):
...         lines.append("recv: " + line)
...         if cnt == num:
...             break
...     print(''.join(lines))

>>> read_lines(3)               # byexample: +type
[hello]
[my name is John]
[how are you?]
recv: hello
recv: my name is John
recv: how are you?
```

## Alias: +input / +type

Starting from `byexample 10.0.3` you can use `+type` or `+input`
to enable this feature. Both are the same.

```python
>>> name = input("your name please: ")      # byexample: +type
your name please: [john]

>>> print(name)
john

>>> name = input("your name please: ")      # byexample: +input
your name please: [joanna]

>>> print(name)
joanna
```

If you are using an older version of `byexample`, `+type` will
not available and you will have to use `+input`.

## Support

Input is an *experimental* feature: any kind of comments are welcome.

Don't be afraid to
[open an issue in Github](https://github.com/byexamples/byexample/issues).

See the documentation page of each language for more information.


## The Input Prefix

When `byexample` finds a `[text]` it knows that it needs to type
the that text but it does not know *when* it should do it.

Some runners/interpreters are sensible to this and typing the text before
the right moment may make them to *ignore* the text.

For this reason `byexample` uses the text that appears *before* `[text]`
and waits for it before start typing.

In general `byexample` is smart enough to keep all of this behind scenes
however, when a capture tag is found, `byexample` requires at minimum
of text before the input tag and if there is not enough it will complain:

```shell
$ cat test/ds/minimum-ctx-input.md          # byexample: +rm= 
 <...>
 >>> x = input("say: ")      # byexample: +type
 sa<...>y: [foo]
 
 >>> x
 'foo'
 <...>


$ byexample -l python test/ds/minimum-ctx-input.md
<...>=> Parse of example 1 of 2 failed.
ValueError: There are too few characters (3) before the input tag at character 10th to proceed
<...>
[ABORT] Pass: 0 Fail: 0 Skip: 0
```

In these cases `byexample` requires a *minimum* of prefix.

In other cases, `byexample` may use too much of the text *before* `[text]`:
it may wait for too large text before start typing.

This can be a problem if the text that you are expecting does not match
with the output of the example.

If the mismatch happen too close to `[text]`, `byexample` may never type
the given text; if the example keeps waiting for it the example will
eventually timeout:

```shell
$ cat test/ds/maximum-ctx-input.md      # byexample: +rm= 
 <...>
 >>> x = input("Some large text: ")      # byexample: +type
 Some typo! text: [foo]
 
 >>> x
 'foo'
 <...>

$ byexample -l python test/ds/maximum-ctx-input.md
<...>=> Execution timedout at example 1 of 2.
- This could be because the example just ran too slow (try add more time
with +timeout=<n>) or the example is "syntactically incorrect" and
the interpreter hang (may be you forgot a parenthesis or something like that?).
- This happen before typing 'foo'.
Perhaps the text before did not match what you expected?
typo! text:
- This is the last output obtained:
Some large text:
<...>
[ABORT] Pass: 0 Fail: 1 Skip: 0
```

Of course the problem is that the expected and the got outputs are different
(`typo! text:` and `Some large text:` respectively) and it should be fixed
in the first place but because `byexample` will not
type anything that may generate more mismatches later which makes
the whole thing more difficult to understand.

`byexample` uses a `maximum` of prefix to control this: larger prefixes
increase the probability of having a mismatch and making `byexample` to
not type the text; smaller prefixes on the other hand may make `byexample`
to type the text sooner and the example could ignore it.

Both minimum and maximum can be controlled by an option per example
or globally:

```shell
$ byexample -l python -o '+input-prefix-range=3:12' test/ds/minimum-ctx-input.md
<...>
[PASS] Pass: 2 Fail: 0 Skip: 0

$ byexample -l python -o '+input-prefix-range=4:4' test/ds/maximum-ctx-input.md
<...>
Expected:
Some typo! text: [foo]
Got:
Some large text: [foo]
<...>
```

## Input a Pasted Text

It is perfectly possible to capture a text in one example
and use it as input for another.

The only thing you need is to enable the
[paste mode](/{{ site.uprefix }}/basic/capture-and-paste)
`+paste` and the input mode `+type`.

```python
>>> 42
<magic>

>>> n = input("a number please: ")      # byexample: +paste +type
a number please: [<magic>]

>>> s = input("a password: ")           # byexample: +paste +type
a password: [admin<magic>!]

>>> n
'42'

>>> s
'admin42!'
```

> **Warning:** pasting inside an input tag is okay, *capturing* is not.
> It makes no sense. This could happen by accident if the tag you are using
> did not capture anything before, it is new or you forgot to enable the
> [paste mode](/{{ site.uprefix }}/basic/capture-and-paste)
> with `+paste`.


<!--
Hide these examples/tests from the user: they don't add too much
value but they are here because is a simple way to test if all
the interpreters support the 'input' feature.

Also use '+input' instead of '+type' to test this flag too
which should be an alias.

Python:
>>> input("num: ")   # byexample: +input
num: [42]
'42'

Shell:
$ read -p "num: " ; echo $REPLY    # byexample: +input
num: [42]
42

Ruby:
>> gets     # byexample: +input
[hi!]
=> "hi!\n"

PowerShell:
PS> $num = Read-Host num    # byexample: +input +pass
num: [i love 42]
PS> echo $num
i love 42


The problem when we cannot disabled the echo from the interpreter
is that the algorithm that searches for the input's prefix matches
the text echoed instead of the real output
This not only defeats the purpose of the input's prefix but also
makes byexample to echo the input's prefix and the [input] in
the wrong place

It is really broken


C++: not supported
?: #include <iostream>
?: int n;
?: std::cout << "num:\n" ; std::cin >> n;   n       // byexample: +input +skip
num:
[42]
(int) 42

PHP: not supported
php> $f = fopen('php://stdin', 'r');
php> echo fgets($f);      // byexample: +input +skip
[42]
42

Javascript: not supported
> const readline = require('readline');
> const rl = readline.createInterface({
.   input: process.stdin,
.   terminal: false
. });

> rl.question('nu'+'m: ', (n) => {             // byexample: +input +skip
.   console.log(n + " is a cool number");
. });
num: [42]
42 is a cool number

GDB: not needed?
(gdb) help help  # byexample: +input +skip
No idea what example could we do here

Elixir: not supported
iex> IO.gets("num: ")         # byexample: +input +skip
num: [42]
=> "42\n"
-->
