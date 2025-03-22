from PyQt6.QtCore import QObject, pyqtSignal, QThread, QTimer
import queue
import time

class CameraThread(QThread):
    """Thread for capturing camera frames"""
    frame_ready = pyqtSignal(object)  # Signal to emit when a new frame is ready
    
    def __init__(self, camera_control):
        super().__init__()
        self.camera_control = camera_control
        self.running = True
        self.frame_interval = 33  # Fixed 30 Hz (1000ms/30 ≈ 33.33ms)
        self.frame_count = 0
        self.last_fps_update = 0
        self.fps_update_interval = 1.0  # Update FPS every second
        
    def run(self):
        """Main thread loop"""
        while self.running:
            try:
                # Sleep for the frame interval before getting next image
                time.sleep(self.frame_interval / 1000.0)
                
                # Get image from camera
                self.camera_control.get_image()
                image_data = self.camera_control.get_image_data()
                
                if image_data is not None:
                    self.frame_ready.emit(image_data)
                    self.frame_count += 1
                
                # Update FPS counter every second
                current_time = time.time()
                if current_time - self.last_fps_update >= self.fps_update_interval:
                    fps = self.frame_count / (current_time - self.last_fps_update)
                    print(f"Camera FPS: {fps:.1f}")
                    self.frame_count = 0
                    self.last_fps_update = current_time
                
            except Exception as e:
                print(f"Error in camera thread: {str(e)}")
                time.sleep(0.1)  # Sleep briefly on error to prevent tight loop
    
    def stop(self):
        """Stop the thread"""
        self.running = False
        self.wait()

class StreamCamera(QObject):
    """Main camera streaming class that manages the camera thread"""
    frame_ready = pyqtSignal()  # Signal to emit when a new frame is ready
    
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
            self.camera_thread.frame_ready.connect(self._handle_frame)
            self.camera_control.start_camera()
            self.camera_thread.start()
            print("StreamCamera.start_stream(): Camera stream started.")

    def _handle_frame(self, image_data):
        """Handle a new frame from the camera thread"""
        if not self.streaming_queue.full():
            self.streaming_queue.put(image_data)
            self.frame_ready.emit()

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
        # Clear the queue
        while not self.streaming_queue.empty():
            try:
                self.streaming_queue.get_nowait()
            except queue.Empty:
                break