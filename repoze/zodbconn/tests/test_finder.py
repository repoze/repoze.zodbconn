import unittest

class TestSimpleCleanup(unittest.TestCase):

    def _getTargetClass(self):
        from repoze.zodbconn.finder import SimpleCleanup
        return SimpleCleanup

    def _makeOne(self, cleaner, environ):
        return self._getTargetClass()(cleaner, environ)

    def test___del___calls_cleaner(self):
        root = DummyRoot()
        conn = DummyConn(root)
        environ = {}
        cleanup = self._makeOne(conn, environ)
        del cleanup
        self.failUnless(root.closed)

class TestLoggingCleanup(unittest.TestCase):

    def _getTargetClass(self):
        from repoze.zodbconn.finder import LoggingCleanup
        return LoggingCleanup

    def _makeOne(self, cleaner, environ):
        return self._getTargetClass()(cleaner, environ)

    def test___del___calls_cleaner_and_logs_no_qs(self):
        logger = DummyLogger()
        root = DummyRoot()
        conn = DummyConn(root)
        environ = {'REQUEST_METHOD': 'GET',
                   'PATH_INFO': '/test',
                  }
        cleanup = self._makeOne(conn, environ)
        cleanup.logger = logger
        del cleanup
        self.failUnless(root.closed)
        self.assertEqual(len(logger._wrote), 1)
        self.assertEqual(logger._wrote[0], '"GET","/test",0,0\n')

    def test___del___calls_cleaner_and_logs_w_qs(self):
        logger = DummyLogger()
        root = DummyRoot()
        conn = DummyConn(root)
        environ = {'REQUEST_METHOD': 'GET',
                   'PATH_INFO': '/test',
                   'QUERY_STRING': 'foo=bar',
                  }
        cleanup = self._makeOne(conn, environ)
        cleanup.logger = logger
        del cleanup
        self.failUnless(root.closed)
        self.assertEqual(len(logger._wrote), 1)
        self.assertEqual(logger._wrote[0], '"GET","/test?foo=bar",0,0\n')

_marker = object()

