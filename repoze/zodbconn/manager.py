from repoze.zodbconn.utils import dbfactory_from_uri

class DatabaseManager:
    def __init__(self, factorymaker=dbfactory_from_uri):
        self.factorymaker = factorymaker
        self.databases = {}
        self.keys = {}

    def from_uri(self, uri):
        key = self.keys.get(uri)
        if key is not None:
            return self.databases[key]
        else:
            key, factory = self.factorymaker(uri)
            db = factory()
            self.databases[key] = db
            self.keys[uri] = key
        return db

databases = DatabaseManager()
