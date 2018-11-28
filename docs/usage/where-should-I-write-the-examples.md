# Where should I write the examples?

Anywhere!

``byexample`` uses currently two levels of detection:

 - a generic Markdown Code Fenced Block based
 - a specific for each language based on prompts

For the first case, anything that it is between ````` ```<language> `````
and ````` ``` ````` is considered
an example; the ``out:`` marks the begin of the expected output:

`````python
 ```python
 1 + 2

 out:
 3
 ```
`````

For the second case, it will depend of the language of the example:
``>>>`` is for Python examples, ``>>`` for Ruby, ``$`` for Shell.

Take a look to the documentation of each language
[docs/languages](https://github.com/byexamples/byexample/tree/master/docs/languages/).

Here are some examples:

```python
>>> 1 + 2   # python
3
```

```ruby
>> 3 * 3    # ruby
=> 9
```

You can even mix the two ways in which case the specific will override the
generic one:

`````python
 ```python
 $ echo "hello"   # but this is shell
 hello
 ```
`````

## Detect the end of an example

``byexample`` detects the end of the example if:

 - it is followed by a prompt (the next example begins with ``>>>`` for example)
 - the text has a lower indentation level
 - there is a blank line

This is an example showing those three cases:

```python
>>> 1   # example 1 delimited by the second >>>
1
>>> 2   # example 2 delimited by a blank line
2

    >>> 3   # example 3 delimited by a text with a lower indentation level
    3
# this line has a lower indentation level
# and mark the end of the example too

>>> 4   # example 4 delimited by a blank line (see spurious endings)
4
```

### Spurious endings

Consider the following example written in a *mixed* way:

`````python
 ```python
 >>> 1 + 2
 3
 ```
`````

The initial expected string found by ``byexample`` would be ``3`` **plus**
````` ``` ````` because there is not a blank line that separate these two.

However, ``byexample`` will *ignore* the last line of an example if has some
special tokens like ````` ``` `````, ``~~~``, ``'''`` and ``-->``.

Check out [how to support new finders and languages](https://byexamples.github.io/byexample/how-to-support-new-finders-and-languages)
to see the internals of these.

## New lines at the end are ignored

``byexample`` will ignore any empty line(s) at the end of the expected string
and from the got string from the executed examples.

Look at this successful example even if the example prints several empty lines
at the end which are not expected:

```python
>>> print("bar\n\n")
bar
```

This is because most of the time an empty new line is added for aesthetics
purposes in the example or produced by the runner/interpreter as an artifact.

### New lines in the middle of the expected string

Most, if not all the examples use an empty line as delimiter to mark the end
of the expected string.

But what if you want to test a multiline text that has empty lines?

You can use a special character like ``~`` and instruct ``byexample`` to
ignore it with the ``rm`` option.

```python
>>> print("hello\n\nworld!")    # byexample: +rm=~
hello
~
world!
```


