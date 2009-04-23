import unittest

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

    def _makeOne(self, uri, appmaker):
        klass = self._getTargetClass()
        return klass(uri, appmaker)

    def test_call_no_db(self):
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

    def test_call_with_db(self):
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


class DummyRoot:
    closed = False

class DummyConn:
    closed = False
    def __init__(self, rootob):
        self.rootob = rootob

    def root(self):
        return self.rootob

    def close(self):
        self.rootob.closed = True
        
class DummyDB:
    def __init__(self, rootob, database_name):
        self.conn = DummyConn(rootob)
        self.database_name = database_name

    def open(self):
        return self.conn
    

    
