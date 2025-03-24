import threading
from queue import Queue, Empty, Full
import psutil
from interface.status_bar.update_notif import update_notif

class LoggingQueue:
    """Handles the queue setup and management for frame logging."""
    
    def __init__(self, window, roi_width, roi_height):
        self.window = window
        
        # Store ROI dimensions
        self.roi_width = roi_width
        self.roi_height = roi_height
        
        # Initialize queue
        self.queue_size = self._calculate_queue_size()
        self.frame_queue = Queue(maxsize=self.queue_size)
        self.frame_bytes = None
        
        # Performance tracking
        self.frames_dropped = 0
        self.frames_recorded = 0
        self.frames_saved = 0
        
    def _calculate_queue_size(self):
        """Calculate queue size based on 90% of available RAM."""
        available_ram = psutil.virtual_memory().available
        queue_size_bytes = available_ram * 0.9
        
        # Calculate bytes per frame (assuming 8-bit depth) We can update this one day to handle any bit depth
        bytes_per_pixel = 1  # 8-bit = 1 byte
        bytes_per_frame = self.roi_width * self.roi_height * bytes_per_pixel
        
        queue_size_elements = queue_size_bytes / bytes_per_frame
        queue_size_GB = int(queue_size_bytes / 1024**3)
        
        print(f"Queue size set to {queue_size_elements:.1f} elements ({(queue_size_GB)} GB)")
        return int(queue_size_elements)
        
    def _update_notif(self, message):
        """Update status bar and print message."""
        print(message)
        update_notif(message)
        
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
            
        try:
            self.frame_queue.put((frame, timestamp), timeout=0.1)
            self.frames_recorded += 1
            return True
        except Full:
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
