from PyQt6.QtCore import QObject
import qtawesome as qta
import logging

from .camera_controls.control_manager import CameraControlManager
from .status_bar.status_bar_manager import StatusBarManager
from acquisitions.acquire_stream import AcquireStream
from acquisitions.snapshot import Snapshot
from .ui_img_disp.draw_roi import DrawROI

from .ui_img_disp.ui_display_methods import UIDisplayMethods

from utils import PopupNotifManager

from utils.popup_path import popup_request_path  # adjust the import path as needed


logger = logging.getLogger(__name__)

class UIMethods(QObject):

    def __init__(self, window, stream_camera):
        
        super().__init__()
        self.window = window
        self.stream_camera = stream_camera
        self.camera_control = self.stream_camera.camera_control
        self.snapshot = Snapshot(stream_camera, window)
        self.record_stream = AcquireStream(stream_camera, window)
        self.draw_roi = DrawROI()
        self.popup_manager = PopupNotifManager(self.window)
        
        self.popup_request_path = popup_request_path
        
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
        snapshot_path = self.popup_request_path()
        if snapshot_path is not None:
            self.snapshot.save_snapshot(snapshot_path)
            self.popup_manager.show_popup_notif("Snapshot Saved", button="Stop")  # Uncommented to show notification
        else:
            self.popup_manager.show_popup_notif("Failed to Save Snapshot")
    
    def handle_recording(self):
        
        if not hasattr(self.window.start_recording, 'is_recording'):
            self.window.start_recording.is_recording = False
            
        if not self.window.start_recording.is_recording:
            
            recording_path = self.popup_request_path()
            
            if self.record_stream.start_recording(recording_path):
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
    
    def cleanup(self):
        
        """Clean up resources."""
        self.control_manager.cleanup()