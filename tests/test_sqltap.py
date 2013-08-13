from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy.ext.declarative import declarative_base
import sqltap, unittest, threading, sqltap.dec, sqltap.ctx

def _startswith(qs, text):
    return filter(lambda q: str(q.text).startswith(text), qs)

class SqlTapTests(unittest.TestCase):

    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:', echo = True)

        Base = declarative_base(bind = self.engine)

        class A(Base):
            __tablename__ = "a"
            id = Column("id", Integer, primary_key = True)
        self.A = A

        Base.metadata.create_all(self.engine)

        self.Session = sessionmaker(bind = self.engine)

    def test_insert(self):
        """ Simple test that sqltap collects an insert query. """
        sqltap.start(self.engine)

        sess = self.Session()
        sess.add(self.A())
        sess.flush()

        stats = sqltap.collect()
        assert len(_startswith(stats, 'INSERT')) == 1

    def test_select(self):
        """ Simple test that sqltap collects a select query. """
        sqltap.start(self.engine)

        sess = self.Session()
        sess.query(self.A).all()

        stats = sqltap.collect()
        assert len(_startswith(stats, 'SELECT')) == 1

    def test_thread(self):
        """ Test that queries in a separate thread can not be collected from
        another thread.
        """
        def f():
            engine2 = create_engine('sqlite:///:memory:', echo = True)

            Base = declarative_base(bind = engine2)

            class B(Base):
                __tablename__ = "b"
                id = Column("id", Integer, primary_key = True)

            Base.metadata.create_all(engine2)
            Session = sessionmaker(bind = engine2)
            sqltap.start(engine2)

            sqltap.start(self.engine)
            sess2 = Session()
            sess2.query(B).all()
        
        thread = threading.Thread(target = f)
        thread.start()
        thread.join()
        stats = sqltap.collect()
        assert len(_startswith(stats, 'SELECT')) == 0

    def test_engine_scoped(self):
        """ Test that calling sqltap.start with a particular engine instance
        properly captures queries only to that engine.
        """
        engine2 = create_engine('sqlite:///:memory:', echo = True)

        Base = declarative_base(bind = engine2)

        class B(Base):
            __tablename__ = "b"
            id = Column("id", Integer, primary_key = True)

        Base.metadata.create_all(engine2)
        Session = sessionmaker(bind = engine2)
        sqltap.start(engine2)

        sess = self.Session()
        sess.query(self.A).all()

        sess2 = Session()
        sess2.query(B).all()

        stats = _startswith(sqltap.collect(), 'SELECT')
        assert len(stats) == 1

    def test_engine_global(self):
        """ Test that registering globally for all queries correctly pulls queries
        from multiple engines.
    
        This test passes, but because SQLAlchemy won't ever let us unregister
        our event handlers, this causes side-effects in other tests that will
        break them.
        """
        return
    
        engine2 = create_engine('sqlite:///:memory:', echo = True)

        Base = declarative_base(bind = engine2)

        class B(Base):
            __tablename__ = "b"
            id = Column("id", Integer, primary_key = True)

        Base.metadata.create_all(engine2)
        Session = sessionmaker(bind=engine2)
        sqltap.start()

        sess = self.Session()
        sess.query(self.A).all()

        sess2 = Session()
        sess2.query(B).all()

        stats = _startswith(sqltap.collect(), 'SELECT')
        assert len(stats) == 2
        
    def test_start_twice(self):
        """ Ensure that if multiple calls to sqltap.start on the same
        engine do not cause us to record more than one event per query.
        """
        sqltap.start(self.engine)
        sqltap.start(self.engine)

        sess = self.Session()
        sess.query(self.A).all()

        stats = _startswith(sqltap.collect(), 'SELECT')
        assert len(stats) == 1

    def test_stop(self):
        """ Ensure queries after you call sqltap.stop() are not recorded. """
        sqltap.start(self.engine)
        
        sess = self.Session()
        sess.query(self.A).all()
        
        sqltap.stop(self.engine)
        
        sess.query(self.A).all()

        assert len(sqltap.collect()) == 1

    def test_stop_global(self):
        """ Ensure queries after you call sqltap.stop() are not recorded when passing
        in the 'global' Engine object to record queries across all engines.
    
        This test passes, but because SQLAlchemy won't ever let us unregister
        our event handlers, this causes side-effects in other tests and will.
        """
        return
        
        sqltap.start()
        
        sess = self.Session()
        sess.query(self.A).all()
        
        sqltap.stop()
        
        sess.query(self.A).all()

        assert len(sqltap.collect()) == 1

    def test_report(self):
        sqltap.start(self.engine)

        sess = self.Session()
        q = sess.query(self.A)
        qtext = str(q)
        q.all()

        report = sqltap.report(sqltap.collect())
        assert 'SQLTap Report' in report
        assert qtext in report

    def test_report_aggregation(self):
        """ Test that we aggregate stats for the same query called from
        different locations as well as aggregating queries called
        from the same stack trace.
        """
        sqltap.start(self.engine)

        sess = self.Session()
        q = sess.query(self.A)

        q.all()
        q.all()

        q2 = sess.query(self.A).filter(self.A.id == 10)
        for i in xrange(10):
            q2.all()

        report = sqltap.report(sqltap.collect())
        assert '2 unique' in report
        assert 'Query count: 10' in report

    def test_decorator(self):
        sess = self.Session()
        q = sess.query(self.A)

        @sqltap.dec.profile(self.engine)
        def test_function():
            q.all()
            
        q.all()
        
        stats = sqltap.collect()
        assert len(_startswith(stats, 'SELECT')) == 0

        test_function()
        test_function()
        q.all()

        stats = sqltap.collect()
        assert len(_startswith(stats, 'SELECT')) == 0

    def test_context_manager(self):
        sess = self.Session()
        q = sess.query(self.A)

        with sqltap.ctx.profile(self.engine):
            q.all()
                
        q.all()
        
        stats = sqltap.collect()
        assert len(_startswith(stats, 'SELECT')) == 1

    def test_context_fn(self):
        sqltap.start(self.engine, lambda *args: 1)

        sess = self.Session()
        q = sess.query(self.A)
        q.all()
        stats = sqltap.collect()

        ctxs = [qstats.user_context for qstats in _startswith(stats, 'SELECT')]
        assert ctxs[0] == 1

    def test_context_fn_isolation(self):
        engine2 = create_engine('sqlite:///:memory:', echo = True)

        Base = declarative_base(bind = engine2)

        class B(Base):
            __tablename__ = "b"
            id = Column("id", Integer, primary_key = True)

        Base.metadata.create_all(engine2)
        Session = sessionmaker(bind = engine2)

        sqltap.start(self.engine, lambda *args: 1)
        sqltap.start(engine2, lambda *args: 2)

        sess = self.Session()
        sess.query(self.A).all()

        sess2 = Session()
        sess2.query(B).all()

        stats = sqltap.collect()

        ctxs = [qstats.user_context for qstats in _startswith(stats, 'SELECT')]
        assert ctxs.count(1) == 1
        assert ctxs.count(2) == 1

    def test_collect_empty(self):
        sqltap.start(self.engine)
        assert len(sqltap.collect()) == 0
