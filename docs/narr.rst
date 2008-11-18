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

Middleware to Close a Connection
--------------------------------

If you use the ``PersistentApplicationFinder`` class, it inserts a key
in the environment which is a "closer".  When the environment is
garbage collected, the closer will usually be called.  If you're
having problems with this (the environment is not garbage collected,
for some reason, for instance), you can use the "closer" middleware at
the top of your pipeline::

  egg:repoze.zodbconn#closer

This will cause the key to be deleted explicitly rather than relying
on garbage collection.

