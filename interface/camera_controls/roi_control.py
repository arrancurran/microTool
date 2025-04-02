from .base_control import NumericCameraControl
import logging

logger = logging.getLogger(__name__)

class ROIControl(NumericCameraControl):
    
    def __init__(self, camera_control, window):
        super().__init__(
            camera_control=camera_control,
            window=window,
            display_name="ROI",
            command_name="roi"
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
        try:
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
                    # Add detailed debug logging
                    logger.debug(f"Setting up {control_name}:")
                    logger.debug(f"  min_val: {min_val}")
                    logger.debug(f"  max_val: {max_val}")
                    logger.debug(f"  inc_val: {inc_val}")
                    logger.debug(f"  current: {current}")                    
                    
                    if all(v is not None for v in [min_val, max_val, inc_val, current]):
                        # Configure spinbox
                        spinbox.setMinimum(min_val)
                        spinbox.setMaximum(max_val)
                        spinbox.setSingleStep(inc_val)
                        spinbox.setValue(current)
                        
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
        try:
            # Update camera
            self.camera_control.call_camera_command(command, "set", value)
            
            logger.debug(f"{command} set to {value}")
            
            if command in ['width', 'height']:
                # Get current dimension and max dimension
                max_value  = self.camera_control.call_camera_command(f"{command}_max", "get")
                
                # Calculate and set new max offset
                max_offset = max_value - value
                
                # Update the appropriate offset spinbox
                if command == 'width':
                    self.window.roi_offset_x.setMaximum(max_offset)
                else:  # height
                    self.window.roi_offset_y.setMaximum(max_offset)
                    
            # Update status bar
            #  TODO: We need to clean up self.window so it makes sense for both here and image_container
            self.window.image_container.ui_methods.status_bar_manager.update_on_control_change(command)

                
        except Exception as e:
            logger.error(f"Error handling ROI change: {str(e)}")
            
    def _apply_change(self):
        """Not used for ROI control as we handle changes directly."""
        pass 