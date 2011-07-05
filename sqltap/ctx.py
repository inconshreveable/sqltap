import sqltap
import sqlalchemy.engine

class profile:
    """
    Convenience context manager for profiling sqlalchemy queries.
    
    See :func:`sqltap.start` for parameter information.

    Example usage::
        
        with sqltap.ctx.profile:
            for number in Session.query(Numbers).filter(Numbers.value <= 3):
                print number
    """
    def __init__(self, engine = sqlalchemy.engine.Engine, user_context_fn = None):
        self.engine = engine
        self.user_context_fn = user_context_fn

    def __enter__(self, *args, **kwargs):
        sqltap.start(self.engine, self.user_context_fn)

    def __exit__(self, *args, **kwargs):
        sqltap.stop(self.engine)


