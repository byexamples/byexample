import collections, argparse, shlex

class Options(collections.MutableMapping):
    r'''
    The execution of the examples can be modified by configuring different options.

    ``Options`` behaves as a normal dictionary

        >>> from byexample.options import Options
        >>> opt = Options()

        >>> opt['foo'] = 42
        >>> opt['foo']
        42

        >>> opt['bar']
        Traceback (most recent call last):
        <...>
        KeyError: 'bar'

        >>> len(opt)
        1

        >>> del opt['foo']
        >>> len(opt)
        0

    But the interesting is that it works as a stack of dictionaries: one can push
    a new dictionary on the top of the stack where new keys can be set but the
    rest of the dictionaries are keep intact.
    If a key is retrieved, the search starts from the top through all the stack
    until the key is found.
    To control the stack there are two methods ``up`` and ``down``. We could use
    the classic ``push`` and ``pop`` but a dictionary already has a ``pop`` so
    we preferred to not break that contract.

        >>> opt['foo'] = 42
        >>> opt.up() # push a new dictionary
        >>> opt['bar'] = 256

        >>> opt['foo'], opt['bar'] # look up through the entire stack
        (42, 256)

        >>> len(opt)
        2

        >>> sorted(list(opt))
        ['bar', 'foo']

        >>> d = opt.as_dict()   # actually, you can see it as a normal dictionary
        >>> isinstance(d, dict)
        True
        >>> d['foo'], d['bar']
        (42, 256)

        >>> del opt['foo'] # but only the top most dictionary is mutable
        Traceback (most recent call last):
        <...>
        KeyError: 'foo'

        >>> opt['foo'] = 257 # this only hides the 'foo' key of the dict below
        >>> opt['foo']
        257

        >>> opt.down() # remove the top most dictionary from the stack
        >>> opt['foo']
        42

        >>> 'bar' in opt
        False

    Multiple levels are allowed

        >>> opt = Options({'foo': 1})
        >>> opt.up({'foo': 2, 'bar': 2})
        >>> opt.up({'foo': 3, 'baz': 3})

        >>> sorted(list(opt))
        ['bar', 'baz', 'foo']

        >>> [opt[x] for x in sorted(list(opt))]
        [2, 3, 3]

        >>> opt.down()
        >>> [opt[x] for x in sorted(list(opt))]
        [2, 2]

        >>> opt.down()
        >>> [opt[x] for x in sorted(list(opt))]
        [1]

        >>> opt.down()
        Traceback (most recent call last):
        <...>
        IndexError: list index out of range

    Even you can push argparse.Namespace objects

        >>> from argparse import Namespace
        >>> opt.up(Namespace(foo=2, bar=2))

        >>> sorted(list(opt))
        ['bar', 'foo']

        >>> [opt[x] for x in sorted(list(opt))]
        [2, 2]

    '''

    def __init__(self, *args, **kwargs):
        self.top = dict()
        self.stack = [self.top] # [top, ...., bottom]

        self.cache = None

        self.update(dict(*args, **kwargs))  # use the free update to set keys

    def __getitem__(self, key):
        for d in self.stack:
            if key in d:
                return d[key]

        return self.top[key] # KeyError

    def __setitem__(self, key, value):
        self.top[key] = value

    def __delitem__(self, key):
        del self.top[key]

    def __iter__(self):
        return iter(self.as_dict())

    def __len__(self):
        return len(self.as_dict())

    def __repr__(self):
        return repr(self.as_dict())

    def up(self, other_mapping=None):
        if isinstance(other_mapping, Options):
            other_mapping = other_mapping.as_dict()

        if isinstance(other_mapping, argparse.Namespace):
            other_mapping = vars(other_mapping)

        self.top = other_mapping if other_mapping is not None else {}
        self.stack.insert(0, self.top)
        if self.top:
            self.cache = None

    def down(self):
        if self.top:
            self.cache = None

        del self.stack[0]
        self.top = self.stack[0]

    def as_dict(self):
        if len(self.stack) > 1 and self.cache is not None:
            collapsed = self.cache.copy()
        elif len(self.stack) == 1:
            collapsed = {}
        else:
            collapsed = self.stack[-1].copy()
            for d in reversed(self.stack[1:-1]):
                collapsed.update(d)

            self.cache = collapsed.copy()

        collapsed.update(self.top)
        return collapsed

    def copy(self):
        clone = Options()
        clone.stack = list(self.stack) # copy
        clone.cache = self.cache       # do not copy
        clone.top = clone.stack[0]

        return clone

class UnrecognizedOption(Exception):
    pass

class OptionParser(argparse.ArgumentParser):
    def __init__(self, **kw):
        if 'prefix_chars' not in kw:
            kw['prefix_chars'] = '-+'

        if 'argument_default' not in kw:
            # if an option is not explicitly set, and it has no
            # a default value, do not create an entry for it
            kw['argument_default'] = argparse.SUPPRESS

        argparse.ArgumentParser.__init__(self, **kw)

    def add_flag(self, name, **kw):
        g = self.add_mutually_exclusive_group()
        g.add_argument("+" + name, action='store_true', **kw)
        g.add_argument("-" + name, action='store_false')

        return self

    def defaults(self):
        return self.parse(None)

    def parse(self, source, strict):
        try:
            source = shlex.split(source)
        except:
            pass

        if not source:
            source = []

        if not isinstance(source, list):
            raise ValueError("The source for the OptionParser is neither a string nor a list but it is '%s'." % type(source))

        if strict:
            args = self.parse_args(source)
        else:
            args = self.parse_known_args(source)[0]

        return Options(vars(args))

    def error(self, message):
        raise UnrecognizedOption(message)
