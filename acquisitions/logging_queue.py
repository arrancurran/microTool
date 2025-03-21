import threading
from queue import Queue, Empty, Full
import psutil
import time
from datetime import datetime
from utils.status import update_status

class LoggingQueue:
    """Handles the queue setup and management for frame logging."""
    
    def __init__(self, window):
        self.window = window
        
        # Initialize queue
        self.queue_size = self._calculate_queue_size()
        self.frame_queue = Queue(maxsize=self.queue_size)
        self.frame_bytes = None
        
        # Performance tracking
        self.frames_dropped = 0
        self.frames_recorded = 0
        self.frames_saved = 0
        
    def _calculate_queue_size(self):
        """Calculate queue size based on 50% of available RAM."""
        available_ram = psutil.virtual_memory().available
        size = int((available_ram * 0.5) / (2048 * 2048))
        print(f"Queue size set to {size} frames")
        return size
        
    def _update_status(self, message):
        """Update status bar and print message."""
        print(message)
        update_status(message)
        
    def _format_size(self, bytes_size):
        """Format bytes to human readable size."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024
        return f"{bytes_size:.1f} TB"
        
    def get_queue_size(self):
        """Get current queue size in human readable format."""
        if not self.frame_bytes or self.frame_queue.empty():
            return "0 B"
        return self._format_size(self.frame_bytes * self.frame_queue.qsize())
        
    def put_frame(self, frame, timestamp):
        """Put a frame in the queue with backpressure handling."""
        if self.frame_bytes is None:
            self.frame_bytes = frame.nbytes
            
        if self.frame_queue.qsize() >= self.queue_size * 0.9:
            time.sleep(0.001)  # Apply backpressure
            return False
            
        try:
            self.frame_queue.put((frame, timestamp), timeout=0.1)
            self.frames_recorded += 1
            return True
        except Full:
            self.frames_dropped += 1
            print(f"Warning: Frame dropped - queue full ({self.frames_dropped} total drops)")
            return False
            
    def get_frame(self, timeout=0.1):
        """Get a frame from the queue."""
        try:
            frame, timestamp = self.frame_queue.get(timeout=timeout)
            self.frame_queue.task_done()
            return frame, timestamp
        except Empty:
            return None, None
            
    def is_empty(self):
        """Check if queue is empty."""
        return self.frame_queue.empty()
        
    def get_queue_stats(self):
        """Get current queue statistics."""
        return {
            'frames_recorded': self.frames_recorded,
            'frames_saved': self.frames_saved,
            'frames_dropped': self.frames_dropped,
            'queue_size': self.frame_queue.qsize(),
            'queue_capacity': self.queue_size
        }
        
    def reset_stats(self):
        """Reset all statistics counters."""
        self.frames_dropped = 0
        self.frames_recorded = 0
        self.frames_saved = 0
