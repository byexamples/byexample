from __future__ import unicode_literals
import sre_parse
import sre_compile
import appdirs
import os
import sys
import contextlib
import errno
import warnings

from .log import clog, log_context

try:
    import cPickle as pickle
except ImportError:
    import pickle

try:
    # See https://docs.python.org/3.6/library/msvcrt.html
    import msvcrt

    def _at_begin(file):
        fpos = file.tell()
        try:
            file.seek(0, 0)
            yield f
        finally:
            file.seek(fpos, 0)

    def _acquire_flock_os(file, read_lock):
        # Note: this has the side effect of chainging the file position
        # and restoring it back during the lock-operation

        # https://docs.microsoft.com/en-us/cpp/c-runtime-library/reference/locking?view=vs-2019
        # seems that msvcrt has no support for read or shared locks
        mode = msvcrt.LK_LOCK
        while True:
            try:
                with _at_begin(file):
                    msvcrt.locking(file.fileno(), mode, 1)
                break
            except OSError as err:
                if err.errno in (errno.EACCES, errno.EDEADLOCK):
                    continue
                raise

    def _release_flock_os(file):
        # Note: this has the side effect of chainging the file position
        # and restoring it back during the lock-operation
        with _at_begin(file):
            msvcrt.locking(file.fileno(), msvcrt.LK_UNLCK, 1)
except ImportError:
    pass

try:
    # See https://docs.python.org/3/library/fcntl.html#fcntl.flock
    import fcntl

    def _acquire_flock_os(file, read_lock):
        fcntl.lockf(
            file.fileno(), fcntl.LOCK_SH if read_lock else fcntl.LOCK_EX
        )

    def _release_flock_os(file):
        fcntl.lockf(file.fileno(), fcntl.LOCK_UN)
except ImportError:
    pass


@contextlib.contextmanager
def flock(file, read_lock=False):
    _acquire_flock_os(file, read_lock)
    try:
        yield
    finally:
        _release_flock_os(file)


def create_file_new_or_fail(name):
    # The 'x' means create a new file or fail
    # Honestly, I'm not sure if 'x' is race-condition free
    # this is a best effort implementation
    return open(name, 'xb')


'''
>>> from byexample.log import init_log_system
>>> init_log_system()

>>> from byexample.cache import RegexCache
>>> import warnings
>>> warnings.filterwarnings('ignore', module='byexample.cache')

Currently this feature does not work on Python 3.8
>>> import sys
>>> if sys.version_info <= (3, 7):
...     print("cache enabled")
<cache-enabled>
'''


