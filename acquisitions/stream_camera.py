"""
Camera streaming module that handles continuous frame capture in a background thread.
Uses QThread to stream frames from a Ximea camera without blocking the UI.
Emits signals when new frames are ready for display.
"""

from PyQt6.QtCore import QObject, pyqtSignal, QThread
import queue
import time

class CameraThread(QThread):
    """
    Handles continuous camera frame capture in a background thread.
    
    Called by:
    - interface/ui_methods.py: UIMethods uses CameraThread for streaming
    - acquisitions/record_stream.py: RecordStream uses CameraThread for recording
    
    Example usage:
        camera_control = CameraControl()
        thread = CameraThread(camera_control)
        thread.frame_captured.connect(handle_new_frame)
        thread.start()
        # ... later ...
        thread.stop()
    """
    frame_captured = pyqtSignal(object) # Signal to emit when a new frame has been captured from the camera
    
    def __init__(self, camera_control):
        
        """Initialize the camera thread"""
        super().__init__()
        self.camera_control = camera_control
        self.running = True
        self.frame_Hz = 60  # Fixed 60 Hz (1000ms/60 ≈ 16.67ms)

    def run(self):
        
        """Main thread loop"""
        while self.running:
            try:
                time.sleep(1/self.frame_Hz) # Sleep for the appropriate amount of time to achieve the desired frame rate
                
                """Get image from camera"""
                self.camera_control.get_image()
                image_data = self.camera_control.get_image_data()
                
                if image_data is not None:
                    self.frame_captured.emit(image_data)
                
            except Exception as e:
                print(f"Error in camera thread: {str(e)}")
                time.sleep(0.1)  # Sleep briefly on error to prevent hammering the CPU on error
    
    def stop(self):
        
        """Stop the thread"""
        self.running = False
        self.wait()

class StreamCamera(QObject):
    """
    Manages camera streaming with frame buffering and thread control.
    
    Called by:
    - interface/ui_methods.py: UIMethods uses StreamCamera for live display
    - acquisitions/record_stream.py: RecordStream uses StreamCamera for recording
    
    Example usage:
        camera = CameraControl()
        stream = StreamCamera(camera)
        stream.frame_available.connect(update_display)
        stream.start_stream()
        # ... later ...
        stream.stop_stream()
    """
    frame_available = pyqtSignal() # Signal to emit when a new frame is available in the queue
    
    def __init__(self, camera_control):
        
        """Initialize the camera and streaming components."""
        super().__init__()
        self.camera_control = camera_control
        self.camera = None
        self.streaming_queue = queue.Queue(maxsize=1)  # Buffer for frames
        self.camera_thread = None

    def start_stream(self):
        
        """Start capturing frames in a separate thread."""
        if self.camera_thread is None or not self.camera_thread.isRunning():
            self.camera_thread = CameraThread(self.camera_control)
            self.camera_thread.frame_captured.connect(self._handle_frame)
            self.camera_control.start_camera()
            self.camera_thread.start()
            print("StreamCamera.start_stream(): Camera stream started.")

    def _handle_frame(self, image_data):
        """Handle a new frame from the camera thread with throttling"""
        current_time = time.time()
        
        # Only process frame if enough time has passed (limit to 30 FPS for UI)
        if not hasattr(self, '_last_frame_time') or (current_time - self._last_frame_time) >= 0.033:
            self._last_frame_time = current_time
            
            # Process frame as normal
            try:
                if not self.streaming_queue.full():
                    self.streaming_queue.put(image_data)
                    self.frame_available.emit()
            except Exception as e:
                print(f"Error handling frame: {str(e)}")

    def stop_stream(self):
        
        """Stop the frame capture thread."""
        try:
            if hasattr(self, 'camera_thread') and self.camera_thread is not None:
                if self.camera_thread.isRunning():
                    self.camera_thread.stop()
                self.camera_thread = None
            print("StreamCamera.stop_stream(): Camera stream stopped.")
            self.camera_control.stop_camera()
        except RuntimeError:
            # Ignore errors if the thread has already been deleted
            pass

    def get_latest_frame(self):
        
        """Retrieve the latest frame from the queue."""
        if not self.streaming_queue.empty():
            return self.streaming_queue.get()
        return None

    def cleanup(self):
        
        """Clean up resources before deletion"""
        self.stop_stream()
        """Clear the queue"""
        while not self.streaming_queue.empty():
            try:
                self.streaming_queue.get_nowait()
            except queue.Empty:
                break