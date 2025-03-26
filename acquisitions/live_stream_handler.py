
import queue, time, logging
from PyQt6.QtCore import QObject, pyqtSignal, QThread

logger = logging.getLogger(__name__)

class LiveStreamQThread(QThread):

    live_img_acq_qtSignal = pyqtSignal(object) # Signal to emit when a new frame has been captured from the camera
    
    def __init__(self, camera_control):
        super().__init__()
        self.camera_control = camera_control
        self.live_is_running = True
        self.live_stream_freq = 60

    def run(self):
        while self.live_is_running:
            try:
                time.sleep(1/self.live_stream_freq)
                
                self.camera_control.get_image()
                image_data = self.camera_control.get_image_data()
                
                if image_data is not None:
                    self.live_img_acq_qtSignal.emit(image_data)
                
            except Exception as e:
                logger.error(f"Error in camera thread: {str(e)}")
                time.sleep(0.1)  # Sleep briefly on error to prevent hammering CPU on error
    
    def stop(self):
        self.live_is_running = False
        self.wait()

class LiveStreamHandler(QObject):

    live_img_in_queue_qtSignal = pyqtSignal() # Signal to emit when a new frame is available in the queue
    
    def __init__(self, camera_control):
        super().__init__()
        self.camera_control = camera_control
        self.camera = None
        self.live_stream_queue = queue.Queue(maxsize=1)
        self.live_stream_qthread = None

    def start_stream(self):
        if self.live_stream_qthread is None or not self.live_stream_qthread.isRunning():
            self.live_stream_qthread = LiveStreamQThread(self.camera_control)
            self.live_stream_qthread.live_img_acq_qtSignal.connect(self._handle_frame)
            self.camera_control.start_camera()
            self.live_stream_qthread.start()

    def _handle_frame(self, image_data):
        """Handle a new frame from the camera thread with throttling"""
        current_time = time.time()
        # Only process frame if enough time has passed (limit to 30 FPS for UI)
        if not hasattr(self, '_last_frame_time') or (current_time - self._last_frame_time) >= 0.033:
            self._last_frame_time = current_time

            try:
                if not self.live_stream_queue.full():
                    self.live_stream_queue.put(image_data)
                    self.live_img_in_queue_qtSignal.emit()
            except Exception as e:
                logger.error(f"Error handling frame: {str(e)}")

    def stop_stream(self):
        try:
            if hasattr(self, 'live_stream_qthread') and self.live_stream_qthread is not None:
                if self.live_stream_qthread.isRunning():
                    self.live_stream_qthread.stop()
                self.live_stream_qthread = None
            self.camera_control.stop_camera()
            logger.debug("Camera stream stopped.")
        except RuntimeError: # Ignore errors if the thread has already been deleted
            pass

    def get_img_from_queue(self):
        if not self.live_stream_queue.empty():
            return self.live_stream_queue.get()
        return None

    def cleanup(self):
        self.stop_stream()
        while not self.live_stream_queue.empty():
            try:
                self.live_stream_queue.get_nowait()
            except queue.Empty:
                break