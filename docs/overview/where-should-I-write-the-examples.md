<!--
Check that we have byexample installed first
$ hash byexample                                    # byexample: +fail-fast

$ alias byexample=byexample\ --pretty\ none

--
-->

# Where and How Should I Write the Examples?

For Markdown files (those with the ``.md`` extension),
``byexample`` searches examples inside of code blocks or
comments: anything that it is between ````` ```<language> `````
and ````` ``` ````` or between ``<!--`` and ``-->``. There is where
you should write them.

For Python files (``.py`` extension) you should write your examples
in a docstring.

For the rest of the files, the examples are searched in the entire file
so you are free to write your examples anywhere.

Once you decided where, it is time to write them prefixing them
with a *prompt*.

How to do that it will depend of the language of the example:
``>>>`` is the prompt for Python examples, ``>>`` for Ruby, ``$`` for Shell.

Here are some examples:

```python
>>> 1 + 2   # python
3
```

```ruby
>> 3 * 3    # ruby
=> 9
```

Notice how after the prompt you write a snippet of code and in the next line
the expected value.

Multi line examples are supported too using a *secondary prompt*:

```python
>>> [1, 2,      # python
...  3, 4]
[1, 2, 3, 4]
```

```ruby
>> puts "a long
.. text line"   # ruby
a long
text line
```

I *highly* recommend to you to read the documentation of language of your choice in
[docs/languages](https://github.com/byexamples/byexample/tree/master/docs/languages/)
to learn more about how to write examples and
[docs/examples](https://github.com/byexamples/byexample/tree/master/docs/examples/)
to see some examples.

For the *advanced* reader or the curious mind, check out
[how to support new finders and languages](/{{ site.uprefix }}/contrib/how-to-support-new-finders-and-languages)
Take a look if you want to add new languages and extend the capabilities
of ``byexample`` or if you are just curious of how this works.

## Full example

Take a look to this Markdown file, it has one Python example
and just one:

`````shell
$ cat test/ds/first-example.md
This a Markdown file with some examples embebed
like this one:
    ```python
    >>> 1 + 2
    3
    ```
However anything outside of a code block or comment
is ignored:
    >>> like this, this is not an example
    so it is not executed
`````

Let's run it:

```shell
$ byexample -l python test/ds/first-example.md
<...>
File test/ds/first-example.md, 1/1 test ran in <...> seconds
[PASS] Pass: 1 Fail: 0 Skip: 0
```

Once again I *highly* recommend to you to read the documentation of language
of your choice in
[docs/languages](https://github.com/byexamples/byexample/tree/master/docs/languages/)
and see some examples in
[docs/examples](https://github.com/byexamples/byexample/tree/master/docs/examples/).

## Detect the end of an example

``byexample`` detects the end of an example when:

 - it is followed by a prompt (the next example begins with ``>>>`` for example)
 - there is a blank line
 - it is followed by text with a lower indentation level
 - it is the end of the file or search area (like the end of a Markdown code block)

This is an example showing those four cases:

```python
>>> 1   # example 1 delimited by the second >>>
1
>>> 2   # example 2 delimited by a blank line
2

    >>> 3   # example 3 delimited by a text with a lower indentation level
    3
# this line has a lower indentation level
# and mark the end of the example too

>>> 4   # example 4 delimited by the end of the Markdown code block
4
```

## New lines in the middle of the expected string

An example ends when ``byexample`` finds an empty line.

But what if you want to test a multi line text that has empty lines?

You can use a special character like ``~`` and instruct ``byexample`` to
ignore it with the ``rm`` option.

```python
>>> print("hello\n\nworld!")    # byexample: +rm=~
hello
~
world!
```


## New lines at the end are ignored

By the way, ``byexample`` will ignore any empty line(s) at
the end of the expected string and from the got string
from the executed examples.

Look at this successful example even if the example prints several empty lines
at the end which are not expected:

```python
>>> print("bar\n\n")
bar
```

This is because most of the time an empty new line is added for aesthetics
purposes in the example or produced by the runner/interpreter as an artifact.

