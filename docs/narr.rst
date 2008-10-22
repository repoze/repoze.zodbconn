Resolving URIs
--------------

You can retrieve databases using a URI syntax::

  from repoze.zodbconn.finder import dbfactory_from_uri
  factory = dbfactory_from_uri('zeo://localhost:9991?cache_size=25MB')
  db = factory()

See repoze.zodbconn.resolvers/* for URI syntax resolvers.  Currently
only ZEO and FileStorage resolvers are implemented.

Creating a Root Object
----------------------

You can use the ``PersistentApplicationFinder`` to create and find a
root object in a ZODB for your application.::

   def appmaker(root):
       if not 'myapp' in root:
           myapp = MyApp()
           root['myapp'] = myapp
           import transaction
           transaction.commit()
       return root['myapp']

   from repoze.zodbconn.finder import PersistentApplicationFinder
   finder = PersistentApplicationFinder('zeo://localhost:9991', appmaker)
   environ = {}
   app = finder(environ)
   # When environ dies, the ZODB connection is closed
   del environ
