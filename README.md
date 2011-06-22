
Overview
========

**Profiling and introspection of SQLAlchemy applications.**


Introduction
============

sqltap is a library that allows you to profile and introspect the
queries that your application makes using SQLAlchemy.

sqltap helps you understand:

   * how many times a sql query is executed
   * how much time your sql queries take
   * where your application is issuing sql queries from

Motivation
==========

ORM's are notorious for issuing queries that are not performant or
issuing far more queries than necessary. sqltap gives you flexible
visibility into how your application is using SQLAlchemy so you can
find and fix these problems with minimal effort.


Simple Example
--------------

This is the bare minimum you need to start profiling your application

       sqltap.start()
       session.Query(Knights).filter(who_say = 'Ni').fetchall()
       statistics = sqltap.collect()
       sqltap.report(statistics, "report.html")


Advanced Features
-----------------

sqltap provides the notion of a context function which lets you
associate arbitrary data with each query as it is issued by
sqlalchemy. For example, in a web framework, you may want to associate
each query with the current request or page type so that you can
easily aggregate statistics over those criteria later.

       def on_application_start():
           # Associate the current path, and request identifier with the
           # query statistics.
           def context_fn(*args):
               return (framework.current_request().path,
                       framework.current_request().id)

           sqltap.start(user_context_fn = context_fn)

       def after_request():
           # Get all of the statistics for this request
           def filter_fn(qstats):
               return qstats.user_context[1] == framework.current_request()

           statistics = sqltap.collect(filter_fn)
           sqltap.report(statistics, "report.html")


       def once_per_day():
           # Once per day, aggregate all of the query stats
           all_paths = ["/Books", "/Movies", "/User", "/Account"]

           # Get all of the statistics for each page type
           for path in all_paths:
               def filter_fn(qstats):
                   return qstats.user_context[0].startswith(path)
               statistics = sqltap.collect(filter_fn, and_purge = True)
               sqltap.report(statistics, "%s-report.html" % path[1:])


sqltap
======

sqltap.start(engine=sqlalchemy.engine.base.Engine, user_context_fn=None)

   Start sqltap profiling

   You may call this function when sqltap is already profiling to add
   another engine to be profiled or to replace the user_context_fn
   function.

   Calling start on an engine that is already being profiled has no
   effect.

   Parameters:

   * **engine** -- The sqlalchemy engine on which you want to
    profile queries. The default is sqlalchemy.engine.Engine which
    will profile queries across all engines.
   * **user_context_fn** -- A function which returns a value to be
    stored with the query statistics. The function takes the same
    parameters  passed to the after_execute event in sqlalchemy:
    (conn, clause, multiparams, params, results)

sqltap.stop(engine=sqlalchemy.engine.base.Engine)

   Stop sqltap profiling

   Parameters:
      **engine** -- The sqlalchemy engine on which you want to stop
      profiling queries. The default is sqlalchemy.engine.Engine which
      will stop profiling queries across all engines.

sqltap.collect(filter_fn=None, and_purge=False)

   Collect query statstics from sqltap.

   Parameters:

   * **filter_fn** -- A function which takes a ``QueryStats``
    object  and returns *True* if the ``QueryStats`` object should
    be  collected. If *filter_fn* is *None*, all stats are
    collected.
   * **and_purge** -- If True, purges all of the stats records that
    are collected.

   Returns:
      A list of ``QueryStats`` objects.

sqltap.purge(filter_fn=None)

   Remove query statistics from sqltap.

   Parameters:
      **filter_fn** -- A function which takes a ``QueryStats`` object
      and returns *True* if the ``QueryStats`` object should be
      purged. If *filter_fn* is *None*, all stats are purged.

sqltap.report(statistics, filename=None)

   Generate an HTML report of query statistics.

   Parameters:

   * **statistics** -- An iterable of ``QueryStats`` objects over
    which to prepare a report. This is typically a list returned
    by a call to ``collect()``.
   * **filename** -- If present, additionally write the html report
    out  to a file at the specified path.

   Returns:
      The generated HTML report.

class class sqltap.QueryStats(text, stack, duration, user_context)

   Statistics about a query

   You should not create these objects, but your application may
   choose inspect them in the filter functions you pass to
   ``sqltap.collect()`` and ``sqltap.purge()``.

   Attr text:
      The text of the query

   Attr stack:
      The stack trace when this query was issued. Formatted as
      returned by py:func:*traceback.extract_stack*

   Attr duration:
      Duration of the query in seconds.

   Attr user_context:
      The value returned by the user_context_fn set with
      ``sqltap.start()``.


sqltap.ctx
==========

sqltap.ctx.profile(engine=sqlalchemy.engine.base.Engine, user_context_fn=None)

   Convenience context manager for profiling sqlalchemy queries.

   It takes the same arguments as sqltap.start


sqltap.dec
==========

sqltap.dec.profile(engine=sqlalchemy.engine.base.Engine, user_context_fn=None)

   Convenience decorator for profiling sqlalchemy queries.

   See ``sqltap.start()`` for parameter information.

   Example usage:

      @sqltap.dec.profile
      def holy_hand_grenade():
          for number in Session.query(Numbers).filter(Numbers.value <= 3):
              print number
