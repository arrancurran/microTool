from PyQt6.QtCore import QObject
import qtawesome as qta
import logging
from datetime import datetime, timedelta

from .camera_controls.control_manager import CameraControlManager
from .status_bar.status_bar_manager import StatusBarManager
from acquisitions.endless_stream import EndlessStream
from acquisitions.snapshot import Snapshot
from acquisitions.simple_timeseries import SimpleTimeSeries
from .ui_img_disp.draw_roi import DrawROI

from .ui_img_disp.ui_display_methods import UIDisplayMethods

from utils import PopupNotifManager

logger = logging.getLogger(__name__)

class UIMethods(QObject):

    def __init__(self, window, stream_camera):
        
        super().__init__()
        self.window = window
        self.stream_camera = stream_camera
        self.camera_control = self.stream_camera.camera_control
        self.snapshot = Snapshot(stream_camera, window)
        self.record_stream = EndlessStream(stream_camera, window)
        self.experiment = SimpleTimeSeries(stream_camera, window)
        self.draw_roi = DrawROI()
        self.popup_manager = PopupNotifManager(self.window)
        
        """Initialize camera controls"""
        self.control_manager = CameraControlManager(self.camera_control, window)
        self.control_manager.initialize_controls()
        
        """Initialize status bar manager"""
        self.status_bar_manager = StatusBarManager(window, self.camera_control)
        self.status_bar_manager.initialize_items()  # Initialize all status bar items
        
        self.image_display = UIDisplayMethods(window, window.image_container, stream_camera, self.camera_control, self.status_bar_manager)
        
        """Connect the Apply ROI button"""
        self.window.apply_roi_button.clicked.connect(self.image_display.handle_apply_roi)
        
        """Connect the Reset ROI button"""
        self.window.reset_roi_button.clicked.connect(self.image_display.handle_reset_roi)

        # Update acquisition estimates when ROI spinboxes change (if present)
        for name in ("roi_width", "roi_height"):
            spin = getattr(self.window, name, None)
            if spin is not None:
                spin.valueChanged.connect(self.update_acquisition_estimates)

        # Connect experiment frame rate field, if present
        if hasattr(self.window, "experiment_framerate_edit"):
            self.window.experiment_framerate_edit.editingFinished.connect(
                self.handle_experiment_framerate_change
            )

        # Connect experiment frames field, if present
        if hasattr(self.window, "experiment_frames_edit"):
            self.window.experiment_frames_edit.editingFinished.connect(
                self.update_acquisition_estimates
            )

        # Track acquisition mode (free run vs frame rate mode)
        self.acquisition_mode = "Free run (max speed)"
        if hasattr(self.window, "acquisition_mode_combo"):
            self.window.acquisition_mode_combo.currentIndexChanged.connect(
                self.handle_acquisition_mode_change
            )
        
        """Set the original image size"""
        self.original_image_size = None
        
    def update_img_display(self):
        self.image_display.update_img_display()
        # Keep the time-series toolbar button in sync with the
        # acquisition state (so it returns to the start icon when
        # a run finishes naturally).
        self._sync_time_series_button()

    def handle_mouse_press(self, event):
        self.image_display.handle_mouse_press(event)

    def handle_mouse_move(self, event):
        self.image_display.handle_mouse_move(event)

    def handle_mouse_release(self, event):
        self.image_display.handle_mouse_release(event)

    def handle_paint(self, painter):
        self.image_display.handle_paint(painter)
        
    def handle_snapshot(self):
        base_path = self._get_experiment_base_path()
        if base_path is None:
            self.popup_manager.show_popup_notif("Set experiment directory and name first")
            return

        if self.snapshot.save_snapshot(base_path):
            self.popup_manager.show_popup_notif("Snapshot Saved", button="Stop")
        else:
            self.popup_manager.show_popup_notif("Failed to Save Snapshot")
    
    def handle_recording(self):
        
        if not hasattr(self.window.start_recording, 'is_recording'):
            self.window.start_recording.is_recording = False
            
        if not self.window.start_recording.is_recording:
            base_path = self._get_experiment_base_path()
            if base_path is None:
                self.popup_manager.show_popup_notif("Set experiment directory and name first")
                return

            if self.record_stream.start_recording(base_path):
                self.window.start_recording.is_recording = True
                # Get the stop recording icon from JSON
                stop_icon = self.window.ui_scaffolding['toolbar']['icons']['Start Recording']['Stop Recording']['icon']
                icon_color = self.window.ui_scaffolding['toolbar']['icons']['Start Recording']['Stop Recording']['icon_color']
                self.window.start_recording.setIcon(qta.icon(stop_icon, color=icon_color))
            else:
                self.popup_manager.show_popup_notif("Failed to Start Recording")
        else:
            self.record_stream.stop_recording()
            self.window.start_recording.is_recording = False
            # Get the start recording icon from JSON
            start_icon = self.window.ui_scaffolding['toolbar']['icons']['Start Recording']['icon']
            self.window.start_recording.setIcon(qta.icon(start_icon))
            self.popup_manager.show_popup_notif("Recording Stopped")

    def handle_experiment(self):
        """Configure and start/stop a fixed-frame time-series acquisition.

        When idle, clicking the toolbar button starts a new time
        series. While a time series is running, clicking it again
        requests a graceful stop and resets the button icon.
        """

        action = getattr(self.window, "start_experiment", None)
        if action is None:
            self.popup_manager.show_popup_notif("Start Time Series action not found in UI")
            return

        # Initialise per-action state flag if needed
        if not hasattr(action, "is_running"):
            action.is_running = False

        # If a time series is already running, treat this as a stop
        # request and return early.
        if action.is_running:
            try:
                self.experiment.stop_time_series()
                action.is_running = False

                # Restore the original start icon
                try:
                    start_icon = self.window.ui_scaffolding["toolbar"]["icons"]["Start Experiment"]["icon"]
                    action.setIcon(qta.icon(start_icon))
                except Exception as e:
                    logger.error(f"Error restoring Start Experiment icon: {e}")

                self.popup_manager.show_popup_notif("Time series stopped")
            except Exception as e:
                logger.error(f"Error stopping time series: {e}")
                self.popup_manager.show_popup_notif("Failed to stop time series")
            return
        # Get number of frames from the Acquisition Settings field
        frames_edit = getattr(self.window, "experiment_frames_edit", None)
        if frames_edit is None:
            self.popup_manager.show_popup_notif("Frames field not found in UI")
            return

        text = frames_edit.text().strip()
        if not text:
            self.popup_manager.show_popup_notif("Enter the number of frames to acquire")
            return

        try:
            frames = int(text)
        except ValueError:
            self.popup_manager.show_popup_notif("Enter a valid integer number of frames")
            return

        if frames <= 0:
            self.popup_manager.show_popup_notif("Number of frames must be positive")
            return

        base_path = self._get_experiment_base_path()
        if base_path is None:
            self.popup_manager.show_popup_notif("Set experiment directory and name first")
            return

        # Determine acquisition mode and target frame rate
        mode = getattr(self, "acquisition_mode", "Free run (max speed)")

        target_fps = None
        edit = getattr(self.window, "experiment_framerate_edit", None)
        if edit is not None:
            text = edit.text().strip()
            if text:
                try:
                    target_fps = float(text)
                except ValueError:
                    self.popup_manager.show_popup_notif("Enter a valid numeric frame rate")
                    return

        if mode == "Frame rate mode" and (target_fps is None or target_fps <= 0):
            self.popup_manager.show_popup_notif("Set a positive frame rate for Frame rate mode")
            return

        if self.experiment.start_time_series(base_path, frames, mode, target_fps):
            # For free-run mode, report the camera's effective
            # framerate. For frame-rate mode, report the user-set
            # target fps (software pacing) so the popup matches what
            # the user requested rather than the hardware max.
            if mode == "Frame rate mode" and target_fps is not None:
                effective_fps = target_fps
            else:
                effective_fps = self.experiment.effective_framerate

            if effective_fps is not None:
                msg = f"Experiment started: {frames} frames @ {effective_fps:.1f} Hz"
            else:
                msg = f"Experiment started: {frames} frames"
            self.popup_manager.show_popup_notif(msg)

            # Update toolbar button to a red "stop" icon while the
            # time series is running.
            try:
                stop_icon = self.window.ui_scaffolding["toolbar"]["icons"]["Start Recording"]["Stop Recording"]["icon"]
                icon_color = self.window.ui_scaffolding["toolbar"]["icons"]["Start Recording"]["Stop Recording"]["icon_color"]
                action.setIcon(qta.icon(stop_icon, color=icon_color))
            except Exception as e:
                logger.error(f"Error setting Stop icon for time series: {e}")

            action.is_running = True
        else:
            self.popup_manager.show_popup_notif("Failed to start experiment")

    def handle_acquisition_mode_change(self, index: int):
        """Update the stored acquisition mode when the user changes it."""
        combo = getattr(self.window, "acquisition_mode_combo", None)
        if combo is None:
            return
        self.acquisition_mode = combo.currentText()
        self.update_acquisition_estimates()

    def handle_experiment_framerate_change(self):
        """Handle changes to the experiment frame rate field.

        Validates against the camera's current max framerate. If the
        requested value is higher than the max, it is clamped to the max
        and the user is notified. The resulting value is applied via the
        existing framerate slider/camera control.
        """

        edit = getattr(self.window, "experiment_framerate_edit", None)
        if edit is None:
            return

        text = edit.text().strip()
        if not text:
            return

        try:
            requested_fps = float(text)
        except ValueError:
            self.popup_manager.show_popup_notif("Enter a valid numeric frame rate")
            return

        # Query current maximum framerate from camera
        try:
            framerate_max = self.camera_control.call_camera_command("framerate_max", "get")
        except Exception:
            framerate_max = None

        target_fps = requested_fps
        if framerate_max is not None and requested_fps > framerate_max:
            target_fps = float(framerate_max)
            # Notify user about clamping
            self.popup_manager.show_popup_notif(
                f"Requested {requested_fps:.1f} Hz exceeds max {framerate_max:.1f} Hz; using {target_fps:.1f} Hz"
            )

        # Update the field to reflect the effective value
        edit.setText(f"{target_fps:.1f}")

        # Apply via framerate slider if available so existing control
        # handling (clamping, status bar updates) is reused.
        if hasattr(self.window, "framerate_slider"):
            try:
                self.window.framerate_slider.setValue(int(round(target_fps)))
                return
            except Exception as e:
                logger.error(f"Error updating framerate slider from experiment field: {e}")

        # We intentionally avoid setting the hardware framerate here,
        # since the connected camera does not support a frame-rate
        # timing mode. The slider value can still be used by higher-
        # level acquisition logic (e.g. for software pacing).

        # Update acquisition estimates using the new (possibly clamped)
        # value.
        self.update_acquisition_estimates()

    def _sync_time_series_button(self):
        """Ensure the Start Experiment button reflects acquisition state.

        If the time series acquisition has finished (is_running is
        False) but the toolbar action still thinks it is running, reset
        the icon and flag. This handles the natural completion case
        without requiring explicit callbacks from the worker thread.
        """

        action = getattr(self.window, "start_experiment", None)
        if action is None:
            return

        running = getattr(self.experiment, "is_running", False)
        ui_running = getattr(action, "is_running", False)

        if (not running) and ui_running:
            try:
                start_icon = self.window.ui_scaffolding["toolbar"]["icons"]["Start Experiment"]["icon"]
                action.setIcon(qta.icon(start_icon))
            except Exception as e:
                logger.error(f"Error syncing Start Experiment icon: {e}")
            action.is_running = False

    def _get_experiment_base_path(self):
        """Combine experiment directory and name from the UI.

        Returns a base path without extension, or None if either field is
        missing.
        """
        directory = getattr(self.window, "experiment_dir_edit", None)
        name = getattr(self.window, "experiment_name_edit", None)

        if directory is None or name is None:
            return None

        dir_text = directory.text().strip()
        name_text = name.text().strip()

        if not dir_text or not name_text:
            return None

        # Do not append extension here; individual acquisitions add it.
        from os import path
        return path.join(dir_text, name_text)

    def update_acquisition_estimates(self):
        """Update estimated acquisition time and file size in the UI.

        - Time is based on number of frames and effective frame rate:
          * Free run: use camera framerate_max.
          * Frame rate mode: use user-defined frame rate.
        - Size is based on ROI (width x height) and number of frames.
        """

        # Obtain ROI dimensions from UI spinboxes if available
        roi_width = None
        roi_height = None

        width_spin = getattr(self.window, "roi_width", None)
        height_spin = getattr(self.window, "roi_height", None)

        if width_spin is not None and height_spin is not None:
            roi_width = width_spin.value()
            roi_height = height_spin.value()

        # Fallback: try camera for ROI dimensions
        if roi_width is None or roi_height is None:
            try:
                roi_width = int(self.camera_control.call_camera_command("width", "get"))
                roi_height = int(self.camera_control.call_camera_command("height", "get"))
            except Exception:
                roi_width = None
                roi_height = None

        # Number of frames
        frames = None
        frames_edit = getattr(self.window, "experiment_frames_edit", None)
        if frames_edit is not None:
            text = frames_edit.text().strip()
            if text:
                try:
                    value = int(text)
                    if value > 0:
                        frames = value
                except ValueError:
                    pass

        # Determine effective frame rate for estimate
        fps = None
        mode = getattr(self, "acquisition_mode", "Free run (max speed)")
        if mode == "Frame rate mode":
            edit = getattr(self.window, "experiment_framerate_edit", None)
            if edit is not None:
                text = edit.text().strip()
                if text:
                    try:
                        value = float(text)
                        if value > 0:
                            fps = value
                    except ValueError:
                        pass
        else:
            # Free run: use camera's maximum framerate if available
            try:
                value = self.camera_control.call_camera_command("framerate_max", "get")
                if value is not None and float(value) > 0:
                    fps = float(value)
            except Exception:
                fps = None

        # Compute estimated time and end time (ETA)
        time_str = "-"
        eta_suffix = ""
        if frames is not None and fps is not None and fps > 0:
            total_seconds = frames / fps
            if total_seconds < 60:
                time_str = f"{total_seconds:.1f} s"
            else:
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)
                if hours > 0:
                    time_str = f"{hours} h {minutes} min"
                else:
                    time_str = f"{minutes} min"

            try:
                eta_time = datetime.now() + timedelta(seconds=total_seconds)
                eta_suffix = f" (finishes ≈ {eta_time.strftime('%H:%M')})"
            except Exception:
                eta_suffix = ""

        # Compute estimated file size based on ROI and frames
        size_str = "-"
        if roi_width is not None and roi_height is not None and frames is not None:
            total_bytes = roi_width * roi_height * frames
            if total_bytes >= 1024 ** 3:
                size_str = f"{total_bytes / (1024 ** 3):.2f} GB"
            elif total_bytes >= 1024 ** 2:
                size_str = f"{total_bytes / (1024 ** 2):.2f} MB"
            elif total_bytes >= 1024:
                size_str = f"{total_bytes / 1024:.2f} KB"
            else:
                size_str = f"{total_bytes} B"

        # Update labels in Acquisition Settings, if present
        time_label = getattr(self.window, "experiment_est_time_label", None)
        size_label = getattr(self.window, "experiment_est_size_label", None)

        if time_label is not None:
            time_label.setText(f"Estimated time: {time_str}{eta_suffix}")
        if size_label is not None:
            size_label.setText(f"Estimated size: {size_str}")
    
    def cleanup(self):
        
        """Clean up resources."""
        self.control_manager.cleanup()