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
>>> 1 + 2
3
```

```ruby
>> 3 * 3
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

### Detect the end of an example

``byexample`` detects the end of the example if:

 - it is followed by a prompt (the next example begins with ``>>>`` for example)
 - the text has a lower indentation level
 - there is a blank line

This is an example showing those three cases:

```python
>>> 1   # example followed
1
>>> 1   # by another line with a prompt
1

    >>> 2
    2
# this line has a lower indentation level
# and mark the end of the example too

>>> 3
3

# extra blank line that separates the example
```

### Spurious endings

Consider the following example written in a *mixed* way:

`````python
 ```python
 >>> 1 + 2
 3
 ```
`````

The initial expected string found by byexample would be ``3`` **plus**
````` ``` ````` because there is not a blank line that separate these two.

However, byexample will *ignore* the last line of an example if has some
special tokens like ````` ``` `````, ``~~~``, ``'''`` and ``-->``.

Check out [how to support new finders and languages](https://byexamples.github.io/byexample/how_to_support_new_finders_and_languages)
to see the internals of these.

