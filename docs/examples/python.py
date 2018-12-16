'''
Quick Example in Python

byexample searches for examples of any language inside
of Python's docstrings.

Like this one:

>> puts "Ruby example inside of a Python file."
Ruby example inside of a Python file.
'''

class Awesome:
    r''' Class comment
    >>> 1 + 2
    3
    '''

    def cool(self):
        u""" Method comment
        >>> 2 + 2
        4
        """

'''
Actually byexample searches examples in any multiline comment
(those that starts with three single or double quotes), not necessary
a docstrings.

Shell example follows:
    $ echo "Python rocks!"
    Python rocks!
'''

# >>> 1 + 2
# No, this is not an example.

