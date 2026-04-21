import time
import tracemalloc
from contextlib import contextmanager
from functools import wraps

def us_timer(func):
    """Decorator to clock calculation latency in microseconds."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter_ns()
        result = func(*args, **kwargs)
        end = time.perf_counter_ns()
        
        duration_us = (end - start) / 1000.0
        # Store latest latency for external retrieval
        wrapper.latest_latency_us = duration_us
        return result
        
    wrapper.latest_latency_us = 0.0
    return wrapper

@contextmanager
def track_memory_drift(label="Memory Check"):
    """
    Context manager that reports memory usage change in KB.
    """
    if not tracemalloc.is_tracing():
        tracemalloc.start()
        
    start_current, start_peak = tracemalloc.get_traced_memory()
    yield
    end_current, end_peak = tracemalloc.get_traced_memory()
    
    drift_bytes = end_current - start_current
    print(f"[{label}] Memory Byte-Drift: {drift_bytes / 1024:.2f} KB | Peak Delta: {(end_peak - start_peak) / 1024:.2f} KB")

class LabStatus:
    IDLE = "SYSTEM IDLE"
    ACTIVE = "SIMULATING CASCADE..."
    ERROR = "SYSTEM ERROR"
