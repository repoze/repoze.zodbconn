Resolving URIs
--------------

You can retrieve databases using a URI syntax::

  from repoze.zodbconn.uri import db_from_uri
  db = db_from_uri('zeo://localhost:9991?cache_size=25MB')

The URI schemes currently recognized are ``file://``, ``zeo://``, and
``zconfig://``.

``file://`` URI scheme
~~~~~~~~~~~~~~~~~~~~~~

The ``file://`` URI scheme can be passed to ``db_from_uri`` to
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

The ``zeo://`` URI scheme can be passed to ``db_from_uri`` to
create a ZODB ClientStorage database factory. Either the host and port
parts of this scheme should point at a hostname/portnumber combination
e.g.:

  zeo://localhost:7899

Or the path part should point at a UNIX socket name::

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

``zconfig://`` URI scheme
~~~~~~~~~~~~~~~~~~~~~~~~~

The ``zconfig://`` URI scheme can be passed to ``db_from_uri`` to
create any kind of storage that ZODB can load via ZConfig. The path
info section of this scheme should point at a ZConfig file on the
filesystem. Use an optional fragment identifier to specify which
database to open. This URI scheme does not use query string parameters.

Examples
++++++++

An example ZConfig file::

    <zodb>
      <mappingstorage>
      </mappingstorage>
    </zodb>

If that configuration file is located at /etc/myapp/zodb.conf, use the
following URI to open the database::

    zconfig:///etc/myapp/zodb.conf

A ZConfig file can specify more than one database.  For example::

    <zodb temp1>
      <mappingstorage>
      </mappingstorage>
    </zodb>
    <zodb temp2>
      <mappingstorage>
      </mappingstorage>
    </zodb>

In that case, use a URI with a fragment identifier::

    zconfig:///etc/myapp/zodb.conf#temp1


Multi-Database Support
----------------------

You can connect to multiple ZODB databases by providing a list of URIs,
or a series of URIs separated by whitespace, when calling
``db_from_uris``. Multi-databases allow you to apply different data
management policies for different kinds of data; for example, you might
store session data in a more volatile database.

The first URI in the list specifies the root database. Each URI must
have a distinct and explicit ``database_name``. The ``database_name``
is used in all cross-database references, so do not change the
``database_name`` once you have stored data, or you will break the
references.

An example multi-database application::

   from repoze.zodbconn.uri import db_from_uri
   uris = []
   uris.append('zeo://localhost:9991/?database_name=main&storage=main')
   uris.append('zeo://localhost:9991/?database_name=catalog&storage=catalog')
   db = db_from_uris(uris)
   conn = db.open()
   root = conn.root()

In this example, ``root`` is an object in the database named ``main``,
since that ``main`` database is listed first in the URIs.


Connecting to ZODB in a WSGI Pipeline
-------------------------------------

This package provides a WSGI framework component,
``repoze.zodbconn#connector``, that opens a ZODB connection for
downstream WSGI applications, and unconditionally closes the connection
on the way out. The connection is normally stored in the WSGI
environment under the key ``repoze.zodbconn.connection``.

Here is a sample Paste Deploy configuration file that includes a
ZODB connector::

    [DEFAULT]
    zodb_uri = zeo://localhost:9001

    [pipeline:main]
    pipeline =
        egg:repoze.zodbconn#connector
        egg:repoze.retry#retry
        egg:repoze.tm2#tm
        egg:myapp

    [server:main]
    use = egg:Paste#http
    host = 0.0.0.0
    port = 8080

Note that the ZODB connector does not commit or abort transactions. You
should use ``repoze.tm2`` or ``repoze.tm`` to manage transactions. The
example above shows the recommended ordering of a ZODB connector,
``repoze.retry``, and ``repoze.tm2`` in a pipeline.

The parameters for the ZODB connector are:

zodb_uri
  The ZODB URI or URIs.  Separate URIs with whitespace.  This can be
  either a local or global configuration parameter.
connection_key
  The key to put in the WSGI environment.  Defaults to
  ``repoze.zodbconn.connection``.


Helper: Creating a Root Object
------------------------------

A higher-level API to using the ``repoze.zodbconn`` package allows you
to create a "root factory".  You can use the
``PersistentApplicationFinder`` helper to create and find a root
object in a ZODB for your application.

.. code-block:: python

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

If a ZODB connection already exists in the environment passed to
``PersistentApplicationFinder``, that ZODB connection will be used
instead of opening a new connection.  If you want to prevent
``PersistentApplicationFinder`` from getting the connection from the
environment, add the parameter ``connection_key=None`` when
creating the finder.


Customizing Connection Cleanup
------------------------------

The ``PersistentApplicationFinder`` helper takes an optional ``cleanup``
argument, which should serve as a factory for an object which will be
stored in the WSGI environment:

