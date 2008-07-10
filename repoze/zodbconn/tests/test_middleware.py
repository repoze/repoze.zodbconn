import sys
import unittest

class TestMiddleware(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.zodbconn.middleware import ZODBConnectionMiddleware
        return ZODBConnectionMiddleware

    def _makeOne(self, *arg, **kw):
        klass = self._getTargetClass()
        return klass(*arg, **kw)
    
    def test_ctor(self):
        app = DummyApp()
        db1 = DummyDB()
        db2 = DummyDB()
        registry = DummyRegistry(uri1=db1, uri2=db2)
        name_to_uri_map = {'name1':'uri1', 'name2':'uri2'}
        mw = self._makeOne(app, registry, name_to_uri_map)
        self.assertEqual(mw.app, app)
        databases = mw.databases[:]
        databases.sort()
        self.assertEqual(databases, [('name1', db1), ('name2', db2)])
        self.assertEqual(mw.registry, registry)

    def test_call_noexc(self):
        app = DummyApp(result=['foo'])
        db1 = DummyDB()
        db2 = DummyDB()
        registry = DummyRegistry(uri1=db1, uri2=db2)
        name_to_uri_map = {'name1':'uri1', 'name2':'uri2'}
        mw = self._makeOne(app, registry, name_to_uri_map)
        environ = {}
        result = mw(environ, None)
        self.assertEqual(result, ['foo'])
        conns = app.conns
        for conn in conns:
            self.assertEqual(conn.closed, True)
        from repoze.zodbconn.middleware import _ENV_KEY
        conn_d = environ.get(_ENV_KEY, {})
        self.failIf(conn_d.has_key('name1'))
        self.failIf(conn_d.has_key('name2'))

    def test_call_exc(self):
        app = DummyApp(result=['foo'], exception=ValueError)
        db1 = DummyDB()
        db2 = DummyDB()
        registry = DummyRegistry(uri1=db1, uri2=db2)
        name_to_uri_map = {'name1':'uri1', 'name2':'uri2'}
        mw = self._makeOne(app, registry, name_to_uri_map)
        environ = {}
        self.assertRaises(ValueError, mw, environ, None)
        conns = app.conns
        for conn in conns:
            self.assertEqual(conn.closed, True)
        from repoze.zodbconn.middleware import _ENV_KEY
        conn_d = environ.get(_ENV_KEY, {})
        self.failIf(conn_d.has_key('name1'))
        self.failIf(conn_d.has_key('name2'))

class DummyApp:
    def __init__(self, exception=None, result=()):
        self.exception = exception
        self.result = result
        self.conns = []

    def __call__(self, environ, start_response):
        from repoze.zodbconn.middleware import _ENV_KEY
        self.conns = environ.get(_ENV_KEY, {}).values()
        if self.exception:
            raise self.exception
        return self.result

class DummyConnection:
    closed = False
    def close(self):
        self.closed = True

class DummyDB:
    def open(self):
        return DummyConnection()

class DummyRegistry:
    def __init__(self, **map):
        self.map = map

    def from_uri(self, uri):
        return self.map[uri]

def test_suite():
    return unittest.findTestCases(sys.modules[__name__])

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
