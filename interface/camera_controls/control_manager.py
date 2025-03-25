"""
Manager for all camera controls.
"""
from typing import Dict
import logging

from .base_control import CameraControl
from .exposure_control import ExposureControl
from .roi_control import ROIControl
from .framerate_control import FramerateControl

logger = logging.getLogger(__name__)

class CameraControlManager:
    """Manages all camera controls and their initialization."""
    
    # Register new control types here
    CONTROL_TYPES = {
        'exposure': ExposureControl,
        'roi': ROIControl,
        'framerate': FramerateControl,
        # Add new controls like:
        # 'gain': GainControl,
    }
    
    def __init__(self, camera_control, window):
        logger.debug("Initializing CameraControlManager")  # Debug print
        self.camera_control = camera_control
        self.window = window
        self.controls: Dict[str, CameraControl] = {}
        
    def initialize_controls(self):
        """Initialize all registered control types."""
        logger.debug(f"Initializing {len(self.CONTROL_TYPES)} camera controls...")  # Debug print
        for control_name, control_class in self.CONTROL_TYPES.items():
            logger.debug(f"Setting up {control_name} control...")  # Debug print
            try:
                control = control_class(self.camera_control, self.window)
                if control.setup_ui():
                    self.controls[control_name] = control
                    logger.debug(f"Successfully initialized {control_name} control")
                else:
                    logger.error(f"Failed to initialize {control_name} control - setup_ui returned False")
            except Exception as e:
                logger.error(f"Error initializing {control_name} control: {str(e)}")
        logger.debug(f"Finished initializing controls. Active controls: {list(self.controls.keys())}")  # Debug print
    
    def get_control(self, control_name: str) -> CameraControl:
        """Get a specific control by name."""
        control = self.controls.get(control_name)
        if control is None:
            logger.warning(f"Warning: Control '{control_name}' not found")  # Debug print
        return control
    
    def cleanup(self):
        """Cleanup all controls."""
        logger.debug("Cleaning up camera controls...")  # Debug print
        for control_name, control in self.controls.items():
            try:
                if hasattr(control, 'cleanup'):
                    control.cleanup()
                    logger.debug(f"Cleaned up {control_name} control")  # Debug print
            except Exception as e:
                logger.error(f"Error cleaning up {control_name} control: {str(e)}")
        logger.debug("Finished cleaning up controls")  # Debug print 