class TestPersistentApplicationFinder(unittest.TestCase):
    def setUp(self):
        from repoze.zodbconn.resolvers import RESOLVERS
        self.root = DummyRoot()
        self.db = DummyDB(self.root, 'foo')
        def dbfactory():
            return self.db
        RESOLVERS['foo'] = lambda *arg: ('key', 'arg', 'kw', dbfactory)
        def addon_dbfactory():
            return DummyDB(DummyRoot(), 'addon')
        RESOLVERS['addon'] = lambda *arg: ('key', 'arg', 'kw', addon_dbfactory)

    def tearDown(self):
        from repoze.zodbconn.resolvers import RESOLVERS
        del RESOLVERS['foo']

    def _getTargetClass(self):
        from repoze.zodbconn.finder import PersistentApplicationFinder
        return PersistentApplicationFinder

    def _makeOne(self, uri, appmaker, cleanup=_marker):
        klass = self._getTargetClass()
        if cleanup is _marker:
            return klass(uri, appmaker)
        return klass(uri, appmaker, cleanup)

    def test_ctor_no_cleanup(self):
        from repoze.zodbconn.finder import SimpleCleanup
        def makeapp(root):
            pass
        finder = self._makeOne('foo://bar.baz', makeapp)
        self.assertEqual(finder.uris, ['foo://bar.baz'])
        self.assertEqual(finder.appmaker, makeapp)
        self.failUnless(finder.cleanup is SimpleCleanup)

    def test_ctor_w_cleanup(self):
        def makeapp(root):
            pass
        def cleanup(conn, environ):
            pass
        finder = self._makeOne('foo://bar.baz', makeapp, cleanup)
        self.assertEqual(finder.uris, ['foo://bar.baz'])
        self.assertEqual(finder.appmaker, makeapp)
        self.failUnless(finder.cleanup is cleanup)

    def test_call_no_db_no_cleanup(self):
        def makeapp(root):
            root.made = True
            return 'abc'
        finder = self._makeOne('foo://bar.baz', makeapp)
        environ = {}
        app = finder(environ)
        self.assertEqual(app, 'abc')
        self.assertEqual(self.root.made, True)
        self.assertEqual(self.root.closed, False)
        del environ['repoze.zodbconn.closer']
        self.assertEqual(self.root.closed, True)
        self.assertEqual(finder.db, self.db)

    def test_call_no_db_w_cleanup(self):
        def makeapp(root):
            root.made = True
            return 'abc'
        finder = self._makeOne('foo://bar.baz', makeapp, DummyCleanup)
        environ = {}
        app = finder(environ)
        self.assertEqual(app, 'abc')
        self.assertEqual(self.root.made, True)
        self.assertEqual(self.root.closed, False)
        self.assertEqual(environ['XXX'], None)
        del environ['repoze.zodbconn.closer']
        self.assertEqual(self.root.closed, True)
        self.assertEqual(finder.db, self.db)

    def test_call_with_db_no_cleanup(self):
        def makeapp(root):
            root.made = True
            return 'abc'
        finder = self._makeOne('another://bar.baz', makeapp)
        finder.db = DummyDB(self.root, 'another')
        environ = {}
        app = finder(environ)
        self.assertEqual(app, 'abc')
        self.assertEqual(self.root.made, True)
        self.assertEqual(self.root.closed, False)
        del environ['repoze.zodbconn.closer']
        self.assertEqual(self.root.closed, True)

    def test_call_with_db_w_cleanup(self):
        def makeapp(root):
            root.made = True
            return 'abc'
        finder = self._makeOne('another://bar.baz', makeapp, DummyCleanup)
        finder.db = DummyDB(self.root, 'another')
        environ = {}
        app = finder(environ)
        self.assertEqual(app, 'abc')
        self.assertEqual(self.root.made, True)
        self.assertEqual(self.root.closed, False)
        self.assertEqual(environ['XXX'], None)
        del environ['repoze.zodbconn.closer']
        self.assertEqual(self.root.closed, True)

    def test_multiple_databases(self):
        def makeapp(root):
            root.made = True
            return 'abc'
        finder = self._makeOne('foo://bar.baz addon://', makeapp)
        environ = {}
        app = finder(environ)
        self.assertEqual(app, 'abc')
        self.assertEqual(self.root.made, True)
        self.assertEqual(self.root.closed, False)

        self.assertEqual(finder.db, self.db)
        self.assertTrue('addon' in finder.db.databases)
        self.assertTrue('foo' in finder.db.databases)
        self.assertEqual(finder.db.databases,
            finder.db.databases['addon'].databases)

        del environ['repoze.zodbconn.closer']
        self.assertEqual(self.root.closed, True)

    def test_disallow_duplicate_database_name(self):
        def makeapp(root):
            return 'abc'
        finder = self._makeOne('foo://bar.baz foo://bar.baz', makeapp)
        environ = {}
        self.assertRaises(ValueError, finder, environ)

class TestDBFactoryFromURI(unittest.TestCase):
    def setUp(self):
        from repoze.zodbconn.resolvers import RESOLVERS
        RESOLVERS['foo'] = lambda *arg: ('key', 'arg', 'kw', 'factory')

    def tearDown(self):
        from repoze.zodbconn.resolvers import RESOLVERS
        del RESOLVERS['foo']

    def _getFUT(self):
        from repoze.zodbconn.finder import dbfactory_from_uri
        return dbfactory_from_uri

    def test_it(self):
        dbfactory_from_uri = self._getFUT()
        self.assertEqual(dbfactory_from_uri('foo://abc'), 'factory')
        self.assertRaises(ValueError, dbfactory_from_uri, 'bar://abc')


class DummyRoot:
    closed = False

class DummyConn:
    closed = False
    _loads = _saves = 0

    def __init__(self, rootob):
        self.rootob = rootob

    def root(self):
        return self.rootob

    def close(self):
        self.rootob.closed = True

    def getTransferCounts(self):
        return self._loads, self._saves

class DummyCleanup:
    def __init__(self, conn, environ):
        self.conn = conn
        environ['XXX'] = None
    def __del__(self):
        self.conn.close()

class DummyDB:
    def __init__(self, rootob, database_name):
        self.conn = DummyConn(rootob)
        self.database_name = database_name

    def open(self):
        return self.conn

class DummyLogger:
    def __init__(self):
        self._wrote = []

    def write(self, chunk):
        self._wrote.append(chunk)
