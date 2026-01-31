import threading, time, logging
from datetime import datetime

from .hdf5_handler import HDF5Handler
from .data_queue_handler import ImgDataQueueHandler
from interface.status_bar.update_notif import update_notif
from utils import get_computer_name

logger = logging.getLogger(__name__)


class AcquireExperiment:
    """Acquire a fixed number of frames at the current camera framerate.

    The effective framerate is always clamped so it does not exceed the
    camera's current maximum framerate capability.
    """

    def __init__(self, stream_camera, window):
        self.stream_camera = stream_camera
        self.camera_control = stream_camera.camera_control
        self.window = window
        self.h5_handler = HDF5Handler()

        self.queue = None
        self.experiment_thread = None
        self.is_running = False
        self.was_streaming = False

        self.requested_frames = 0
        self.effective_framerate = None

    def start_experiment(self, path=None, num_frames: int = 0) -> bool:
        """Start an experiment acquisition.

        Parameters
        ----------
        path : str
            Base path (without extension) for the output HDF5 file.
        num_frames : int
            Number of frames to acquire.
        """

        if self.is_running:
            logger.warning("Experiment acquisition already running")
            return False

        if not path or num_frames <= 0:
            logger.error("Invalid experiment parameters: path or num_frames")
            return False

        try:
            logger.info(f"Starting experiment acquisition for {num_frames} frames")

            # Handle streaming state
            self.was_streaming = (
                self.stream_camera.live_stream_qthread is not None
                and self.stream_camera.live_stream_qthread.isRunning()
            )
            if self.was_streaming:
                self.window.stop_stream.trigger()

            # Get ROI dimensions
            roi_width = self.camera_control.call_camera_command("width", "get")
            roi_height = self.camera_control.call_camera_command("height", "get")

            # Initialize queue with ROI dimensions
            self.queue = ImgDataQueueHandler(self.window, roi_width, roi_height)
            self.queue.reset_stats()

            # Determine current and maximum framerate, and clamp if needed
            framerate_max = self.camera_control.call_camera_command("framerate_max", "get")
            current_fps = self.camera_control.call_camera_command("framerate", "get")

            self.effective_framerate = current_fps

            if (
                framerate_max is not None
                and current_fps is not None
                and current_fps > framerate_max
            ):
                # Clamp to max and apply to camera
                self.effective_framerate = framerate_max
                logger.info(
                    f"Requested framerate {current_fps} Hz exceeds camera max "
                    f"{framerate_max} Hz. Clamping to max."
                )

                # Apply clamped value to camera
                self.camera_control.call_camera_command(
                    "framerate", "set", self.effective_framerate
                )

                # Update UI control to show the clamped value
                try:
                    if hasattr(self.window, "framerate_slider"):
                        self.window.framerate_slider.blockSignals(True)
                        self.window.framerate_slider.setValue(int(round(self.effective_framerate)))
                        self.window.framerate_slider.blockSignals(False)
                    if hasattr(self.window, "framerate_label") and self.effective_framerate is not None:
                        self.window.framerate_label.setText(
                            f"Framerate: {self.effective_framerate:.1f} Hz"
                        )
                except Exception as ui_err:
                    logger.error(f"Error updating framerate UI after clamping: {ui_err}")

            # Prepare metadata
            metadata = {
                "Computer Name": get_computer_name(),
                "Acquisition Type": "Experiment",
                "Software Name": "microTool",
                "Software Version": "v1.0",
                "Camera Model": self.camera_control.camera.get_device_name().decode("utf-8"),
                "Start Time": datetime.now().isoformat(),
                "Exposure": self.camera_control.call_camera_command("exposure", "get"),
                "Framerate": float(self.effective_framerate) if self.effective_framerate is not None else None,
                "Requested Frames": int(num_frames),
                "ROI Width": roi_width,
                "ROI Height": roi_height,
                "ROI Offset X": self.camera_control.call_camera_command("offset_x", "get"),
                "ROI Offset Y": self.camera_control.call_camera_command("offset_y", "get"),
            }

            if not self.h5_handler.init_h5File(metadata, path):
                raise Exception("Failed to create HDF5 file for experiment")

            # Start acquisition thread and saving
            self.is_running = True
            self.requested_frames = num_frames

            self.experiment_thread = threading.Thread(
                target=self._record_frames, name="ExperimentAQThread", daemon=True
            )
            self.experiment_thread.start()

            if not self.h5_handler.init_saving_thread(self.queue):
                raise Exception("Failed to start saving thread for experiment")

            # Start camera after everything is ready
            self.camera_control.start_camera()
            update_notif(f"Experiment: acquiring {num_frames} frames")
            return True

        except Exception as e:
            logger.error(f"Error starting experiment acquisition: {e}")
            update_notif(f"Error starting experiment: {e}")
            self.is_running = False
            self._cleanup_on_error()
            return False

    def stop_experiment(self):
        """Request a graceful stop of the experiment acquisition."""
        if not self.is_running:
            return

        self.is_running = False
        self.camera_control.stop_camera()

        if self.experiment_thread:
            self.experiment_thread.join(timeout=5.0)

        cleanup_thread = threading.Thread(
            target=self.h5_handler.cleanup,
            args=(self.queue, self.was_streaming, self.window),
            daemon=True,
        )
        cleanup_thread.start()

    def _record_frames(self):
        """Acquire a fixed number of frames into the queue."""
        frames_captured = 0

        while self.is_running and frames_captured < self.requested_frames:
            try:
                self.camera_control.get_image()
                timestamp = self.camera_control.get_image_timestamp()
                frame = self.camera_control.get_image_data()

                if frame is not None:
                    if not self.queue.put_frame(frame, timestamp):
                        # If queue is full, stop experiment
                        logger.debug("Queue full during experiment - stopping acquisition")
                        update_notif("Queue full - stopping experiment", duration=2000)
                        self.is_running = False
                        self.camera_control.stop_camera()

                        cleanup_thread = threading.Thread(
                            target=self.h5_handler.cleanup,
                            args=(self.queue, self.was_streaming, self.window),
                            daemon=True,
                        )
                        cleanup_thread.start()
                        break

                    frames_captured += 1

            except Exception as e:
                logger.error(f"Error during experiment acquisition: {e}")
                time.sleep(0.1)

        # Normal completion path
        if self.is_running:
            # We've reached requested frame count
            self.is_running = False
            self.camera_control.stop_camera()

            cleanup_thread = threading.Thread(
                target=self.h5_handler.cleanup,
                args=(self.queue, self.was_streaming, self.window),
                daemon=True,
            )
            cleanup_thread.start()

    def _cleanup_on_error(self):
        """Internal cleanup helper for error paths."""
        self.queue = None
        self.experiment_thread = None
        self.was_streaming = False
        self.requested_frames = 0
        self.effective_framerate = None
