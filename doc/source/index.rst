.. sqltap documentation master file, created by
   sphinx-quickstart on Thu Jun 16 23:52:52 2011.

SQLTap - profiling and introspection for SQLAlchemy applications
================================================================


.. image:: images/sqltap-report-example.png
    :align: center
    :height: 500px


Introduction
------------

sqltap is a library that allows you to profile and introspect
the queries that your application makes using SQLAlchemy.

sqltap helps you understand:
    - how many times a sql query is executed
    - how much time your sql queries take
    - where your application is issuing sql queries from

Motivation
----------
When you work at a high level of abstraction, it's more common for your
code to be inefficient and cause performance problems. SQLAlchemy's ORM
is excellent and gives you the flexibility to fix these inefficiencies
if you know where to look! sqltap is a library that hooks into SQLAlchemy
to collect metrics on all queries you send to your databases. sqltap
can help you find where in your application you are generating slow or
redundant queries so that you can fix them with minimal effort.

Simple Example
^^^^^^^^^^^^^^
This is the bare minimum you need to start profiling your application

::

    profiler = sqltap.start()
    session.query(Knights).filter_by(who_say = 'Ni').all()
    statistics = profiler.collect()
    sqltap.report(statistics, "report.html")


Advanced Features
^^^^^^^^^^^^^^^^^
sqltap provides the notion of a context function which lets you associate
arbitrary data with each query as it is issued by sqlalchemy. For example,
in a web framework, you may want to associate each query with the current
request or page type so that you can easily aggregate statistics over
those criteria later.

::

    def context_fn(*args):
        """ Associate the request path, unique id with each query statistic """
        return (framework.current_request().path,
                framework.current_request().id)

    # start the profiler immediately
    profiler = sqltap.start(user_context_fn=context_fn)

    def generate_reports():
        """ call this at any time to generate query reports reports """
        all_stats = []
        per_request_stats = collections.defaultdict(list)
        per_page_stats = collections.defaultdict(list)

        qstats = profiler.collect()
        for qs in qstats:
            all_stats.append(qs)

            page = qstats.user_context[0]
            per_page_stats[page].append(qs)

            request_id = qstats.user_context[1]
            per_request_stats[request_id].append(qs)

        # report with all queries
        sqltap.report(all_stats, "report_all.html")

        # a report per page
        for page, stats:
            sqltap.report(stats, "report_page_%s.html" % page)

        # a report per request
        for request_id, stats:
            sqltap.report(stats, "report_request_%s.html" % request_id)

Modules
=======

sqltap
----------------------------------
.. automodule:: sqltap
   :members: start, ProfilingSession, report, QueryStats

sqltap.wsgi
----------------------------------
.. automodule:: sqltap.wsgi
   :members:

