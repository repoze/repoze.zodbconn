import urlparse
from repoze.zodbconn.resolvers import RESOLVERS

class Cleanup:
    def __init__(self, cleaner):
        self.cleaner = cleaner

    def __del__(self):
        self.cleaner()

class PersistentApplicationFinder:
    db = None

    def __init__(self, uris, appmaker):
        if isinstance(uris, basestring):
            uris = uris.split()
        self.uris = uris
        self.appmaker = appmaker

    def __call__(self, environ):
        if self.db is None:
            databases = {}
            for uri in self.uris:
                dbfactory = dbfactory_from_uri(uri)
                db = dbfactory()
                if db.database_name in databases:
                    raise ValueError("database_name %r already in databases" %
                        db.database_name)
                # link the databases together
                databases[db.database_name] = db
                db.databases = databases
                if self.db is None:
                    # the first database in the list of URIs is the root
                    self.db = db
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

