import sys
import unittest

class TestRegisterURIResolver(unittest.TestCase):
    def tearDown(self):
        from repoze.zodbconn.utils import _URI_RESOLVERS
        _URI_RESOLVERS.clear()
        
    def _getFUT(self):
        from repoze.zodbconn.utils import register_uri_resolver
        return register_uri_resolver

    def test_it(self):
        register = self._getFUT()
        register('foo', 'bar')
        from repoze.zodbconn.utils import _URI_RESOLVERS
        self.assertEqual(_URI_RESOLVERS['foo'], 'bar')

class TestUnregisterURIResolver(unittest.TestCase):
    def setUp(self):
        from repoze.zodbconn.utils import _URI_RESOLVERS
        _URI_RESOLVERS['foo'] = 'bar'

    def tearDown(self):
        from repoze.zodbconn.utils import _URI_RESOLVERS
        _URI_RESOLVERS.clear()
        
    def _getFUT(self):
        from repoze.zodbconn.utils import unregister_uri_resolver
        return unregister_uri_resolver

    def test_it(self):
        unregister = self._getFUT()
        unregister('foo')
        from repoze.zodbconn.utils import _URI_RESOLVERS
        self.assertEqual(_URI_RESOLVERS, {})

class TestDBFactoryFromURI(unittest.TestCase):
    def setUp(self):
        from repoze.zodbconn.utils import register_uri_resolver
        register_uri_resolver('foo', lambda *arg: ('key', 'factory'))
        
    def tearDown(self):
        from repoze.zodbconn.utils import unregister_uri_resolver
        unregister_uri_resolver('foo')

    def _getFUT(self):
        from repoze.zodbconn.utils import dbfactory_from_uri
        return dbfactory_from_uri

    def test_it(self):
        dbfactory_from_uri = self._getFUT()
        self.assertEqual(dbfactory_from_uri('foo://abc'), ('key', 'factory'))
        self.assertRaises(ValueError, dbfactory_from_uri, 'bar://abc')

def test_suite():
    return unittest.findTestCases(sys.modules[__name__])

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

