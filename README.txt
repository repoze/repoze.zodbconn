=================
 repoze.zodbconn
=================

Library which manages ZODB databases.

Middleware which makes a ZODB connection available to downstream
applications.

Library Usage
-------------

You can retrieve databases using a URI syntax.

  from repoze.zodbconn.manager import databases
  db = databases.from_uri('zeo://localhost:9991?cache_size=25MB')
  conn = db.open()

The initial call to ``from_uri`` will create the database.  Subsequent
calls for the same URI will return the created database.

See repoze.zodbconn.resolvers/* for URI syntax resolvers.  Currently
only a ZEO is implemented.

Middleware Usage
----------------

app = <some downstream app>
from repoze.zodbconn.manager import databases
from repoze.zodbconn.middleware import ZODBConnectionMiddleware

  name_to_uri_map = {'conn1':''zeo://localhost:9991', 'conn2':'zeo:///var/sock'}
  middleware = ZODBConnectionMiddleware(app, databases, name_to_uri_map)

When this middleware is placed in the pipeline, an open connection to
each of the databases is placed into the WSGI environment.  In the
above example, the environ will have two repoze.zodbconn-related keys:

  'repoze.zodbconn.conn1' -- A connection to the database on localhost:9991

  'repoze.zodbconn.conn2' -- A connection to the database on /var/sock

The connections are closed automatically by the middleware once the
downstream application has returned (or has raised an exception).

