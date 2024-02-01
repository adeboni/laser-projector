import functools
import threading
import time

def threaded_time_delay(time_delay):
    def _threaded(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            def delayed_func(*args, **kwargs):
                time.sleep(time_delay)
                func(*args, **kwargs)
            t = threading.Thread(target=delayed_func, args=args, kwargs=kwargs)
            t.start()
        return wrapper
    return _threaded

def threaded(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        t = threading.Thread(target=func, args=args, kwargs=kwargs)
        t.start()
    return wrapper