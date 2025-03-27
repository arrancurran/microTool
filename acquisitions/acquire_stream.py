import threading, time, logging
from datetime import datetime
import qtawesome as qta

from .hdf5_handler import HDF5Handler
from .data_queue_handler import ImgDataQueueHandler
from interface.status_bar.update_notif import update_notif
from utils import get_computer_name

logger = logging.getLogger(__name__)

class AcquireStream:
    """Handles continuous recording of camera frames to a queue."""
    
    def __init__(self, stream_camera, window):
        self.stream_camera = stream_camera
        self.camera_control = stream_camera.camera_control
        self.window = window
        self.h5_handler = HDF5Handler()
        
        # Initialize recording state
        self.queue = None
        self.camera_aq__thread = None
        self.is_recording = False
        self.was_streaming = False
        
        # Connect stop signal to window
        self.window.start_recording.triggered.connect(self.stop_recording)
        
    def start_recording(self):
        """Start recording frames from camera."""
        logging.info("Starting Recording")
        if self.is_recording:
            return False
            
        try:
            # Handle streaming state
            self.was_streaming = (self.stream_camera.live_stream_qthread is not None and self.stream_camera.live_stream_qthread.isRunning())
            if self.was_streaming:
                self.window.stop_stream.trigger()
            
            # Get ROI dimensions
            roi_width = self.camera_control.call_camera_command("width", "get")
            roi_height = self.camera_control.call_camera_command("height", "get")
            
            # Initialize queue with ROI dimensions
            self.queue = ImgDataQueueHandler(self.window, roi_width, roi_height)
            self.queue.reset_stats()
            
            # Initialize recording
            metadata = {
                'computer_name': get_computer_name(),
                'camera_model': self.camera_control.camera.get_device_name().decode('utf-8'),
                'timestamp': datetime.now().isoformat(),
                'exposure': self.camera_control.call_camera_command("exposure", "get"),
                'roi_width': roi_width,
                'roi_height': roi_height,
                'roi_offset_x': self.camera_control.call_camera_command("offset_x", "get"),
                'roi_offset_y': self.camera_control.call_camera_command("offset_y", "get")
            }
            
            if not self.h5_handler.init_h5File(metadata):
                raise Exception("Failed to start HDF5 logger")
            
            # Start recording thread and saving
            self.is_recording = True
            self.camera_aq__thread = threading.Thread(target=self._record_frames, name="CameraAQThread", daemon=True)
            self.camera_aq__thread.start()
            
            # Start saving frames
            if not self.h5_handler.init_saving_thread(self.queue):
                raise Exception("Failed to start saving thread")
            
            self.camera_control.start_camera()
            update_notif("Recording Live Stream")
            return True
            
        except Exception as e:
            logger.error(f"Error Starting Recording: {e}")
            update_notif(f"Error Starting Recording: {e}")
            self.is_recording = False
            self._cleanup()
            return False
            
    def stop_recording(self):
        """Stop recording and save remaining frames."""
        if not self.is_recording:
            return
            
        # Stop recording
        self.is_recording = False
        self.camera_control.stop_camera()
        
        if self.camera_aq__thread:
            self.camera_aq__thread.join(timeout=5.0)  # Wait up to 5 seconds for recording to stop
        
        # Start cleanup in background
        cleanup_thread = threading.Thread(
            target=self.h5_handler.cleanup,
            args=(self.queue, self.was_streaming, self.window),
            daemon=True
        )
        cleanup_thread.start()

    def _record_frames(self):
        """Record frames from camera to queue."""
        while self.is_recording:
            try:
                self.camera_control.get_image()
                timestamp = self.camera_control.get_image_timestamp()
                frame = self.camera_control.get_image_data()
                
                if frame is not None:
                    if not self.queue.put_frame(frame, timestamp):
                        # If queue is full, stop recording
                        logger.debug("Queue Full - Stopping Stream")
                        update_notif("Queue Full - Stopping Stream", duration=2000)
                        self.is_recording = False
                        self.camera_control.stop_camera()
                        
                        # Start cleanup in background
                        cleanup_thread = threading.Thread(
                            target=self.h5_handler.cleanup,
                            args=(self.queue, self.was_streaming, self.window),
                            daemon=True
                        )
                        cleanup_thread.start()
                        
                        # Update UI state
                        self.window.start_recording.is_recording = False
                        self.window.start_recording.setIcon(qta.icon("fa5.dot-circle"))
                        break
                        
            except Exception as e:
                logger.error(f"Error recording frame: {e}")
                time.sleep(0.1) 

    def _cleanup(self):
        self.queue = None
        self.camera_aq__thread = None
        self.was_streaming = False
        self.is_recording = False
        self.h5_handler = None
        self.window = None
        self.camera_control = None