import threading
from datetime import datetime
import time
from .log_HDF5 import HDF5Logger
from .logging_queue import LoggingQueue
from utils import update_status

class RecordStream:
    """Handles continuous recording of camera frames to a queue."""
    
    def __init__(self, stream_camera, window):
        self.stream_camera = stream_camera
        self.camera_control = stream_camera.camera_control
        self.window = window
        self.logger = HDF5Logger()
        
        # Initialize recording state
        self.queue = LoggingQueue(window)
        self.recording_thread = None
        self.is_recording = False
        self.was_streaming = False
        
    def start_recording(self):
        """Start recording frames from camera."""
        if self.is_recording:
            return False
            
        # Reset counters
        self.queue.reset_stats()
        
        try:
            # Handle streaming state
            self.was_streaming = (self.stream_camera.camera_thread is not None and self.stream_camera.camera_thread.isRunning())
            if self.was_streaming:
                self.window.stop_stream.trigger()
            
            # Initialize recording
            metadata = {
                'camera_model': self.camera_control.camera.get_device_name().decode('utf-8'),
                'timestamp': datetime.now().isoformat(),
                'exposure': self.camera_control.call_camera_command("exposure", "get"),
                'roi_width': self.camera_control.call_camera_command("width", "get"),
                'roi_height': self.camera_control.call_camera_command("height", "get"),
                'roi_offset_x': self.camera_control.call_camera_command("offset_x", "get"),
                'roi_offset_y': self.camera_control.call_camera_command("offset_y", "get")
            }
            
            if not self.logger.start_recording(metadata):
                raise Exception("Failed to start HDF5 logger")
            
            # Start recording thread and saving
            self.is_recording = True
            self.recording_thread = threading.Thread(target=self._record_frames, daemon=True)
            self.recording_thread.start()
            
            # Start saving frames
            if not self.logger.start_saving(self.queue):
                raise Exception("Failed to start saving thread")
            
            self.camera_control.start_camera()
            update_status("Recording Live Stream")
            return True
            
        except Exception as e:
            print(f"Error Starting Recording: {e}")
            update_status(f"Error Starting Recording: {e}")
            self.is_recording = False
            self.logger.stop_recording()
            return False
            
    def stop_recording(self):
        """Stop recording and save remaining frames."""
        if not self.is_recording:
            return
            
        # Stop recording
        self.is_recording = False
        self.camera_control.stop_camera()
        
        if self.recording_thread:
            self.recording_thread.join(timeout=5.0)  # Wait up to 5 seconds for recording to stop
        
        # Start cleanup in background
        cleanup_thread = threading.Thread(
            target=self.logger.cleanup,
            args=(self.queue, self.was_streaming, self.window),
            daemon=True
        )
        cleanup_thread.start()

    def _record_frames(self):
        """Record frames from camera to queue."""
        while self.is_recording:
            try:
                self.camera_control.get_image()
                frame = self.camera_control.get_image_data()
                
                if frame is not None:
                    self.queue.put_frame(frame, time.time())
                        
            except Exception as e:
                print(f"Error recording frame: {e}") 