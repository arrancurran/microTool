"""
Exposure control for the camera.
"""
import logging

from .base_control import NumericCameraControl

logger = logging.getLogger(__name__)

class ExposureControl(NumericCameraControl):
    """Control for camera exposure settings."""
    
    # Maximum safe exposure time in microseconds (50ms)
    # Higher values can cause UI lag due to frame capture delays
    MAX_SAFE_EXPOSURE_US = 50000
    
    def __init__(self, camera_control, window):
        logger.debug("Initializing ExposureControl")  # Debug print
        super().__init__(
            camera_control=camera_control,
            window=window,
            command_name="exposure",
            display_name="Exposure"
        )
        
    def setup_ui(self) -> bool:
        """Set up the exposure UI elements."""
        logger.debug("Setting up exposure UI elements")  # Debug print
        
        # Check if UI elements exist
        if not hasattr(self.window, 'exposure_slider'):
            logger.error("Error: exposure_slider not found in window")
            return False
        if not hasattr(self.window, 'exposure_label'):
            logger.error("Error: exposure_label not found in window")
            return False
            
        logger.debug("Found required UI elements")
        
        try:
            # Get settings from camera
            settings = super().setup_ui()
            if not settings:
                logger.error("Failed to get exposure settings from camera")
                return False
                
            # logger.debug(f"Got exposure settings: {settings}")  # Debug print
            
            # Convert float values to integers for the slider
            min_val = int(round(settings['min']))
            # Use the minimum between camera's max exposure and our safe limit
            max_val = min(int(round(settings['max'])), self.MAX_SAFE_EXPOSURE_US)
            current = min(int(round(settings['current'])), max_val)
            
            logger.debug(f"Using max exposure value: {max_val} (camera max: {settings['max']}, safe limit: {self.MAX_SAFE_EXPOSURE_US})")
            logger.debug(f"Converted values for slider - min: {min_val}, max: {max_val}, current: {current}")  # Debug print
            
            # Configure the slider
            self.window.exposure_slider.setMinimum(min_val)
            self.window.exposure_slider.setMaximum(max_val)
            logger.debug(f"Configured slider with range: {min_val} to {max_val}")  # Debug print
            
            # Disconnect any existing connections to prevent duplicates
            try:
                self.window.exposure_slider.valueChanged.disconnect()
                logger.debug("Disconnected existing slider connections")  # Debug print
            except Exception:
                logger.debug("No existing connections to disconnect")  # Debug print
                
            # Connect the new signal
            self.window.exposure_slider.valueChanged.connect(self.handle_value_change)
            logger.debug("Connected slider to handle_value_change")  # Debug print
            
            # Set initial value and update label
            self.window.exposure_slider.setValue(current)
            self._format_and_update_label(current)
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting up exposure UI: {str(e)}")
            return False
    
    def _format_and_update_label(self, value):
        """Format and update the exposure label."""
        try:
            if value >= 1000:
                formatted_value = f"Exposure: {value/1000:.1f} ms"
            else:
                formatted_value = f"Exposure: {value} μs"
            self.window.exposure_label.setText(formatted_value)
            logger.debug(f"Updated exposure label to: {formatted_value}")  # Debug print
        except Exception as e:
            logger.error(f"Error updating exposure label: {str(e)}")
    
    def handle_value_change(self, value):
        """Handle exposure slider value changes."""
        logger.debug(f"Exposure value changed to: {value}")  # Debug print
        self._format_and_update_label(value)
        super().handle_value_change(float(value))  # Convert back to float for camera
        
    def _apply_change(self):
        """Apply the pending exposure change to the camera."""
        if self.pending_value is not None:
            logger.debug(f"Applying exposure value: {self.pending_value}")  # Debug print
            try:
                self.camera_control.call_camera_command(self.command_name, "set", self.pending_value)
                logger.debug("Successfully applied exposure value")  # Debug print
                self._format_and_update_label(int(round(self.pending_value)))
                
                # Update status bar
                if hasattr(self.window, 'ui_methods') and hasattr(self.window.ui_methods, 'status_bar_manager'):
                    self.window.ui_methods.status_bar_manager.update_on_control_change(self.command_name)
                
                self.pending_value = None
            except Exception as e:
                logger.error(f"Error applying exposure value: {str(e)}")
                self.pending_value = None 