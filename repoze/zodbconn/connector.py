
from repoze.zodbconn.uri import db_from_uri

CONNECTION_KEY = 'repoze.zodbconn.connection'

class Connector:
    """WSGI framework component that opens and closes a ZODB connection.

    Downstream applications will have the connection in the environment,
    normally under the key 'repoze.zodbconn.connection'.
    """
    def __init__(self, next_app, db, key=CONNECTION_KEY):
        self.next_app = next_app
        self.db = db
        self.key = key

    def __call__(self, environ, start_response):
        conn = self.db.open()
        environ[self.key] = conn
        try:
            result = self.next_app(environ, start_response)
            return result
        finally:
            if self.key in environ:
                del environ[self.key]
            conn.close()

def make_app(next_app, global_conf, **local_conf):
    """Make a Connector app.  Expects keyword parameters:

    uri: The database URI or URIs (either a whitespace-delimited string
      or a list of strings)

    key: Optional; the name of the key to put in the WSGI environment
      containing the database connection.
    """
    uri = local_conf['uri']
    db = db_from_uri(uri)
    key = local_conf.get('key', CONNECTION_KEY)
    return Connector(next_app, db, key=key)
