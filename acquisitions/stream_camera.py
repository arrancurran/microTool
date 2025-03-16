import threading, queue
from instruments.xicam.cam_methods import CameraControl, CameraSettings, CameraSequences

camera_control = CameraControl()

class StreamCamera:
    def __init__(self, camera_control):
        """Initialize the camera and streaming components."""
        self.camera_control = camera_control
        self.camera = None
        self.frame_queue = queue.Queue(maxsize=10)  # Buffer for frames
        self.streaming = threading.Event()  # Controls start/stop of streaming
        self.stream_thread = None  # Thread for capturing frames

    def start_stream(self):
        """Start capturing frames in a separate thread."""
        if not self.streaming.is_set():
            self.streaming.set()
            self.stream_thread = threading.Thread(target=self._capture_frames, daemon=True)
            self.stream_thread.start()
            print("Camera streaming started.")

    def _capture_frames(self):
        """Continuously capture frames and put them in a queue."""
        while self.streaming.is_set():
            self.camera_control.get_image()
            image_data = self.camera_control.get_image_data()

            # Ensure the queue doesn't overflow
            if not self.frame_queue.full():
                self.frame_queue.put(image_data)

    def stop_stream(self):
        """Stop the frame capture thread."""
        if self.streaming.is_set():
            self.streaming.clear()
            self.stream_thread.join()  # Wait for thread to exit
            print("Camera streaming stopped.")

    def get_latest_frame(self):
        """Retrieve the latest frame from the queue."""
        if not self.frame_queue.empty():
            return self.frame_queue.get()
        return None