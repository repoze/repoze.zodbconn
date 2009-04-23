Resolving URIs
--------------

You can retrieve databases using a URI syntax::

  from repoze.zodbconn.finder import dbfactory_from_uri
  factory = dbfactory_from_uri('zeo://localhost:9991?cache_size=25MB')
  db = factory()

Currently only ``file://`` and ``zeo://`` URI schemes are recognized.

``file://`` URI scheme
~~~~~~~~~~~~~~~~~~~~~~

The ``file://`` URI scheme can be passed to ``dbfactory_from_uri`` to
create a ZODB FileStorage database factory.  The path info section of
this scheme should point at a filesystem file path that should contain
the filestorage data.  For example::

  file:///my/absolute/path/to/Data.fs

The URI scheme also accepts query string arguments.  The query string
arguments honored by this scheme are as follows.

FileStorage constructor related
+++++++++++++++++++++++++++++++

These arguments generally inform the FileStorage constructor about
values of the same names.

create
  boolean
read_only
  boolean
quota
  bytesize

Database-related
++++++++++++++++

These arguments relate to the database (as opposed to storage)
settings.

database_name
  string

Connection-related
++++++++++++++++++

These arguments relate to connections created from the database.

connection_cache_size
  integer (default 10000)
connection_pool_size
  integer (default 7)

Blob-related
++++++++++++

If these arguments exist, they control the blob settings for this
storage.

blobstorage_dir
  string
blobstorage_layout
  string

Misc
++++

demostorage 
  boolean (if true, wrap FileStorage in a DemoStorage)

Example
+++++++

An example that combines a path with a query string::

   file:///my/Data.fs?connection_cache_size=100&blobstorage_dir=/foo/bar

``zeo://`` URI scheme
~~~~~~~~~~~~~~~~~~~~~~

The ``zeo://`` URI scheme can be passed to ``dbfactory_from_uri`` to
create a ZODB ClientStorage database factory.  The path info section
of this scheme should either point at a hostname/portnumber
combination e.g.:

  zeo:///localhost:7899

Or a UNIX socket name::

  zeo:///path/to/zeo.sock

The URI scheme also accepts query string arguments.  The query string
arguments honored by this scheme are as follows.

ClientStorage-constructor related
+++++++++++++++++++++++++++++++++

These arguments generally inform the ClientStorage constructor about
values of the same names.

storage
  string
cache_size
  bytesize
name
  string
client
  string
debug
  boolean
var
  string
min_disconnect_poll
  integer
max_disconnect_poll
  integer
wait
  boolean
wait_timeout
  integer
read_only
  boolean
read_only_fallback
  boolean
username
  string
password
  string
realm
  string
blob_dir
  string
shared_blob_dir
  boolean

Misc
++++

demostorage
  boolean (if true, wrap ClientStorage in a DemoStorage)

Connection-related
++++++++++++++++++

These arguments relate to connections created from the database.

connection_cache_size
  integer (default 10000)
connection_pool_size
  integer (default 7)

Database-related
++++++++++++++++

These arguments relate to the database (as opposed to storage)
settings.

database_name
  string

Example
+++++++

An example that combines a path with a query string::

  zeo://localhost:9001?connection_cache_size=20000

Helper: Creating a Root Object
------------------------------

A higher-level API to using the ``repoze.zodbconn`` package allows you
to create a "root factory".  You can use the
``PersistentApplicationFinder`` helper to create and find a root
object in a ZODB for your application::

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

You can connect to multiple ZODB databases by providing a list of URIs,
or a series of URIs separated by whitespace, when creating the
``PersistentApplicationFinder``. Multi-databases allow you to apply
different data management policies for different kinds of data; for
example, you might decide to put a catalog structure in a database with
a large cache limit.

The first URI in the list specifies the root database, meaning the
database that contains the root object passed to the ``appmaker``
callback. Each URI must have a distinct ``database_name``. The
``database_name`` is used in all cross-database references, so do not
change the ``database_name`` once you have stored data, or you will
break the references.

An example multi-database application::

   def appmaker(root):
       if not 'myapp' in root:
           myapp = MyApp()
           root['myapp'] = myapp

           # put the catalog in the catalog database
           catalog = MyCatalog()
           catalog_conn = root._p_jar.get_connection('catalog')
           catalog_conn.root()['catalog'] = catalog
           catalog_conn.add(catalog)

           # make a cross-database reference from myapp to the catalog
           myapp.catalog = catalog

           import transaction
           transaction.commit()
       return root['myapp']

   from repoze.zodbconn.finder import PersistentApplicationFinder
   uris = []
   uris.append('zeo://localhost:9991/?database_name=main&storage=main')
   uris.append('zeo://localhost:9991/?database_name=catalog&storage=catalog')
   finder = PersistentApplicationFinder(uris, appmaker)
   environ = {}
   app = finder(environ)

Application code does not need to do anything special to follow
cross-database references. In the example above, other code can refer
to ``myapp.catalog`` without knowing that a database boundary is being
crossed.

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

