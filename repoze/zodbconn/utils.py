import urlparse

_URI_RESOLVERS = {}

def register_uri_resolver(scheme, resolver):
    _URI_RESOLVERS[scheme] = resolver

def unregister_uri_resolver(scheme):
    del _URI_RESOLVERS[scheme]

def dbfactory_from_uri(uri):
    (scheme, netloc, path, query, frag) = urlparse.urlsplit(uri)
    resolver =  _URI_RESOLVERS.get(scheme)
    if resolver is None:
        raise ValueError('Unresolveable URI %s' % uri)
    return resolver(uri)
