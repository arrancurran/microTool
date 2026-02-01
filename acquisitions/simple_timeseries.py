import threading, time, logging
from datetime import datetime

from .hdf5_handler import HDF5Handler
from .data_queue_handler import ImgDataQueueHandler
from .metadata_builder import build_metadata
from interface.status_bar.update_notif import update_notif

logger = logging.getLogger(__name__)


class SimpleTimeSeries:
    """Acquire a fixed number of frames.

    Supports two modes:
    - "Free run (max speed)": acquire as fast as the camera delivers.
    - "Frame rate mode": use software timing (time.perf_counter) to
      pace acquisitions to a user-defined frame rate.
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
        self.mode = "Free run (max speed)"
        self.requested_framerate = None
        self.metadata_written = False
        self.roi_width = None
        self.roi_height = None
        self.start_time = None

    def start_experiment(self, path=None, num_frames: int = 0, mode: str | None = None, target_fps: float | None = None) -> bool:
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

            # Store mode and requested software frame rate for the
            # acquisition thread.
            self.mode = mode or "Free run (max speed)"
            self.requested_framerate = target_fps if (target_fps is not None and target_fps > 0) else None

            # Handle streaming state
            self.was_streaming = (
                self.stream_camera.live_stream_qthread is not None
                and self.stream_camera.live_stream_qthread.isRunning()
            )
            if self.was_streaming:
                self.window.stop_stream.trigger()

            # Get ROI dimensions
            self.roi_width = self.camera_control.call_camera_command("width", "get")
            self.roi_height = self.camera_control.call_camera_command("height", "get")

            # Initialize queue with ROI dimensions
            self.queue = ImgDataQueueHandler(self.window, self.roi_width, self.roi_height)
            self.queue.reset_stats()

            # Mark experiment start time
            self.start_time = datetime.now()

            # Read the current camera framerate for potential metadata
            # (we avoid any "set framerate" calls here and simply
            # record whatever the camera reports).
            try:
                current_fps = self.camera_control.call_camera_command("framerate", "get")
                self.effective_framerate = current_fps
            except Exception:
                self.effective_framerate = None

            # Initialise HDF5 file. We write an initial metadata
            # block now, and will update it again once acquisition
            # has finished so that fields like Acquired Frames are
            # correct.
            if not self.h5_handler.init_h5File(path=path):
                raise Exception("Failed to create HDF5 file for experiment")

            initial_metadata = build_metadata(
                acquisition_type="Experiment",
                window=self.window,
                camera_control=self.camera_control,
                roi_width=self.roi_width,
                roi_height=self.roi_height,
                start_time=self.start_time,
                requested_frames=num_frames,
                acquired_frames=None,
                mode=self.mode,
                requested_framerate=self.requested_framerate,
                effective_framerate=self.effective_framerate,
            )
            self.h5_handler.set_metadata(initial_metadata)

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

        # Finalise metadata based on what was actually acquired
        if self.queue is not None:
            self._finalise_metadata()

        cleanup_thread = threading.Thread(
            target=self.h5_handler.cleanup,
            args=(self.queue, self.was_streaming, self.window),
            daemon=True,
        )
        cleanup_thread.start()

    def _record_frames(self):
        """Acquire a fixed number of frames into the queue.

        - In "Free run (max speed)" mode, this pulls frames as fast as
          the camera delivers them.
        - In "Frame rate mode", this uses time.perf_counter to pace
          acquisitions to the requested frame rate (software timing).
        """

        frames_captured = 0

        use_timed = (
            self.mode == "Frame rate mode"
            and self.requested_framerate is not None
            and self.requested_framerate > 0
        )

        if use_timed:
            frame_interval = 1.0 / self.requested_framerate
            start_time = time.perf_counter()
            next_time = start_time
            frame_index = 0
        else:
            frame_interval = None
            next_time = None
            frame_index = 0

        while self.is_running and frames_captured < self.requested_frames:
            try:
                if use_timed:
                    now = time.perf_counter()
                    if now < next_time:
                        # Sleep in small chunks to reduce CPU usage.
                        sleep_dt = next_time - now
                        if sleep_dt > 0:
                            time.sleep(min(sleep_dt, 0.005))
                        continue

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

                        # Finalise metadata before cleanup
                        self._finalise_metadata()

                        cleanup_thread = threading.Thread(
                            target=self.h5_handler.cleanup,
                            args=(self.queue, self.was_streaming, self.window),
                            daemon=True,
                        )
                        cleanup_thread.start()
                        break

                    frames_captured += 1

                    if use_timed:
                        frame_index += 1
                        next_time = start_time + frame_index * frame_interval

            except Exception as e:
                logger.error(f"Error during experiment acquisition: {e}")
                time.sleep(0.1)

        # Normal completion path
        if self.is_running:
            # We've reached requested frame count
            self.is_running = False
            self.camera_control.stop_camera()

            # Finalise metadata before cleanup
            self._finalise_metadata()

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
        self.mode = "Free run (max speed)"
        self.requested_framerate = None
        self.metadata_written = False
        self.roi_width = None
        self.roi_height = None
        self.start_time = None

    def _finalise_metadata(self):
        """Build and write metadata once acquisition has finished."""

        if self.metadata_written or not self.h5_handler or not self.h5_handler.create_hdf5:
            return

        acquired_frames = None
        if self.queue is not None:
            try:
                acquired_frames = self.queue.frames_recorded
            except Exception:
                acquired_frames = None

        metadata = build_metadata(
            acquisition_type="Experiment",
            window=self.window,
            camera_control=self.camera_control,
            roi_width=self.roi_width,
            roi_height=self.roi_height,
            start_time=self.start_time,
            requested_frames=self.requested_frames,
            acquired_frames=acquired_frames,
            mode=self.mode,
            requested_framerate=self.requested_framerate,
            effective_framerate=self.effective_framerate,
        )

        self.h5_handler.set_metadata(metadata)
        self.metadata_written = True
