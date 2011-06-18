import sqlalchemy.engine, sqlalchemy.event
import traceback, time, threading, collections, sys, mako, os

_current_query = threading.local()
_statslock = threading.Lock()
_queries = list()
_user_context_fn = None

class QueryStats:
    """ Statistics about a query

    You should not create these objects, but your application may choose
    inspect them in the filter functions you pass to :func:`sqltap.collect`
    and :func:`sqltap.purge`.
    
    :attr text: The text of the query
    :attr stack: The stack trace when this query was issued. Formatted as
        returned by py:func:`traceback.extract_stack`
    :attr duration: Duration of the query in seconds.
    :attr user_context: The value returned by the user_context_fn set with :func:`sqltap.start`.
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

    global _user_context_fn
    _user_context_fn = user_context_fn

def stop(engine = sqlalchemy.engine.Engine):
    """ Stop sqltap profiling

    :param engine: The sqlalchemy engine on which you want to
        stop profiling queries. The default is sqlalchemy.engine.Engine
        which will stop profiling queries across all engines.
    """
    sqlalchemy.event.remove(engine, "before_execute", _before_exec)
    sqlalchemy.event.remove(engine, "after_execute", _after_exec)
    

def collect(filter_fn = None, and_purge = False):
    """ Collect query statstics from sqltap. 

    :param filter_fn: A function which takes a :class:`.QueryStats` object 
        and returns `True` if the :class:`.QueryStats` object should be 
        collected. If `filter_fn` is `None`, all stats are collected.
        
    :param and_purge: If True, purges all of the stats records that are collected.
    
    :return: A list of :class:`.QueryStats` objects.
    """
    if filter_fn is None:
        filter_fn = lambda q: True

    with _statslock:
        # return a copy of the list to the caller
        stats = filter(filter_fn, _queries)

        if and_purge:
            _purge(filter_fn)
        
        return stats

def _purge(filter_fn):
    global _queries
    # The filter_fn returns True for items to be removed,
    # so invert it here for items to keep
    _queries = filter(lambda q: not filter_fn(q), _queries)
    
def purge(filter_fn = None):
    """ Remove query statistics from sqltap.

    :param filter_fn: A function which takes a :class:`.QueryStats` object 
        and returns `True` if the :class:`.QueryStats` object should be 
        purged. If `filter_fn` is `None`, all stats are purged.
    """
    if filter_fn is None:
        filter_fn = lambda q: True

    with _statslock:
        _purge(filter_fn)

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

def _before_exec(conn, clause, mutliparams, params):
    """ SQLAlchemy event hook """

    _current_query.start_time = time.time()

def _after_exec(conn, clause, multiparams, params, results):
    """ SQLAlchemy event hook """
    duration = time.time() - _current_query.start_time
    context = (None if not _user_context_fn else
                _user_context_fn(conn, clause, multiparams, params, results))
    q = QueryStats(clause, traceback.extract_stack()[:-1], duration, context)
    with _statslock:
        _queries.append(q)

