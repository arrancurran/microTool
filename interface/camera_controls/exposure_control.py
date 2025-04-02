import logging

from .base_control import NumericCameraControl

logger = logging.getLogger(__name__)

class ExposureControl(NumericCameraControl):
    
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
        if not hasattr(self.window, 'exposure_slider') or not hasattr(self.window, 'exposure_label'):
            logger.error("Error: Exposure control not found.")
            return False
                    
        try:
            # Get settings from camera
            settings = super().setup_ui()
            if not settings:
                logger.error("Failed to get exposure settings from camera")
                return False
                            
            # Convert float values to integers for the slider
            min_val = int(round(settings['min']))
            # Use the minimum between camera's max exposure and our safe limit
            max_val = min(int(round(settings['max'])), self.MAX_SAFE_EXPOSURE_US)
            current = min(int(round(settings['current'])), max_val)

            # Configure the slider
            self.window.exposure_slider.setMinimum(min_val)
            self.window.exposure_slider.setMaximum(max_val)
            
            # TODO: Potential memory leak. If setup_ui is called multiple times, the signal may be connected multiple times..
            self.window.exposure_slider.valueChanged.connect(self.handle_value_change)            
            self.window.exposure_slider.setValue(current)
            self._format_and_update_label(current)

            return True
            
        except Exception as e:
            logger.error(f"Error setting up exposure UI: {str(e)}")
            return False
    
    def _format_and_update_label(self, value):
        formatted_value = "Exposure: "
        try:
            if value >= 1000:
                formatted_value += f"{value/1000:.1f} ms"
            else:
                formatted_value += f"{value} μs"
            
            self.window.exposure_label.setText(formatted_value)
        except Exception as e:
            logger.error(f"Error updating exposure label: {str(e)}")
    
    def handle_value_change(self, value):
        self._format_and_update_label(value)
        super().handle_value_change(float(value))  # Convert back to float for camera
        
    def _apply_change(self):
        if self.pending_value is not None:
            try:
                self.camera_control.call_camera_command(self.command_name, "set", self.pending_value)
                self._format_and_update_label(int(round(self.pending_value)))
                # Update status bar
                self.window.image_container.ui_methods.status_bar_manager.update_on_control_change(self.command_name)
                
                self.pending_value = None
            except Exception as e:
                logger.error(f"Error applying exposure value: {str(e)}")
                self.pending_value = None 