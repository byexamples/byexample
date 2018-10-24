from __future__ import unicode_literals
import sre_parse
import sre_compile
import appdirs
import os
import sys
import contextlib
import fcntl

try:
    import cPickle as pickle
except ImportError:
    import pickle

try:
    unicode
except NameError:
    unicode = str

def cache_filepath(filename, type):
    ''' Create a valid file path based on <filename>.

        The path will be formed based on the user's cache directory,
        platform and python version and on the type of cache requested.

        >>> from byexample.cache import cache_filepath
        >>> cache_filepath('foo', 're')
        '<user-cache-dir>/byexample/re-<platform>-<python-version>/foo'

        The dir part of <filename> is ignored:

        >>> cache_filepath('foo/bar/baz', 're')
        '<user-cache-dir>/byexample/re-<platform>-<python-version>/baz'

        Note: this function *will* create any directory needed.
    '''

    if type == 're':
        version = "%s-%s-%08i" % (type, sys.platform, sys.hexversion)
    else:
        raise ValueError("Unsupported cache type version '%s'." % str(type))

    dir = appdirs.user_cache_dir(appname='byexample', version=version)
    try:
        os.makedirs(dir)
    except OSError:
        pass # note: for Python 3.2 and greater, use exist_ok=True (see makedirs)

    filename = os.path.basename(filename)
    return os.path.join(dir, filename)

@contextlib.contextmanager
def flock(file):
    fcntl.lockf(file.fileno(), fcntl.LOCK_EX)
    try:
        yield
    finally:
        fcntl.lockf(file.fileno(), fcntl.LOCK_UN)


class RegexCache(object):
    def __init__(self, filename, disabled=False):
        self.disabled = disabled
        if self.disabled:
            return

        self.filename = filename
        self.dirty = False

        self._cache = self._load_cache_from_disk()

    def _load_cache_from_disk(self):
        ''' Load the cache from disk, create an empty one if the
            cache doesn't exist.

            If the load/read fails, return a empty cache too.
            '''
        try:
            with open(self.filename, 'rb+') as f, flock(f):
                return self._read_cache_or_empty(f)
        except FileNotFoundError:
            return self._create_empty_cache_in_disk()

    def _read_cache_or_empty(self, file):
        ''' Read from the given file and load the cache.
            Assumes that the file is open for reading and its read
            pointer is at the begin of the file.

            This does not set any lock: use flock yourself to avoid
            a race condition.

            Return an empty cache if the read fails.
            '''
        try:
            return pickle.loads(file.read())
        except:
            # possible corrupt cache, ignore it
            print("Corrupted")
            return self._new_cache()

    def _new_cache(self):
        return {}

    def _create_empty_cache_in_disk(self):
        ''' Create an empty cache in disk if doesn't exist yet. '''
        cache = self._new_cache()
        try:
            # 'x' means create a new file or fail
            # honestly, I'm not sure if 'x' is race-condition free
            # this is a best effort implementation
            with open(self.filename, 'xb') as f, flock(f):
                # the open didn't fail, so it *must* be new:
                # save an empty cache
                f.write(pickle.dumps(cache))
        except FileExistsError:
            pass

        return cache

    def sync(self):
        if self.dirty and not self.disabled and self.filename != None:
            with open(self.filename, 'rb+') as f, flock(f):
                # get a fresh disk version in case that other
                # byexample instance had touched the cache
                cache = self._read_cache_or_empty(f)

                cache.update(self._cache)

                # write to disk the new updated cache, truncate
                # and shrink it if the new is smaller than the original.
                f.seek(0,0)
                f.write(pickle.dumps(self._cache))
                f.truncate()

            self.dirty = False

    def get(self, pattern, flags=0):
        ''' RegexCache.get compiles a pattern into a regex object like
            re.compile does.

            At difference with re.compile, RegexCache.get caches the
            bytecode, the internal representation of the regex
            instead of caching the whole regex object.

            If multiple times the same pattern is built, this is slower
            but enables us to serialize (pickle) the bytecode to disk.

                >>> import re
                >>> from byexample.cache import RegexCache

                >>> get = RegexCache(None).get

                >>> r1 = re.compile(r'foo.*bar', re.DOTALL)
                >>> r2 = get(r'foo.*bar', re.DOTALL)

                >>> r1.pattern == r2.pattern
                True

                >>> r3 = re.compile(r2) # from another regex
                >>> r4 = get(r2)  # but we don't support this
                Traceback <...>
                <...>
                ValueError: Regex pattern must be a string or bytes but it is <...>

            RegexCache.get uses internal, undocumented functions from re module.

        '''
        if not isinstance(pattern, (str, bytes, unicode)):
            raise ValueError("Regex pattern must be a string or bytes but it is %s"
                                % type(pattern))

        key = (pattern, flags)
        try:
            bytecode = self._cache[key]
        except KeyError:
            bytecode = self._pattern_to_bytecode(pattern, flags)
            self._cache[key] = bytecode
            self.dirty = True

        return self._bytecode_to_regex(pattern, bytecode)

    def _pattern_to_bytecode(self, pattern, flags=0):
        if not isinstance(pattern, (str, bytes)):
            raise ValueError("Regex pattern must be a string or bytes but it is %s"
                                % type(pattern))

        p = sre_parse.parse(pattern, flags)
        code = [i.real for i in sre_compile._code(p, flags)]

        flags = flags | p.pattern.flags
        ngroups = p.pattern.groups

        return (flags, code, ngroups, p.pattern.groupdict)

    def _bytecode_to_regex(self, pattern, bytecode):
        flags, code, ngroups, groupindex = bytecode

        # map in either direction
        indexgroup = [None] * ngroups
        for k, i in groupindex.items():
            indexgroup[i] = k

        return sre_compile._sre.compile(
            pattern, flags, code,
            ngroups-1,
            groupindex, indexgroup
        )

    def __enter__(self):
        if self.disabled:
            return self

        # PATCH! TODO is a better way?!?
        self._original__sre_compile__compile = sre_compile.compile
        sre_compile.compile = self.get

        #print("Cache [%s]: %i regexs on enter" % (self.filename, len(self._cache)))
        return self

    def __exit__(self, *args, **kargs):
        if self.disabled:
            return

        sre_compile.compile = self._original__sre_compile__compile
        self.sync()
        #print("Cache [%s]: %i regexs on exit" % (self.filename, len(self._cache)))

