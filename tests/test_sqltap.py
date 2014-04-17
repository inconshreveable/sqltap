from __future__ import print_function

from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy.ext.declarative import declarative_base
import sqltap, unittest
import nose.tools

def _startswith(qs, text):
    return list(filter(lambda q: str(q.text).startswith(text), qs))

class TestSQLTap(object):

    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:', echo=True)

        Base = declarative_base(bind = self.engine)

        class A(Base):
            __tablename__ = "a"
            id = Column("id", Integer, primary_key = True)
        self.A = A

        Base.metadata.create_all(self.engine)

        self.Session = sessionmaker(bind=self.engine)

    def test_insert(self):
        """ Simple test that sqltap collects an insert query. """
        profiler = sqltap.start(self.engine)

        sess = self.Session()
        sess.add(self.A())
        sess.flush()

        stats = profiler.collect()
        assert len(_startswith(stats, 'INSERT')) == 1

    def test_select(self):
        """ Simple test that sqltap collects a select query. """
        profiler = sqltap.start(self.engine)

        sess = self.Session()
        sess.query(self.A).all()

        stats = profiler.collect()
        assert len(_startswith(stats, 'SELECT')) == 1

    def test_engine_scoped(self):
        """
        Test that calling sqltap.start with a particular engine instance
        properly captures queries only to that engine.
        """
        engine2 = create_engine('sqlite:///:memory:', echo=True)

        Base = declarative_base(bind = engine2)

        class B(Base):
            __tablename__ = "b"
            id = Column("id", Integer, primary_key = True)

        Base.metadata.create_all(engine2)
        Session = sessionmaker(bind=engine2)
        profiler = sqltap.start(engine2)

        sess = self.Session()
        sess.query(self.A).all()

        sess2 = Session()
        sess2.query(B).all()

        stats = _startswith(profiler.collect(), 'SELECT')
        assert len(stats) == 1


    def test_engine_global(self):
        """ Test that registering globally for all queries correctly pulls queries
            from multiple engines.
        """
        engine2 = create_engine('sqlite:///:memory:', echo=True)

        Base = declarative_base(bind = engine2)

        class B(Base):
            __tablename__ = "b"
            id = Column("id", Integer, primary_key = True)

        Base.metadata.create_all(engine2)
        Session = sessionmaker(bind=engine2)
        profiler = sqltap.start()

        sess = self.Session()
        sess.query(self.A).all()

        sess2 = Session()
        sess2.query(B).all()

        stats = _startswith(profiler.collect(), 'SELECT')
        assert len(stats) == 2
        
    @nose.tools.raises(AssertionError)
    def test_start_twice(self):
        """ Ensure that multiple calls to ProfilingSession.start() raises assertion
        error.
        """
        profiler = sqltap.ProfilingSession(self.engine)
        profiler.start()
        profiler.start()

    def test_stop(self):
        """ Ensure queries after you call ProfilingSession.stop() are not recorded. """
        profiler = sqltap.start(self.engine)
        sess = self.Session()
        sess.query(self.A).all()
        profiler.stop()
        sess.query(self.A).all()

        assert len(profiler.collect()) == 1

    def test_stop_global(self):
        """ Ensure queries after you call ProfilingSession.stop() are not recorded
            when passing in the 'global' Engine object to record queries across all engines.
        """
        profiler = sqltap.start()
        sess = self.Session()
        sess.query(self.A).all()
        profiler.stop()
        sess.query(self.A).all()

        assert len(profiler.collect()) == 1

    def test_report(self):
        profiler = sqltap.start(self.engine)

        sess = self.Session()
        q = sess.query(self.A)
        qtext = str(q)
        q.all()

        report = sqltap.report(profiler.collect())
        assert 'sqltap profile report' in report
        assert qtext in report
        

    def test_report_aggregation(self):
        """
        Test that we aggregate stats for the same query called from
        different locations as well as aggregating queries called
        from the same stack trace.
        """
        profiler = sqltap.start(self.engine)

        sess = self.Session()
        q = sess.query(self.A)

        q.all()
        q.all()
            
        q2 = sess.query(self.A).filter(self.A.id == 10)
        for i in range(10):
            q2.all()

        report = sqltap.report(profiler.collect())
        print(report)
        assert '2 unique' in report
        assert '<dd>10</dd>' in report

    def test_start_stop(self):
        sess = self.Session()
        q = sess.query(self.A)
        profiled = sqltap.ProfilingSession(self.engine)

        q.all()

        stats = profiled.collect()
        assert len(_startswith(stats, 'SELECT')) == 0

        profiled.start()
        q.all()
        q.all()
        profiled.stop()
        q.all()

        stats2 = profiled.collect()
        assert len(_startswith(stats2, 'SELECT')) == 2

    def test_decorator(self):
        """ Test that queries issued in a decorated function are profiled """
        sess = self.Session()
        q = sess.query(self.A)
        profiled = sqltap.ProfilingSession(self.engine)

        @profiled
        def test_function():
            self.Session().query(self.A).all()
            
        q.all()
        
        stats = profiled.collect()
        assert len(_startswith(stats, 'SELECT')) == 0

        test_function()
        test_function()
        q.all()

        stats = profiled.collect()
        assert len(_startswith(stats, 'SELECT')) == 2

    def test_context_manager(self):
        sess = self.Session()
        q = sess.query(self.A)
        profiled = sqltap.ProfilingSession(self.engine)

        with profiled:
            q.all()
                
        q.all()
        
        stats = profiled.collect()
        assert len(_startswith(stats, 'SELECT')) == 1


    def test_context_fn(self):
        profiler = sqltap.start(self.engine, lambda *args: 1)

        sess = self.Session()
        q = sess.query(self.A)
        q.all()
        stats = profiler.collect()

        ctxs = [qstats.user_context for qstats in _startswith(stats, 'SELECT')]
        assert ctxs[0] == 1

    def test_context_fn_isolation(self):
        x = { "i": 0 }
        def context_fn(*args):
            x['i'] += 1
            return x['i']

        profiler = sqltap.start(self.engine, context_fn)

        sess = self.Session()
        sess.query(self.A).all()

        sess2 = Session()
        sess2.query(self.A).all()

        stats = profiler.collect()

        ctxs = [qstats.user_context for qstats in _startswith(stats, 'SELECT')]
        assert ctxs.count(1) == 1
        assert ctxs.count(2) == 1

    def test_collect_empty(self):
        profiler = sqltap.start(self.engine)
        assert len(profiler.collect()) == 0

    def test_collect_fn(self):
        collection = []
        def my_collector(q):
            collection.append(q)

        sess = self.Session()
        profiler = sqltap.start(self.engine, collect_fn=my_collector)
        sess.query(self.A).all()

        assert len(collection) == 1

        sess.query(self.A).all()

        assert len(collection) == 2

    @nose.tools.raises(AssertionError)
    def test_collect_fn_execption_on_collect(self):
        def noop(): pass
        profiler = sqltap.start(self.engine, collect_fn=noop)
        profiler.collect()
