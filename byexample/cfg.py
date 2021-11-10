from __future__ import unicode_literals
from .common import transfer_constants
import collections
import collections.abc


class Config(collections.abc.Mapping):
    ''' An immutable configuration object.

        Once the configuration was loaded, this object should be
        used to maintain constant references/values.

        Only 4 keys are allowed to reference mutable values:
         - options: to hold dynamic options
         - output: the file where write to
         - registry: the parsers, runners and other dynamic objects
         - namespaces: a dictionary of namespaces by registry objects' classes.
           Each namespace is a mutable object shared among the workers.

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
        exception_keys = ('options', 'output', 'registry', 'namespaces')
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
             - namespaces: a dictionary of namespaces by class

            The copy of this Config object will be independent of
            the original because:

             - The mutable 'options' are copied and therefore independent
             - The mutable 'registry' is recreated (and if we assume that the
             registry's values (parsers, runners) do not share things (like
             global variables, class attributes) then the copy is independent.
             - The mutable 'namespaces' is shallowly copied and each of its
             namespaces are transformed in a named tuple (constant objects).

            The copied Config will be independent of the original except in
            2 places:

             - The output file will be the same
             - The content of each namespace in the 'namespaces' dictionary
             are expected to be shareable by definition and
             therefore *not* independent. The copy() method will make each of
             these namespaces objects a named tuple, constant by definition, but
             it will not touch the *content* of them.
             It is up to the user/client avoid any race condition that may
             arose in the access of the namespace objects' content.
             See byexample.jobs.

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
            elif k == 'namespaces':
                v = self._recreate_namespaces_as_namedtuples(v)

            new[k] = v

        new.update(patch)
        # pop out 'namespaces' because it is not a global configuration.
        # instead, _recreate_registry will pass to each object its own local
        # namespace (if any)
        namespaces = new.pop('namespaces')
        new['registry'] = self._recreate_registry(
            self['registry'], new, namespaces
        )
        new['namespaces'] = namespaces
        return Config(new)

    def _namespace_as_namedtuple(self, ns):
        # "tuplefy": make the mutable namespace 'ns' an
        # immutable named tuple
        NS = collections.namedtuple('Namespace', ns._attribute_names)
        return NS(**{n: getattr(ns, n) for n in ns._attribute_names})

    def _recreate_namespaces_as_namedtuples(self, namespaces_by_class):
        ''' Return an independent copy of the namespaces making each
            namespace an immutable named tuple.

            Note that the content of each namespace is *still* mutable
            and it may lead to RC but this is on purpose and it is up
            to the user/client to not end in a race condition.
        '''
        return {
            klass: self._namespace_as_namedtuple(ns)
            for klass, ns in namespaces_by_class.items()
        }

    def _recreate_registry(self, registry, cfg, namespaces_by_class):
        ''' Create a copy of the registry recreating its objects. '''
        new = {}
        EmptyNS = collections.namedtuple('Namespace', [])
        empty_ns = EmptyNS()  # a placeholder when the object has no namespace
        for what in registry:
            container = registry[what]
            new[what] = {}

            for k, obj in container.items():
                ns = namespaces_by_class.get(obj.__class__, empty_ns)
                obj2 = obj.__class__(ns=ns, **cfg)
                transfer_constants(obj, obj2)

                new[what][k] = obj2

        return new
