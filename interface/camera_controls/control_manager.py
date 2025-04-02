from typing import Dict
import logging

from .base_control import CameraControl
from .exposure_control import ExposureControl
from .roi_control import ROIControl
from .framerate_control import FramerateControl

logger = logging.getLogger(__name__)

class CameraControlManager:
    
    # Register all camera control here
    CONTROL_TYPES = {
        'exposure': ExposureControl,
        'roi': ROIControl,
        'framerate': FramerateControl,
        # Add new controls like:
        # 'gain': GainControl,
    }
    
    def __init__(self, camera_control, window):
        self.camera_control = camera_control
        self.window = window
        self.controls: Dict[str, CameraControl] = {}
        
    def initialize_controls(self):
        for control_name, control_class in self.CONTROL_TYPES.items():
            try:
                control = control_class(self.camera_control, self.window)
                if control.setup_ui():
                    self.controls[control_name] = control
            except Exception as e:
                logger.error(f"Error initializing {control_name} control: {str(e)}")
    
    def get_control(self, control_name: str) -> CameraControl:
        control = self.controls.get(control_name)
        if control is None:
            logger.warning(f"Warning: Control '{control_name}' not found")  # Debug print
        return control
    
    def cleanup(self):
        for control_name, control in self.controls.items():
            try:
                if hasattr(control, 'cleanup'):
                    control.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up {control_name} control: {str(e)}")
        logger.debug("Finished cleaning up controls")  # Debug print 