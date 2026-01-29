import time
from contextlib import contextmanager
from typing import Generator


class Timer:
    """Simple timer for measuring execution time"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """Start the timer"""
        self.start_time = time.time()
    
    def stop(self):
        """Stop the timer"""
        self.end_time = time.time()
    
    @property
    def duration(self) -> float:
        """Get duration in seconds"""
        if self.start_time is None or self.end_time is None:
            return 0.0
        return self.end_time - self.start_time
    
    @property
    def duration_ms(self) -> float:
        """Get duration in milliseconds"""
        return self.duration * 1000


@contextmanager
def timer_context() -> Generator[Timer, None, None]:
    """Context manager for timing code blocks"""
    timer = Timer()
    timer.start()
    try:
        yield timer
    finally:
        timer.stop()
