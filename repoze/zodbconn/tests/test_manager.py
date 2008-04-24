import sys
import unittest

class TestDatabaseManager(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.zodbconn.manager import DatabaseManager
        return DatabaseManager

    def _makeOne(self, factorymaker):
        klass = self._getTargetClass()
        return klass(factorymaker)

    def test_from_uri(self):
        manager = self._makeOne(dummy_factorymaker)
        db = manager.from_uri('uri')
        self.assertEqual(db, dummydb)
        self.assertEqual(manager.databases['key'], db)
        self.assertEqual(manager.keys['uri'], 'key')

    def test_from_uri_cached(self):
        manager = self._makeOne(None)
        manager.keys['uri'] = 'key'
        manager.databases['key'] = dummydb
        db = manager.from_uri('uri')
        self.assertEqual(db, dummydb)
        
class DummyDB:
    pass

dummydb = DummyDB()        

def dummyfactory():
    return dummydb

def dummy_factorymaker(uri):
    return 'key', dummyfactory

def test_suite():
    return unittest.findTestCases(sys.modules[__name__])

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

