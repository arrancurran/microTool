import threading
from datetime import datetime
import time
from queue import Queue, Empty, Full
import psutil
from .log_HDF5 import HDF5Logger
from PyQt6.QtCore import Qt, QMetaObject, Q_ARG

class RecordStream:
    """Handles continuous recording of camera frames to a queue."""
    
    def __init__(self, stream_camera, window):
        self.stream_camera = stream_camera
        self.camera_control = stream_camera.camera_control
        self.window = window
        self.logger = HDF5Logger()
        
        # Initialize recording state
        self.queue_size = self._calculate_queue_size()
        self.frame_queue = Queue(maxsize=self.queue_size)
        self.recording_thread = None
        self.saving_thread = None
        self.is_recording = False
        self.is_saving = False
        self.was_streaming = False
        
        # Performance tracking
        self.frames_dropped = 0
        self.frames_recorded = 0
        self.frames_saved = 0
        self.frame_bytes = None
        
    def _calculate_queue_size(self):
        """Calculate queue size based on 50% of available RAM."""
        available_ram = psutil.virtual_memory().available
        size = int((available_ram * 0.5) / (2048 * 2048))
        print(f"Queue size set to {size} frames")
        return size
        
    def _update_status(self, message):
        """Update status bar and print message."""
        print(message)
        if hasattr(self.window, 'statusBar'):
            QMetaObject.invokeMethod(
                self.window.statusBar(),
                "showMessage",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, message)
            )
            
    def _format_size(self, bytes_size):
        """Format bytes to human readable size."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024
        return f"{bytes_size:.1f} TB"
        
    def _get_queue_size(self):
        """Get current queue size in human readable format."""
        if not self.frame_bytes or self.frame_queue.empty():
            return "0 B"
        return self._format_size(self.frame_bytes * self.frame_queue.qsize())
        
    def start_recording(self):
        """Start recording frames from camera."""
        if self.is_recording:
            return False
            
        # Reset counters
        self.frames_dropped = self.frames_recorded = self.frames_saved = 0
        
        try:
            # Handle streaming state
            self.was_streaming = (self.stream_camera.camera_thread is not None and 
                                self.stream_camera.camera_thread.isRunning())
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
            
            # Start recording threads
            self.is_recording = self.is_saving = True
            self.saving_thread = threading.Thread(target=self._save_frames, daemon=True)
            self.recording_thread = threading.Thread(target=self._record_frames, daemon=True)
            
            self.saving_thread.start()
            time.sleep(0.1)  # Ensure saving thread is ready
            self.recording_thread.start()
            
            self.camera_control.start_camera()
            return True
            
        except Exception as e:
            self._update_status(f"Error starting recording: {e}")
            self.is_recording = self.is_saving = False
            self.logger.stop_recording()
            return False
            
    def _cleanup(self):
        """Handle cleanup after recording stops."""
        try:
            # Wait for all frames to be saved with timeout
            max_wait_time = 30  # Maximum wait time in seconds
            start_time = time.time()
            
            while not self.frame_queue.empty():
                queue_size = self._get_queue_size()
                frames_remaining = self.frame_queue.qsize()
                save_rate = max(1, self.frames_saved / (time.time() - start_time + 0.1))
                estimated_time = int(frames_remaining / save_rate)
                
                self._update_status(
                    f"Acquisition Finished. Saving data to disk... ({queue_size} in queue, ~{estimated_time}s remaining)"
                )
                
                # Check for timeout
                if time.time() - start_time > max_wait_time:
                    print(f"Warning: Saving timeout after {max_wait_time} seconds")
                    break
                    
                time.sleep(0.2)
            
            # Ensure saving thread completes
            self.is_saving = False
            if self.saving_thread:
                self.saving_thread.join(timeout=5.0)  # Wait up to 5 seconds for thread to finish
            
            self.logger.stop_recording()
            
            # Print statistics
            stats = (f"\nRecording Statistics:\n"
                    f"Total frames recorded: {self.frames_recorded}\n"
                    f"Total frames saved: {self.frames_saved}\n"
                    f"Frames dropped: {self.frames_dropped}\n"
                    f"Frames remaining in queue: {self.frame_queue.qsize()}")
            print(stats)
            
            # Final cleanup - ensure queue is empty
            try:
                while True:
                    frame, timestamp = self.frame_queue.get_nowait()
                    if self.logger.save_frame(frame, timestamp):
                        self.frames_saved += 1
                    self.frame_queue.task_done()
            except Empty:
                pass
            
            # Verify all frames were handled
            frames_handled = self.frames_saved + self.frames_dropped
            if frames_handled < self.frames_recorded:
                print(f"Warning: {self.frames_recorded - frames_handled} frames were lost during cleanup")
            
            # Show completion message briefly, then clear
            self._update_status("Acquisition finished and saved to disk.")
            time.sleep(2)  # Show completion message for 2 seconds
            self._update_status("")  # Clear status bar
            
            if self.was_streaming:
                self.window.start_stream.trigger()
                
        except Exception as e:
            self._update_status(f"Error during cleanup: {e}")
            time.sleep(2)  # Show error for 2 seconds
            self._update_status("")  # Clear status bar
            
    def stop_recording(self):
        """Stop recording and save remaining frames."""
        if not self.is_recording:
            return
            
        # Stop recording but keep saving thread running
        self.is_recording = False
        self.camera_control.stop_camera()
        
        if self.recording_thread:
            self.recording_thread.join(timeout=5.0)  # Wait up to 5 seconds for recording to stop
        
        # Start cleanup in background
        cleanup_thread = threading.Thread(target=self._cleanup, daemon=True)
        cleanup_thread.start()
        
        # Show initial status
        self._update_status(
            f"Acquisition Finished. Saving data to disk... ({self._get_queue_size()} in queue)"
        )
        
    def _record_frames(self):
        """Record frames from camera to queue."""
        while self.is_recording:
            try:
                if self.frame_queue.qsize() >= self.queue_size * 0.9:
                    time.sleep(0.001)  # Apply backpressure
                    continue
                
                self.camera_control.get_image()
                frame = self.camera_control.get_image_data()
                
                if frame is not None:
                    if self.frame_bytes is None:
                        self.frame_bytes = frame.nbytes
                        
                    try:
                        self.frame_queue.put((frame, time.time()), timeout=0.1)
                        self.frames_recorded += 1
                    except Full:
                        self.frames_dropped += 1
                        print(f"Warning: Frame dropped - queue full ({self.frames_dropped} total drops)")
                        
            except Exception as e:
                print(f"Error recording frame: {e}")
                
    def _save_frames(self):
        """Save frames from queue to disk."""
        batch_size = 10
        frames_in_batch = 0
        last_update = 0
        start_time = time.time()
        
        while self.is_saving or not self.frame_queue.empty():
            try:
                frame, timestamp = self.frame_queue.get(timeout=0.1)
                
                if self.logger.save_frame(frame, timestamp):
                    self.frames_saved += 1
                else:
                    print("Warning: Failed to save frame")
                    
                self.frame_queue.task_done()
                
                # Update status periodically during saving
                current_time = time.time()
                if not self.is_recording and current_time - last_update >= 1.0:
                    queue_size = self._get_queue_size()
                    frames_remaining = self.frame_queue.qsize()
                    save_rate = self.frames_saved / (current_time - start_time + 0.1)
                    estimated_time = int(frames_remaining / max(1, save_rate))
                    
                    self._update_status(
                        f"Acquisition Finished. Saving data to disk... ({queue_size} in queue, ~{estimated_time}s remaining)"
                    )
                    last_update = current_time
                
                # Prevent thread starvation
                frames_in_batch += 1
                if frames_in_batch >= batch_size:
                    frames_in_batch = 0
                    time.sleep(0)
                    
            except Empty:
                if not self.is_saving and self.frame_queue.empty():
                    break
                frames_in_batch = 0
            except Exception as e:
                print(f"Error saving frame: {e}")
                self.frame_queue.task_done() 