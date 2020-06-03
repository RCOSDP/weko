from functools import wraps

import memory_profiler
try:
    import tracemalloc
    has_tracemalloc = True
except ImportError:
    has_tracemalloc = False

def my_profiler(func=None, stream=None, precision=1, backend='psutil'):
    backend = memory_profiler.choose_backend(backend)
    if backend == 'tracemalloc' and has_tracemalloc:
        if not tracemalloc.is_tracing():
            tracemalloc.start()
    if func is not None:
        @wraps(func)
        def wrapper(*args, **kwargs):
            prof = memory_profiler.LineProfiler(backend=backend)
            val = prof(func)(*args, **kwargs)
            memory_profiler.show_results(prof, stream=stream,
                                         precision=precision)
            return val
        return wrapper
    else:
        def inner_wrapper(f):
            return profile(f, stream=stream, precision=precision,
                           backend=backend)
        return inner_wrapper

