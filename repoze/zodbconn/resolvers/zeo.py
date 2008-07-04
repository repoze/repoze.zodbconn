from repoze.zodbconn.datatypes import byte_size
from repoze.zodbconn.datatypes import FALSETYPES
from repoze.zodbconn.datatypes import TRUETYPES

import cgi
import urlparse

class ZEOURIResolver:
    _int_args = ('debug', 'min_disconnect_poll', 'max_disconnect_poll',
                  'wait_for_server_on_startup', 'wait', 'wait_timeout',
                  'read_only', 'read_only_fallback', 'shared_blob_dir')
    _string_args = ('storage', 'name', 'client', 'var', 'username',
                     'password', 'realm', 'blob_dir')
    _bytesize_args = ('cache_size', )

    def interpret_kwargs(self, kw):
        newkw = {}

        # boolean values are also treated as integers
        for name in self._int_args:
            value = kw.get(name)
            if value is not None:
                value = value.lower()
                if value in FALSETYPES:
                    value = 0
                if value in TRUETYPES:
                    value = 1
                value = int(value)
                newkw[name] = value

        # strings
        for name in self._string_args:
            value = kw.get(name)
            if value is not None:
                newkw[name] = value

        # suffix multiplied
        for name in self._bytesize_args:
            value = kw.get(name)
            if value is not None:
                newkw[name] = byte_size(value)

        return newkw

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

resolve_zeo_uri = ZEOURIResolver()

