import threading, queue
from instruments.xicam.cam_methods import CameraControl, CameraSettings, CameraSequences
import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal


camera_control = CameraControl()

class StreamCamera(QObject):
    
    frame_ready = pyqtSignal()  # Signal to emit when a new frame is ready

    def __init__(self, camera_control):
        """Initialize the camera and streaming components."""
        super().__init__()
        self.camera_control = camera_control
        self.camera = None
        self.streaming_queue = queue.Queue(maxsize=10)  # Buffer for frames
        self.streaming = threading.Event()  # Controls start/stop of streaming
        self.stream_thread = None  # Thread for capturing frames

    def start_stream(self):
        """Start capturing frames in a separate thread."""
        if not self.streaming.is_set():
            self.streaming.set()
            self.stream_thread = threading.Thread(target=self._capture_frames, daemon=True)
            self.stream_thread.start()
            print("StreamCamera.start_stream(): Camera stream started.")

    def _capture_frames(self):
        """Continuously capture frames and put them in a queue."""
        while self.streaming.is_set():
            self.camera_control.get_image()
            image_data = self.camera_control.get_image_data()

            # Ensure the queue doesn't overflow
            if not self.streaming_queue.full():
                self.streaming_queue.put(image_data)
                self.frame_ready.emit()  # Emit signal when new frame is ready

    def stop_stream(self):
        """Stop the frame capture thread."""
        if self.streaming.is_set():
            self.streaming.clear()
            self.stream_thread.join()  # Wait for thread to exit
            print("StreamCamera.stop_stream(): Camera stream stopped.")

    def get_latest_frame(self):
        """Retrieve the latest frame from the queue."""
        if not self.streaming_queue.empty():
            return self.streaming_queue.get()
        return None