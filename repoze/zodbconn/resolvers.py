import os
import cgi
import urlparse

from repoze.zodbconn.datatypes import byte_size
from repoze.zodbconn.datatypes import FALSETYPES
from repoze.zodbconn.datatypes import TRUETYPES

from ZODB.FileStorage.FileStorage import FileStorage
from ZODB.DemoStorage import DemoStorage
from ZODB.blob import BlobStorage
from ZODB.DB import DB

def interpret_int_args(argnames, kw):
    newkw = {}

    # boolean values are also treated as integers
    for name in argnames:
        value = kw.get(name)
        if value is not None:
            value = value.lower()
            if value in FALSETYPES:
                value = 0
            if value in TRUETYPES:
                value = 1
            value = int(value)
            newkw[name] = value

    return newkw

def interpret_string_args(argnames, kw):
    newkw = {}
    # strings
    for name in argnames:
        value = kw.get(name)
        if value is not None:
            newkw[name] = value
    return newkw

def interpret_bytesize_args(argnames, kw):
    newkw = {}

    # suffix multiplied
    for name in argnames:
        value = kw.get(name)
        if value is not None:
            newkw[name] = byte_size(value)

    return newkw

class Resolver(object):
    def interpret_kwargs(self, kw):
        new = {}
        newkw = interpret_int_args(self._int_args, kw)
        new.update(newkw)
        newkw = interpret_string_args(self._string_args, kw)
        new.update(newkw)
        newkw = interpret_bytesize_args(self._bytesize_args, kw)
        new.update(newkw)
        return new

class FileStorageURIResolver(Resolver):
    _int_args = ('create', 'read_only', 'demostorage', 'connection_cache_size',
                 'connection_pool_size')
    _string_args = ('blobstorage_dir', 'blobstorage_layout', 'database_name')
    _bytesize_args = ('quota',)
    def __call__(self, uri):
        (scheme, netloc, path, query, frag) = urlparse.urlsplit(uri)
         # urlparse doesnt understand file URLs and stuffs everything into path
        (scheme, netloc, path, query, frag) = urlparse.urlsplit('http:' + path)
        path = os.path.normpath(path)
        kw = dict(cgi.parse_qsl(query))
        kw = self.interpret_kwargs(kw)
        dbkw = get_dbkw(kw)
        items = kw.items()
        items.sort()
        args = (path,)
        dbitems = dbkw.items()
        dbitems.sort()
        key = (args, tuple(items), tuple(dbitems))
        demostorage = False

        if 'demostorage'in kw:
            kw.pop('demostorage')
            demostorage = True

        blobstorage_dir = None
        blobstorage_layout = 'automatic'
        if 'blobstorage_dir' in kw:
            blobstorage_dir = kw.pop('blobstorage_dir')
        if 'blobstorage_layout' in kw:
            blobstorage_layout = kw.pop('blobstorage_layout')

        if demostorage and blobstorage_dir:
            def factory():
                filestorage = FileStorage(*args, **kw)
                demostorage = DemoStorage(base=filestorage)
                blobstorage = BlobStorage(blobstorage_dir, demostorage,
                                          layout=blobstorage_layout)
                return DB(blobstorage, **dbkw)
        elif blobstorage_dir:
            def factory():
                filestorage = FileStorage(*args, **kw)
                blobstorage = BlobStorage(blobstorage_dir, filestorage,
                                          layout=blobstorage_layout)
                return DB(blobstorage, **dbkw)
        elif demostorage:
            def factory():
                filestorage = FileStorage(*args, **kw)
                demostorage = DemoStorage(base=filestorage)
                return DB(demostorage, **dbkw)
        else:
            def factory():
                filestorage = FileStorage(*args, **kw)
                return DB(filestorage, **dbkw)

        return key, args, kw, factory

class ClientStorageURIResolver(Resolver):
    _int_args = ('debug', 'min_disconnect_poll', 'max_disconnect_poll',
                 'wait_for_server_on_startup', 'wait', 'wait_timeout',
                 'read_only', 'read_only_fallback', 'shared_blob_dir',
                 'demostorage', 'connection_cache_size',
                 'connection_pool_size')
    _string_args = ('storage', 'name', 'client', 'var', 'username',
                    'password', 'realm', 'blob_dir', 'database_name')
    _bytesize_args = ('cache_size', )

    def __call__(self, uri):
        (scheme, netloc, path, query, frag) = urlparse.urlsplit(uri)
         # urlparse doesnt understand zeo URLs and stuffs everything into path
        (scheme, netloc, path, query, frag) = urlparse.urlsplit('http:' + path)
        if netloc:
            # TCP URL
            if ':' in netloc:
                host, port = netloc.split(':')
                port = int(port)
            else:
                host = netloc
                port = 9991
            args = ((host, port),)
        else:
            # Unix domain socket URL
            path = os.path.normpath(path)
            args = (path,)
        kw = dict(cgi.parse_qsl(query))
        kw = self.interpret_kwargs(kw)
        dbkw = get_dbkw(kw)
        items = kw.items()
        items.sort()
        dbitems = dbkw.items()
        dbitems.sort()
        key = (args, tuple(items), tuple(dbitems))
        if 'demostorage' in kw:
            kw.pop('demostorage')
            def factory():
                from ZEO.ClientStorage import ClientStorage
                from ZODB.DB import DB
                from ZODB.DemoStorage import DemoStorage
                demostorage = DemoStorage(base=ClientStorage(*args, **kw))
                return DB(demostorage, **dbkw)
        else:
            def factory():
                from ZEO.ClientStorage import ClientStorage
                from ZODB.DB import DB
                clientstorage = ClientStorage(*args, **kw)
                return DB(clientstorage, **dbkw)
        return key, args, kw, factory

def get_dbkw(kw):
    dbkw = {}
    dbkw['cache_size'] = 10000
    dbkw['pool_size'] = 7
    dbkw['database_name'] = 'unnamed'
    if 'connection_cache_size' in kw:
        dbkw['cache_size'] = int(kw.pop('connection_cache_size'))
    if 'connection_pool_size' in kw:
        dbkw['pool_size'] = int(kw.pop('connection_pool_size'))
    if 'database_name' in kw:
        dbkw['database_name'] = kw.pop('database_name')

    return dbkw


RESOLVERS = {
    'zeo':ClientStorageURIResolver(),
    'file':FileStorageURIResolver(),
    }