class RegexCache(object):
    def __init__(self, filename, disabled=False, cache_verbose=False):
        self.disabled = disabled
        self.verbose = cache_verbose
        if self.disabled:
            return

        warnings.warn(
            "Cache is enabled. This is an *experimental* feature",
            RuntimeWarning
        )

        try:
            _acquire_flock_os
            _release_flock_os
        except NameError:
            # if we cannot prevent race condition due a lack of file locks,
            # disable the cache
            warnings.warn(
                "Cache will be disabled because the current OS/file system does not support file locks",
                RuntimeWarning
            )
            self.disabled = True

        if filename:
            self.filename = self._cache_filepath(filename)
            self._cache = self._load_cache_from_disk()
        else:
            self.filename = None
            self._cache = self._new_cache()

        self.clear_stats()
        clog().chat("Cache '%s': %i entries", self.filename, self._nkeys)

    @contextlib.contextmanager
    def synced(self, label=""):
        ''' Clear the cache's stats on enter and sync the cache
            on exit.
            '''
        if self.disabled:
            yield self
            return

        self.clear_stats()
        try:
            yield self
        finally:
            self._sync(label)

    @contextlib.contextmanager
    def activated(self, auto_sync, label=""):
        ''' Activate the cache (patch re.compile) on enter
            and deactivate it on exit.

            If auto_sync is True, also clear the cache's stats
            on enter and sync the cache on exit.
            '''
        if self.disabled:
            yield self
            return

        self._patch()
        try:
            if auto_sync:
                with self.synced(label):
                    yield self
            else:
                yield self
        finally:
            self._unpatch()

    @log_context('byexample.cache')
    def clear_stats(self):
        self._nkeys, self._hits = len(self._cache), 0

    @classmethod
    def _cache_filepath(cls, filename):
        ''' Create a valid file path based on <filename>.

            The path will be formed based on the user's cache directory,
            platform and python version.

            >>> RegexCache._cache_filepath('foo')
            '<user-cache-dir>/byexample/re-<platform>-<python-version>/foo'

            The dir part of <filename> is ignored:

            >>> RegexCache._cache_filepath('foo/bar/baz')
            '<user-cache-dir>/byexample/re-<platform>-<python-version>/baz'

            Note: this function *will* create any directory needed.
        '''

        version = "re-%s-%08i" % (sys.platform, sys.hexversion)
        dir = appdirs.user_cache_dir(appname='byexample', version=version)
        os.makedirs(dir, exist_ok=True)

        filename = os.path.basename(filename)
        return os.path.join(dir, filename)

    def _load_cache_from_disk(self):
        ''' Load the cache from disk, create an empty one if the
            cache doesn't exist.

            If the load/read fails, return a empty cache too.
            '''
        try:
            with open(self.filename, 'rb') as f, flock(f, read_lock=True):
                return self._read_cache_or_empty(f)
        except FileNotFoundError as e:
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
            clog().warn("Cache file '%s' corrupted.", self.filename)
            return self._new_cache()

    def _new_cache(self):
        return {}

    def _create_empty_cache_in_disk(self):
        ''' Create an empty cache in disk if doesn't exist yet. '''
        cache = self._new_cache()
        try:
            clog().info(
                "Cache file '%s' does not exist. Creating a new one...",
                self.filename
            )
            with create_file_new_or_fail(self.filename) as f, flock(f):
                # the open didn't fail, so it *must* be new:
                # save an empty cache
                pickle.dump(cache, f)
        except FileExistsError as e:
            pass

        return cache

    @log_context('byexample.cache')
    def _sync(self, label=""):
        misses = len(self._cache) - self._nkeys
        nohits = self._nkeys - self._hits

        clog().chat(
            "[%s] Cache stats: %i entries %i hits %i misses %i nohits.", label,
            len(self._cache), self._hits, misses, nohits
        )
        if misses and self.filename != None:
            clog().chat("[%s] Cache require sync.", label)
            with open(self.filename, 'rb+') as f, flock(f):
                # get a fresh disk version in case that other
                # byexample instance had touched the cache but
                # do not keep updating if we have too many nohits (useless
                # keys/entries)
                if nohits < 1000:
                    cache = self._read_cache_or_empty(f)
                    cache.update(self._cache)
                else:
                    cache = self._cache

                # write to disk the new updated cache, truncate
                # and shrink it if the new is smaller than the original.
                f.seek(0, 0)
                # XXX pickletools.optimize ??
                pickle.dump(cache, f)
                f.truncate()

            self.clear_stats()

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
                >>> r2 = get(r'foo.*bar', re.DOTALL)     # byexample: +if=cache-enabled

                >>> r1.pattern == r2.pattern       # byexample: +if=cache-enabled
                True

                >>> r3 = re.compile(r2) # from another regex         # byexample: +if=cache-enabled 
                >>> r4 = get(r2)        # but we don't support this  # byexample: +if=cache-enabled 
                Traceback <...>
                <...>
                ValueError: Regex pattern must be a string or bytes but it is <...>

            RegexCache.get uses internal, undocumented functions from re module.

        '''
        if not isinstance(pattern, (str, bytes)):
            raise ValueError(
                "Regex pattern must be a string or bytes but it is %s" %
                type(pattern)
            )

        key = (pattern, flags)
        try:
            bytecode = self._cache[key]
            self._hits += 1
        except KeyError:
            bytecode = self._pattern_to_bytecode(pattern, flags)
            self._cache[key] = bytecode

        return self._bytecode_to_regex(pattern, bytecode)

    def _pattern_to_bytecode(self, pattern, flags=0):
        if not isinstance(pattern, (str, bytes)):
            raise ValueError(
                "Regex pattern must be a string or bytes but it is %s" %
                type(pattern)
            )

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

        indexgroup = tuple(indexgroup)  # required in Python 3.7 to be a tuple
        return sre_compile._sre.compile(
            pattern, flags, code, ngroups - 1, groupindex, indexgroup
        )

    @log_context('byexample.cache')
    def _patch(self):

        # PATCH! TODO is a better way?!?
        self._original__sre_compile__compile = sre_compile.compile
        sre_compile.compile = self.get

        return self

    @log_context('byexample.cache')
    def _unpatch(self, *args, **kargs):
        sre_compile.compile = self._original__sre_compile__compile
