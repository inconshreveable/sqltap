import sqlalchemy.engine, sqlalchemy.event
import traceback, time, threading, collections, sys, mako.template, os

_local = threading.local()
_engines = {}

class QueryStats:
    """ Statistics about a query

    You should not create these objects, but your application may choose
    inspect them in the filter functions you pass to :func:`sqltap.collect`
    and :func:`sqltap.purge`.
    
    :attr text: The text of the query
    :attr stack: The stack trace when this query was issued. Formatted as
        returned by py:func:`traceback.extract_stack`
    :attr duration: Duration of the query in seconds.
    :attr user_context: The value returned by the user_context_fn set 
        with :func:`sqltap.start`.
    """
    def __init__(self, text, stack, duration, user_context):
        self.text = text
        self.stack = stack
        self.duration = duration
        self.user_context = user_context

def start(engine = sqlalchemy.engine.Engine, user_context_fn = None):
    """ Start sqltap profiling

    You may call this function when sqltap is already profiling to
    add another engine to be profiled or to replace the user_context_fn
    function. 

    Calling start on an engine that is already being profiled
    has no effect.

    :param engine: The sqlalchemy engine on which you want to
        profile queries. The default is sqlalchemy.engine.Engine
        which will profile queries across all engines.

    :param user_context_fn: A function which returns a value to be stored
        with the query statistics. The function takes the same parameters 
        passed to the after_execute event in sqlalchemy: 
        (conn, clause, multiparams, params, results)
    """
    sqlalchemy.event.listen(engine, "before_execute", _before_exec)
    sqlalchemy.event.listen(engine, "after_execute", _after_exec)
    _engines[engine] = user_context_fn

def stop(engine = sqlalchemy.engine.Engine):
    """ Stop sqltap profiling

    Please note that because SQLAlchemy does not yet support removing event
    handlers, sqltap will continue to catch events from SQLAlchemy, even
    though it will not store information on any queries related to those
    events.

    :param engine: The sqlalchemy engine on which you want to
        stop profiling queries. The default is sqlalchemy.engine.Engine
        which will stop profiling queries across all engines.


        **WARNING**: Specifying sqlalchemy.engine.Engine will only stop
        profiling across all engines that you have not explicitly passed
        to `sqltap.start`. For example the following will work as expected
        ::
            
            sqltap.start(sqlalchemy.engine.Engine)
            sqltap.stop(sqlalchemy.engine.Engine)

        Whereas the following *will not work*
        ::

            my_engine = create_engine(...)
            sqltap.start(my_engine)
            sqltap.stop(sqlalchemy.engine.Engine)
            # still recording queries from my_engine!

    :exception KeyError: If the caller attempts to stop an engine that
        has not been passed to `sqltap.start`.

    """
    # sqlalchemy doesn't support remove yet for engines :(
    #sqlalchemy.event.remove(engine, "before_execute", _before_exec)
    #sqlalchemy.event.remove(engine, "after_execute", _after_exec)
    _engines.pop(engine)
    

def collect():
    """ Collect query statstics from sqltap. 

    Returns all query statistics collected by sqltap in the current thread.

    All query statistics returned to the caller by this call are removed
    from sqltap's internal storage.

    :return: A list of :class:`.QueryStats` objects.
    """

    if not hasattr(_local, "queries"):
        _local.queries = []

    qs = _local.queries
    _local.queries = []
    return qs


def report(statistics, filename = None):
    """ Generate an HTML report of query statistics.
    
    :param statistics: An iterable of :class:`.QueryStats` objects over
        which to prepare a report. This is typically a list returned by
        a call to :func:`collect`.

    :param filename: If present, additionally write the html report out 
        to a file at the specified path.

    :return: The generated HTML report.
    """

    class QueryGroup:
        def __init__(self):
            self.queries = []
            self.stacks = collections.defaultdict(int)
            self.max = 0
            self.min = sys.maxint
            self.sum = 0
            self.mean = 0

        def add(self, q):
            self.queries.append(q)
            self.stacks[q.stack] += 1

            self.max = max(self.max, q.duration)
            self.min = min(self.min, q.duration)
            self.sum = self.sum + q.duration
            self.mean = self.sum / len(self.queries)

    query_groups = collections.defaultdict(QueryGroup)
    all_group = QueryGroup()

    for qstats in statistics:
        qstats.stack = ''.join(traceback.format_list(qstats.stack))

        group = query_groups[str(qstats.text)]
        group.add(qstats)
        all_group.add(qstats)

    html = mako.template.Template(
        filename = os.path.join(os.path.dirname(__file__), 
                                "templates", "report.mako")
    ).render(
        query_groups = query_groups,
        all_group = all_group,
        name = "SQLTap Profiling Report"
    )

    if filename:
        with open(filename, 'w') as f:
            f.write(html)
        
    return html

def _before_exec(conn, clause, multiparams, params):
    """ SQLAlchemy event hook """
    _local.query_start_time = time.time()

def _after_exec(conn, clause, multiparams, params, results):
    """ SQLAlchemy event hook """

    # sqlalchemy doesn't support removing engines from engines yet
    # this is the hack which will let sqltap.stop still work
    # check whether this query is executed on one of the registered engines
    # or the global engine was registered
    if not(conn.engine in _engines or sqlalchemy.engine.Engine in _engines):
        return

    context_fn = _engines.get(conn.engine, _engines.get(sqlalchemy.engine.Engine))

    duration = time.time() - _local.query_start_time
    context = (None if not context_fn else
                context_fn(conn, clause, multiparams, params, results))
    q = QueryStats(clause, traceback.extract_stack()[:-1], duration, context)
    
    if not hasattr(_local, "queries"):
        _local.queries = []

    _local.queries.append(q)

