import sys
import unittest

class TestZEOURIResolver(unittest.TestCase):
    def _getTargetClass(self):
        from repoze.zodbconn.resolvers.zeo import ZEOURIResolver
        return ZEOURIResolver

    def _makeOne(self):
        klass = self._getTargetClass()
        return klass()

    def test_interpret_zeo_kwargs_noargs(self):
        resolver = self._makeOne()
        kwargs = resolver.interpret_kwargs({})
        self.assertEqual(kwargs, {})

    def test_bytesize_args(self):
        resolver = self._makeOne()
        names = list(resolver._bytesize_args)
        kwargs = {}
        for name in names:
            kwargs[name] = '10MB'
        args = resolver.interpret_kwargs(kwargs)
        keys = args.keys()
        keys.sort()
        self.assertEqual(keys, names)
        for name, value in args.items():
            self.assertEqual(value, 10*1024*1024)

    def test_bool_args(self):
        resolver = self._makeOne()
        f = resolver.interpret_kwargs
        kwargs = f({'read_only':'1'})
        self.assertEqual(kwargs, {'read_only':1})
        kwargs = f({'read_only':'true'})
        self.assertEqual(kwargs, {'read_only':1})
        kwargs = f({'read_only':'on'})
        self.assertEqual(kwargs, {'read_only':1})
        kwargs = f({'read_only':'off'})
        self.assertEqual(kwargs, {'read_only':0})
        kwargs = f({'read_only':'no'})
        self.assertEqual(kwargs, {'read_only':0})
        kwargs = f({'read_only':'false'})
        self.assertEqual(kwargs, {'read_only':0})

    def test_int_args(self):
        resolver = self._makeOne()
        f = resolver.interpret_kwargs
        kwargs = f({'min_disconnect_poll':'500'})
        self.assertEqual(kwargs, {'min_disconnect_poll':500})

    def test_string_args(self):
        resolver = self._makeOne()
        f = resolver.interpret_kwargs
        kwargs = f({'storage':'4'})
        self.assertEqual(kwargs, {'storage': '4'})

    def test_prepare_tcp(self):
        resolver = self._makeOne()
        k, args, kw = resolver.prepare('zeo://localhost:8080?debug=true')
        self.assertEqual(args, (('localhost', 8080),))
        self.assertEqual(kw, {'debug':1})
        self.assertEqual(k, ((('localhost', 8080),), (('debug', 1),)))

    def test_prepare_unix(self):
        resolver = self._makeOne()
        k, args, kw = resolver.prepare('zeo:///var/sock?debug=true')
        self.assertEqual(args, ('/var/sock',))
        self.assertEqual(kw, {'debug':1})
        self.assertEqual(k, (('/var/sock',), (('debug', 1),)))

    def test_call(self):
        resolver = self._makeOne()
        k, factory = resolver('zeo:///var/nosuchfile?wait=false')
        self.assertEqual(k, (('/var/nosuchfile',), (('wait', 0),)))
        from ZEO.ClientStorage import ClientDisconnected
        self.assertRaises(ClientDisconnected, factory)


def test_suite():
    return unittest.findTestCases(sys.modules[__name__])

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
