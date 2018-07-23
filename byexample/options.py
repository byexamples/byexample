import collections, argparse, shlex, pprint

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

        >>> opt
        {'bar': 2, 'baz': 3, 'foo': 3}

        >>> opt.down()
        >>> opt
        {'bar': 2, 'foo': 2}

        >>> opt.down()
        >>> opt
        {'foo': 1}

        >>> opt.down()
        Traceback (most recent call last):
        <...>
        IndexError: list index out of range

    If a key is not found, as any dictionary like, we will raise a KeyError
    exception.
    However it is possible to set a default value if a key is missing.

        >>> opt = Options({'foo': 1})
        >>> opt.mask_default(42)

        >>> opt['foo'], opt['bar']
        (1, 42)

    The 'mask_default' adds a mask layer with a default value. It is possible
    to stack several layers calling mask_default again.

        >>> opt.mask_default(64)
        >>> opt['foo'], opt['bar']
        (1, 64)

    This mask layering is independent of the stack of dictionaries:

        >>> opt.up({'foo': 2, 'bar': 2})
        >>> opt['foo'], opt['bar'], opt['baz']
        (2, 2, 64)

    And like any other layer, the default layer can be removed

        >>> opt.unmask_default()
        >>> opt['foo'], opt['bar'], opt['baz']
        (2, 2, 42)

        >>> opt.unmask_default()
        >>> opt['foo'], opt['bar'], opt['baz']
        Traceback (most recent call last):
        <...>
        KeyError: 'baz'

    Even you can push argparse.Namespace objects

        >>> from argparse import Namespace
        >>> opt.up(Namespace(foo=2, bar=2))

        >>> opt
        {'bar': 2, 'foo': 2}

    '''

    def __init__(self, *args, **kwargs):
        self.top = dict()
        self.stack = [self.top] # [top, ...., bottom]

        self.lower_levels_cached = {}

        self.update(dict(*args, **kwargs))  # use the free update to set keys
        self.default_values = []

    def __getitem__(self, key):
        if key in self.top:
            return self.top[key]

        if self.lower_levels_cached is None:
            for d in self.stack[1:-1]:
                if key in d:
                    return d[key]

            if self.default_values:
                return self.stack[-1].get(key, self.default_values[-1])
            else:
                return self.stack[-1][key] # found or KeyError
        else:
            if self.default_values:
                return self.lower_levels_cached.get(key, self.default_values[-1])
            else:
                return self.lower_levels_cached[key] # found or KeyError


    def __setitem__(self, key, value):
        self.top[key] = value

    def __delitem__(self, key):
        del self.top[key]

    def __iter__(self):
        return iter(self.as_dict())

    def __len__(self):
        return len(self.as_dict())

    def __repr__(self):
        return pprint.pformat(self.as_dict())

    def up(self, other_mapping=None):
        if isinstance(other_mapping, Options):
            other_mapping = other_mapping.as_dict()

        elif isinstance(other_mapping, argparse.Namespace):
            other_mapping = vars(other_mapping)

        elif other_mapping is not None:
            other_mapping = other_mapping.copy()

        if self.lower_levels_cached is not None:
            self.lower_levels_cached.update(self.top)

        self.top = other_mapping if other_mapping is not None else {}
        self.stack.insert(0, self.top)

    def down(self):
        del self.stack[0]
        self.top = self.stack[0]

        self.lower_levels_cached = None if len(self.stack) > 1 else {}

    def mask_default(self, val):
        self.default_values.append(val)

    def unmask_default(self):
        self.default_values.pop()

    def as_dict(self):
        r'''
        Return a copy of this Options in form of a dictionary.

            >>> from byexample.options import Options
            >>> opt = Options()

            >>> opt.as_dict()
            {}

            >>> opt.up({'foo': 1, 'bar': 2})
            >>> opt.as_dict()
            {'bar': 2, 'foo': 1}

            >>> opt.up({})
            >>> opt.as_dict()
            {'bar': 2, 'foo': 1}

            >>> opt.up({'foo': 3, 'baz': 4})
            >>> opt.as_dict()
            {'bar': 2, 'baz': 4, 'foo': 3}

        '''
        if self.lower_levels_cached is None:
            collapsed = self.stack[-1].copy()
            for d in reversed(self.stack[1:-1]):
                collapsed.update(d)

            self.lower_levels_cached = collapsed.copy()
        else:
            collapsed = self.lower_levels_cached.copy()

        collapsed.update(self.top)

        return collapsed

    def copy(self):
        r'''
        Return a copy:

            >>> from byexample.options import Options
            >>> opt = Options()

            >>> opt.copy()['foo'] = 42
            >>> opt
            {}

            >>> opt.up({'foo': 1, 'bar': 2})
            >>> opt.copy()['foo'] = 42
            >>> opt
            {'bar': 2, 'foo': 1}

            >>> opt.copy()
            {'bar': 2, 'foo': 1}

        '''
        clone = Options(self.stack[-1]) # bottom

        # clone pushing up
        for s in reversed(self.stack[:-1]):
            clone.up(s)

        clone.default_values = list(self.default_values)
        return clone


class UnrecognizedOption(Exception):
    pass

class OptionParser(argparse.ArgumentParser):
    def __init__(self, **kw):
        # allow the +flag/-flag semantics
        kw.setdefault('prefix_chars', '-+')

        # if an option is not explicitly set, and it has no
        # a default value, do not create an entry for it
        kw.setdefault('argument_default', argparse.SUPPRESS)

        # do not show any usage?
        kw.setdefault('usage', argparse.SUPPRESS)

        # do not show any program
        kw.setdefault('prog', "")

        # do not add -h/--help options
        kw.setdefault('add_help', False)

        argparse.ArgumentParser.__init__(self, **kw)

    def add_flag(self, name, group_required=False, **kw):
        g = self.add_mutually_exclusive_group(required=group_required)
        g.add_argument("+" + name, action='store_true', **kw)
        g.add_argument("-" + name, action='store_false', help=argparse.SUPPRESS)

        return g

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

    def __repr__(self):
        return "OptionParser(...)"


class ExtendOptionParserMixin(object):
    def extend_option_parser(self, parser):
        '''
        Extend the the instance of OptionParser that will be in
        charge of parsing the options from the command line and
        from the examples.

        Basically you need to see the options of an examples as if they were
        options and flags in a command line.
        '''
        raise NotImplementedError()

    def get_extended_option_parser(self, parent_parser, **kw):
        parents = [parent_parser] if parent_parser else []

        optparser_extended = OptionParser(parents=parents, **kw)
        self.extend_option_parser(optparser_extended)
        if not isinstance(optparser_extended, argparse.ArgumentParser):
            raise ValueError("The option parser is not an instance of ArgumentParser!. This probably means that there is a bug in %s." % str(self))

        return optparser_extended

