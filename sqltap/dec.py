import sqltap
import sqlalchemy.engine

def profile(engine = sqlalchemy.engine.Engine, user_context_fn = None):
    """ Convenience decorator for profiling sqlalchemy queries.
    
    See :func:`sqltap.start` for parameter information.

    Example usage::
        
        @sqltap.dec.profile
        def holy_hand_grenade():
            for number in Session.query(Numbers).filter(Numbers.value <= 3):
                print number
    """
    def inner_profile(fn):
        def dec(*args, **kwargs):
            sqltap.start(engine, user_context_fn)
            retval = fn(*args, **kwargs)
            sqltap.stop(engine)
            return retval
        return dec
    return inner_profile

