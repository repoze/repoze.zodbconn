
from repoze.zodbconn.uri import db_from_uri
from repoze.zodbconn.connector import CONNECTION_KEY

class SimpleCleanup:
    def __init__(self, conn, environ):
        # N.B.:  do *not* create a cycle by holding on to 'environ'!
        self.cleaner = conn.close

    def __del__(self):
        self.cleaner()

class LoggingCleanup:
    logger = None

    def __init__(self, conn, environ):
        # N.B.:  do *not* create a cycle by holding on to 'environ'!
        self.conn = conn
        self.request_method = environ['REQUEST_METHOD']
        self.path_info = environ['PATH_INFO']
        self.query_string = environ.get('QUERY_STRING')
        self.loads_before, self.stores_before = conn.getTransferCounts()

    #############  WAAAAAAAAAAA!!!!!!########################################
    # For some insane reason, the coverage module thinks this entire method
    # is uncovered, in spite of the fact that the passing unit tests prove
    # that both code paths get executed.
    #########################################################################
    def __del__(self): #pragma NO COVERAGE
        loads_after, stores_after = self.conn.getTransferCounts()
        self.conn.close()
        if self.logger is not None:
            if self.query_string:
                url = '%s?%s' % (self.path_info, self.query_string)
            else:
                url = self.path_info
            loads = loads_after - self.loads_before
            stores = stores_after - self.stores_before
            self.logger.write('"%s","%s",%d,%d\n'
                                % (self.request_method, url, loads, stores))

class PersistentApplicationFinder:
    db = None

    def __init__(self, uri, appmaker, cleanup=None):
        if uri:
            if cleanup is None:
                cleanup = SimpleCleanup
        else:
            # If the URI is empty, get the ZODB connection from the
            # WSGI environment. In this mode, we must not use any
            # cleanup function, because that would cause the ZODB
            # connection to be closed twice, leading to nasty
            # multithreading bugs. (The connection can be reopened by
            # other threads immediately after close() is called.)
            if cleanup:
                raise TypeError(
                    "cleanup must not be provided when URI is empty")
        self.uri = uri
        self.appmaker = appmaker
        self.cleanup = cleanup

    def __call__(self, environ):
        if self.uri:
            if self.db is None:
                self.db = db_from_uri(self.uri)
            conn = self.db.open()
        else:
            conn = environ[CONNECTION_KEY]
        root = conn.root()
        app = self.appmaker(root)
        if self.cleanup:
            environ['repoze.zodbconn.closer'] = self.cleanup(conn, environ)
        return app
