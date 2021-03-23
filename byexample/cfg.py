from __future__ import unicode_literals
from .common import transfer_constants
import collections


class Config(collections.Mapping):
    ''' An immutable configuration object.

        Once the configuration was loaded, this object should be
        used to maintain constant references/values.

        Only 4 keys are allowed to reference mutable values:
         - options: to hold dynamic options
         - output: the file where write to
         - registry: the parsers, runners and other dynamic objects
         - ns: a namespace shared among the workers

        The rest of the keys-values must be of immutable types.

        To use Config in a multithread/multiprocess environment,
        you need to call copy() to get an independent copy to work with.

        See the method's doc to know how those 4 mutable keys are handled.
    '''
    def __init__(self, *args, **kargs):
        self._d = dict(*args, **kargs)
        self._ensure_cfg_is_constant()

    def __getitem__(self, key):
        return self._d[key]

    def __iter__(self):
        return iter(self._d)

    def __len__(self):
        return len(self._d)

    def _ensure_cfg_is_constant(self):
        const_types = (int, frozenset, str, bool, bytes, type(None))
        exception_keys = ('options', 'output', 'registry', 'ns')
        for k, v in self._d.items():
            if k in exception_keys:
                continue

            if not isinstance(v, const_types):
                raise Exception(
                    "Non-immutable value for cfg['%s']: '%s'" %
                    (k, v.__class__)
                )

    def copy(self, patch={}):
        ''' Copy the configuration object borrowing references
            with a special copy operation for the registry and options
            keys.

            Assuming that all the values are constant (immutable),
            the copy does not incur in the costs of a real copy.

            Exceptions to this are:
             - options: which a real copy is made (see Options.copy)
             - output: a file which it is NOT copied
             - registry: which a recreation is made (see _recreate_registry)
             - ns: a namespace shared among the workers

            The copy of this Config object will be independent of
            the original because:

             - The mutable 'options' are copied and therefore independent
             - The mutable 'registry' is recreated (and if we assume that the
             registry's values (parsers, runners) do not share things (like
             global variables, class attributes) then the copy is independent.
             - The mutable 'ns' is transformed in a named tuple.

            The copied Config will be independent of the original except in
            2 places:

             - The output file will be the same
             - The content of 'ns' which it is expected to be shareable
             by definition and therefore *not* independent. The copy() method
             will make this object a named tuple, constant by definition, but
             it will not touch the *content* of 'ns'.
             It is up to the user/client avoid any race condition that may
             arose in the access of ns' content. See byexample.jobs.

            After the copy but before the recreation (_recreate_registry),
            the copied dictionary is optionally updated with <patch> dict.

            While it is technically possible to update/patch everything,
            the idea of <patch> is to allows to do a small update/change/patch
            to the configuration before becoming a constant again.

            The key and values of <patch> *must* follow the same 'constantness'
            rules of Config.
        '''
        patch = Config(patch)
        new = {}
        for k, v in self._d.items():
            if k == 'options':
                v = v.copy()
            elif k == 'registry':
                continue  # skip
            elif k == 'output':
                pass  # mutable but don't copy
            elif k == 'ns':
                # "tuplefy": make the mutable namespace 'ns' an
                # immutable named tuple
                NS = collections.namedtuple('Namespace', v._attribute_names)
                v = NS(**{n: getattr(v, n) for n in v._attribute_names})

            new[k] = v

        new.update(patch)
        new['registry'] = self._recreate_registry(self['registry'], new)
        return Config(new)

    def _recreate_registry(self, registry, cfg):
        ''' Create a copy of the registry recreating its objects. '''
        new = {}
        for what in registry:
            container = registry[what]
            new[what] = {}

            for k, obj in container.items():
                obj2 = obj.__class__(**cfg)
                transfer_constants(obj, obj2)

                new[what][k] = obj2

        return new
