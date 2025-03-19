"""
This module provides UI-specific camera settings and initialization.
It handles getting camera parameters and setting up UI elements with appropriate ranges.
"""

class UICameraSettings:
    # Maximum safe exposure time in microseconds (50ms)
    # Higher values can cause UI lag due to frame capture delays
    MAX_SAFE_EXPOSURE_US = 200000
    
    def __init__(self, camera_control):
        """Initialize camera UI settings."""
        self.camera_control = camera_control
        self.exposure_settings = self._get_exposure_settings()
        
    def _get_exposure_settings(self):
        """Get the exposure settings from the camera."""
        try:
            # Get values in microseconds from camera
            min_exposure = int(self.camera_control.call_camera_command("exposure_min", "get"))
            max_exposure = int(self.camera_control.call_camera_command("exposure_max", "get"))
            current_exposure = int(self.camera_control.call_camera_command("exposure", "get"))
            
            # Limit maximum exposure to prevent UI hanging
            max_exposure = min(max_exposure, self.MAX_SAFE_EXPOSURE_US)
            current_exposure = min(current_exposure, max_exposure)
            
            return {
                'min': min_exposure,
                'max': max_exposure,
                'current': current_exposure
            }
        except Exception as e:
            print(f"Error getting exposure settings: {str(e)}")
            # Return default values if camera read fails
            return {
                'min': 0,
                'max': 10000,
                'current': 1000
            }
    
    def setup_exposure_slider(self, slider):
        """Configure the exposure slider with camera-specific ranges."""
        # Ensure all values are integers for the slider
        min_val = self.exposure_settings['min']
        max_val = self.exposure_settings['max']
        current_val = self.exposure_settings['current']
        
        slider.setMinimum(min_val)
        slider.setMaximum(max_val)
        slider.setValue(current_val)
        
        # Set page step to 5% of the range for better usability
        range_size = max_val - min_val
        page_step = 1 # max(1, int(range_size * 0.05))
        slider.setPageStep(page_step)
        
        print(f"Exposure slider configured with min={min_val}, max={max_val}, current={current_val}, step={page_step}")
