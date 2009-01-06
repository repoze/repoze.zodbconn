import urlparse
from repoze.zodbconn.resolvers import RESOLVERS

class Cleanup:
    def __init__(self, cleaner):
        self.cleaner = cleaner

    def __del__(self):
        self.cleaner()

class PersistentApplicationFinder:
    db = None
    def __init__(self, uri, appmaker):
        self.uri = uri
        self.appmaker = appmaker

    def __call__(self, environ):
        if self.db is None:
            dbfactory = dbfactory_from_uri(self.uri)
            self.db = dbfactory()
        conn = self.db.open()
        root = conn.root()
        app = self.appmaker(root)
        environ['repoze.zodbconn.closer'] = Cleanup(conn.close)
        return app

def dbfactory_from_uri(uri):
    (scheme, netloc, path, query, frag) = urlparse.urlsplit(uri)
    resolver =  RESOLVERS.get(scheme)
    if resolver is None:
        raise ValueError('Unresolveable URI %s' % uri)
    _, _, _, dbfactory = resolver(uri)
    return dbfactory

