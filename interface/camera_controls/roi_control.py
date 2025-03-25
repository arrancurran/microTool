"""Controls for camera Region of Interest (ROI) settings - width, height, and offsets."""
from .base_control import NumericCameraControl
import logging

logger = logging.getLogger(__name__)

class ROIControl(NumericCameraControl):
    """
    Controls camera Region of Interest (ROI) settings via spinboxes in the UI.
    Called by the main app to initialize camera controls.
    Example usage:
        roi_control = ROIControl(camera_control, window)
        roi_control.setup_ui()  # Configures spinboxes with camera's ROI limits
    """
    
    def __init__(self, camera_control, window):
        super().__init__(
            camera_control=camera_control,
            window=window,
            command_name="roi",  # Not actually used, we handle commands directly
            display_name="ROI"
        )
        # Store references to spinboxes and their corresponding camera commands
        self.controls = {
            'width': (window.roi_width, 'width'),
            'height': (window.roi_height, 'height'),
            'offset_x': (window.roi_offset_x, 'offset_x'),
            'offset_y': (window.roi_offset_y, 'offset_y')
        }
        
        # Cache for max dimensions
        self.max_dimensions = None
        
    def setup_ui(self) -> bool:
        """Set up the ROI UI elements."""
        try:
            # Get max dimensions from camera
            self.max_dimensions = {
                'width': self.camera_control.call_camera_command("width_max", "get"),
                'height': self.camera_control.call_camera_command("height_max", "get")
            }
            
            if not all(v is not None for v in self.max_dimensions.values()):
                logger.error("Failed to get max dimensions from camera")
                return False
                
            # Set up each control
            for control_name, (spinbox, command) in self.controls.items():
                try:
                    # Get min/max/current values
                    min_val = self.camera_control.call_camera_command(f"{command}_min", "get")
                    max_val = self.camera_control.call_camera_command(f"{command}_max", "get")
                    inc_val = self.camera_control.call_camera_command(f"{command}_inc", "get")
                    current = self.camera_control.call_camera_command(command, "get")
                    
                    
                    if all(v is not None for v in [min_val, max_val, inc_val, current]):
                        # Configure spinbox
                        spinbox.setMinimum(min_val)
                        spinbox.setMaximum(max_val)
                        spinbox.setSingleStep(inc_val)
                        
                        logger.debug(f"{control_name} control set up with max: {max_val}, min: {min_val}, inc: {inc_val}, current: {current}")
                         # Connect signal
                        spinbox.valueChanged.connect(lambda v, c=command: self.handle_value_change(v, c))
                    else:
                        logger.error(f"Failed to get {control_name} settings from camera")
                        return False
                        
                except Exception as e:
                    logger.error(f"Error setting up {control_name} control: {str(e)}")
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"Error setting up ROI controls: {str(e)}")
            return False
            
    def handle_value_change(self, value, command):
        """Handle ROI spinbox value changes."""
        try:
            # Update camera
            self.camera_control.call_camera_command(command, "set", value)
            
            # Update status bar
            if hasattr(self.window, 'ui_methods') and hasattr(self.window.ui_methods, 'status_bar_manager'):
                self.window.ui_methods.status_bar_manager.update_on_control_change(command)
                
        except Exception as e:
            logger.error(f"Error handling ROI change: {str(e)}")
            
    def _apply_change(self):
        """Not used for ROI control as we handle changes directly."""
        pass 