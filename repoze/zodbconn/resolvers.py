from repoze.zodbconn.datatypes import byte_size
from repoze.zodbconn.datatypes import FALSETYPES
from repoze.zodbconn.datatypes import TRUETYPES

import os
import cgi
import urlparse

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
    _int_args = ('create', 'read_only')
    _string_args = ()
    _bytesize_args = ('quota',)
    def prepare(self, uri):
        (scheme, netloc, path, query, frag) = urlparse.urlsplit(uri)
         # urlparse doesnt understand file URLs and stuffs everything into path
        (scheme, netloc, path, query, frag) = urlparse.urlsplit('http:' + path)
        path = os.path.normpath(path)
        kw = dict(cgi.parse_qsl(query))
        kw = self.interpret_kwargs(kw)
        items = kw.items()
        items.sort()
        args = (path,)
        key = (args, tuple(items))
        return key, args, kw

    def __call__(self, uri):
        key, args, kw = self.prepare(uri)
        def factory():
            from ZODB.FileStorage.FileStorage import FileStorage
            from ZODB.DB import DB
            return DB(FileStorage(*args, **kw))
        return key, factory

class ClientStorageURIResolver(Resolver):
    _int_args = ('debug', 'min_disconnect_poll', 'max_disconnect_poll',
                  'wait_for_server_on_startup', 'wait', 'wait_timeout',
                  'read_only', 'read_only_fallback', 'shared_blob_dir')
    _string_args = ('storage', 'name', 'client', 'var', 'username',
                     'password', 'realm', 'blob_dir')
    _bytesize_args = ('cache_size', )

    def prepare(self, uri):
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
        items = kw.items()
        items.sort()
        key = (args, tuple(items))
        return key, args, kw

    def __call__(self, uri):
        key, args, kw = self.prepare(uri)
        def factory():
            from ZEO.ClientStorage import ClientStorage
            from ZODB.DB import DB
            return DB(ClientStorage(*args, **kw))
        return key, factory

RESOLVERS = {
    'zeo':ClientStorageURIResolver(),
    'file':FileStorageURIResolver(),
    }
