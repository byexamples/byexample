'''
Byexample will look for examples in any language
inside of the Python multi line strings (those that starts
with three single or double quotes).

This is an example in Python
    >>> 1 + 2
    3

More examples:
>>> i = 0
>>> i + 2
2

>>> def foo():
...   print("hello!")

>>> foo()
hello!
'''

def awesome():
    r"""
        Here is another example, Shell this time:
        $ echo "Python rocks!"
        Python rocks!
    """
    return 1

''' '''
# >>> 1 + 2
# No, this is not an example.
''' '''

files with invalid syntax (like this one!) may affect the ability of
byexample to find the docstrings and the examples but byexample will try
to do its best.