- The factory will be called with two arguments, ``conn`` (the opened
  ZODB connection) and ``environ`` (the WSGI environment).

- The returned object **must not** hold a reference to ``environ``,
  as its purpose is to have its ``__del__`` method called when the
  ``environ`` is destroyed:  holding a reference would create a potentially
  uncollectable cycle.  Instead, the object could store particular values
  computed from the environment (e.g., the ``PATH_INFO``).

- The returned object **must** contrive to close ``conn`` in its ``__del__``
  method;  typically, this means that the returned object holds a reference
  to the connection or to its ``close`` method.  The ``__del__`` method
  **may** perform other work, but **must not** raise any exception.

**Note**: The ``cleanup`` parameter will be **ignored** when
``PersistentApplicationFinder`` gets its connection from the
environment, so don't use the ``cleanup`` parameter in a WSGI pipeline
that includes a ZODB connector (``repoze.zodbconn#connector``).
Instead, create WSGI framework components that use the open connection
in the environment.

The default cleanup implementation, ``repoze.zodbcon.finder:SimpleCleanup``,
just closes the connection.  An alternate cleanup implementation,
``repoze.zodbcon.finder:LoggingCleanup``, logs the number of objects loaded
and stored for each request to a CSV file, e.g.::

   "GET","/test.html",12,0
   "POST","/edit.html",0,3

To use this cleanup, you need to do two things:

- Arrange for an writable file-like object to be present in the WSGI
  environment under the key, ``repoze.zodbcon.loadsave``.

- Pass the logging cleanup class to the
  ``PersistentApplicationFinder``. E.g.:

.. code-block:: python

    import your.package
    from repoze.bfg.router import make_app as bfg_make_app
    from repoze.zodbconn.finder import PersistentApplicationFinder
    from repoze.zodbconn.finder import LoggingCleanup
    from your.package.models import appmaker

    def make_app(global_config, zodb_uri, **kw):
        logfile = kw.get('connection_log_file')
        if logfile is not None:
            logger = open(logfile, 'a')
        else:
            logger = None

        def _makeCleanup(conn, environ):
            cleanup = LoggingCleanup(conn, environ)
            cleanup.logger = logger
            return cleanup

        get_root = PersistentApplicationFinder(zodb_uri, appmaker,
                                               _makeCleanup)

        app = bfg_make_app(get_root, your.package, options=kw)
        return app


Other WSGI Framework Components
-------------------------------

closer: Close a Connection
~~~~~~~~~~~~~~~~~~~~~~~~~~

If you use the ``PersistentApplicationFinder`` class without a ZODB
connector in the pipeline, the finder inserts a key in the environment
which is a "closer". When the environment is garbage collected, the
closer will usually be called. If you're having problems with this (the
environment is not garbage collected, for some reason, for instance),
you can use the "closer" middleware at the top of your pipeline::

  egg:repoze.zodbconn#closer

This will cause the key to be deleted explicitly rather than relying on
garbage collection.

You should not need the closer middleware in a WSGI pipeline that uses
a ZODB connector (``repoze.zodbconn#connector``).

cachecleanup: Control the Contents of the ZODB Cache
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This package includes a WSGI framework component that helps control the
size of the ZODB cache (which often dominates ZODB application RAM
consumption) by keeping only the state of certain objects in the cache.
To include it in your pipeline, use this entry point::

    egg:repoze.zodbconn#cachecleanup

Next, use the ``class_regexes`` parameter to specify regular
expressions that match the class names of objects you want to keep in
the cache. Class names are composed of the class module name, a colon
(``:``), and the class name. For example, the regular expression
``BTrees`` matches objects of any class in the BTrees package, while
``repoze.catalog.catalog:Catalog`` matches only Repoze Catalog objects.

An example pipeline that includes a cache cleanup component::

    [DEFAULT]
    zodb_uri = zeo://localhost:9001

    [filter:cachecleanup]
    use = egg:repoze.zodbconn#cachecleanup
    class_regexes = BTrees
                    zope.index
                    repoze.catalog

    [pipeline:main]
    pipeline =
        egg:repoze.zodbconn#connector
        cachecleanup
        egg:repoze.retry#retry
        egg:repoze.tm2#tm
        egg:myapp

    [server:main]
    use = egg:Paste#http
    host = 0.0.0.0
    port = 8080

The cache cleanup component requires a ZODB connection to exist in the
environment.

transferlog: Log ZODB loads and stores
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use the ``transferlog`` component to identify URIs that cause ZODB to
load or store a lot of objects. This component provides the same
functionality as the ``LoggingCleanup`` class mentioned above, but it
is compatible with the ``connector`` component
(``repoze.zodbconn#connector``) and can be configured without writing
code.  To include it in your pipeline, use this entry point::

    egg:repoze.zodbconn#transferlog

Provide a ``filename`` parameter that points to a writable log file.

