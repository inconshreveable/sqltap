import contextlib
import sqltap
import sqlalchemy.engine

@contextlib.contextmanager
def profile(engine = sqlalchemy.engine.Engine, user_context_fn = None):
    """
    Convenience context manager for profiling sqlalchemy queries.
    
    It takes the same arguments as sqltap.start
    """
    sqltap.start(engine, user_context_fn)
    yield
    sqltap.stop(engine)


