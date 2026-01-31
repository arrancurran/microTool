from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QInputDialog
import qtawesome as qta
import logging

from .camera_controls.control_manager import CameraControlManager
from .status_bar.status_bar_manager import StatusBarManager
from acquisitions.acquire_stream import AcquireStream
from acquisitions.snapshot import Snapshot
from acquisitions.acquire_experiment import AcquireExperiment
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
        self.record_stream = AcquireStream(stream_camera, window)
        self.experiment = AcquireExperiment(stream_camera, window)
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

        # Connect experiment frame rate field, if present
        if hasattr(self.window, "experiment_framerate_edit"):
            self.window.experiment_framerate_edit.editingFinished.connect(
                self.handle_experiment_framerate_change
            )
        
        """Set the original image size"""
        self.original_image_size = None
        
    def update_img_display(self):
        self.image_display.update_img_display()

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
        """Configure and start a fixed-frame experiment acquisition.

        Uses the current camera framerate (which is itself clamped to the
        camera's max) and prompts the user only for the number of frames
        and output path.
        """

        # Request number of frames
        frames, ok = QInputDialog.getInt(
            self.window,
            "Experiment Setup",
            "Number of frames:",
            value=100,
            min=1,
        )
        if not ok:
            return

        base_path = self._get_experiment_base_path()
        if base_path is None:
            self.popup_manager.show_popup_notif("Set experiment directory and name first")
            return

        if self.experiment.start_experiment(base_path, frames):
            # Read back the effective framerate for user feedback
            effective_fps = self.experiment.effective_framerate
            if effective_fps is not None:
                msg = f"Experiment started: {frames} frames @ {effective_fps:.1f} Hz"
            else:
                msg = f"Experiment started: {frames} frames"
            self.popup_manager.show_popup_notif(msg)
        else:
            self.popup_manager.show_popup_notif("Failed to start experiment")

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

        # Fallback: set camera framerate directly
        try:
            self.camera_control.call_camera_command("framerate", "set", target_fps)
        except Exception as e:
            logger.error(f"Error setting camera framerate from experiment field: {e}")

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
    
    def cleanup(self):
        
        """Clean up resources."""
        self.control_manager.cleanup()