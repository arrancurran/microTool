"""
Mock camera implementation for testing and development without hardware.
"""
import numpy as np
import time

class NoCam:
    """Mock implementation of xiapi.Camera for testing."""
    def __init__(self):
        self.width = 2048
        self.height = 2048
        self.exposure = 10000  # 10ms default
        self.framerate = 30
        self.offset_x = 0
        self.offset_y = 0
        self._is_open = False
        self._is_running = False
        self._last_frame_time = 0
        
    def open_device(self):
        self._is_open = True
        return True
        
    def close_device(self):
        self._is_open = False
        return True
        
    def start_acquisition(self):
        if not self._is_open:
            return False
        self._is_running = True
        self._last_frame_time = time.time()
        return True
        
    def stop_acquisition(self):
        self._is_running = False
        return True
        
    def get_device_name(self):
        return b"No Camera"
        
    def get_image(self, image):
        if not self._is_running:
            return False
            
        # Generate a simple test pattern
        current_time = time.time()
        frame_time = 1.0 / self.framerate
        if current_time - self._last_frame_time < frame_time:
            return False
            
        # Create a test pattern
        x = np.linspace(0, 2*np.pi, self.width)
        y = np.linspace(0, 2*np.pi, self.height)
        xx, yy = np.meshgrid(x, y)
        pattern = np.sin(xx + time.time()) * np.cos(yy + time.time())
        pattern = (pattern + 1) * 127.5  # Scale to 0-255
        
        # Add some noise
        noise = np.random.normal(0, 10, (self.height, self.width))
        pattern = np.clip(pattern + noise, 0, 255).astype(np.uint8)
        
        # Set image data
        image.set_image_data_numpy(pattern)
        image.tsSec = int(current_time)
        image.tsUSec = int((current_time % 1) * 1e6)
        
        self._last_frame_time = current_time
        return True
        
    def get_image_data_numpy(self):
        if not self._is_running:
            return None
        return np.random.randint(0, 255, (self.height, self.width), dtype=np.uint8)
        
    def get_exposure(self):
        return self.exposure
        
    def set_exposure(self, value):
        self.exposure = value
        return True
        
    def get_exposure_min(self):
        return 1
        
    def get_exposure_max(self):
        return 1000000
        
    def get_width(self):
        return self.width
        
    def get_width_min(self):
        return 1
        
    def get_width_max(self):
        return 2048
        
    def get_width_inc(self):
        return 1
        
    def get_height(self):
        return self.height
        
    def get_height_min(self):
        return 1
        
    def get_height_max(self):
        return 2048
        
    def get_height_inc(self):
        return 1
        
    def get_offset_x(self):
        return self.offset_x
        
    def get_offset_x_min(self):
        return 0
        
    def get_offset_x_max(self):
        return 2048
        
    def get_offset_x_inc(self):
        return 1
        
    def set_offset_x(self, value):
        self.offset_x = value
        return True
        
    def get_offset_y(self):
        return self.offset_y
        
    def get_offset_y_min(self):
        return 0
        
    def get_offset_y_max(self):
        return 2048
        
    def get_offset_y_inc(self):
        return 1
        
    def set_offset_y(self, value):
        self.offset_y = value
        return True
        
    def get_framerate(self):
        return self.framerate
        
    def set_framerate(self, value):
        self.framerate = value
        return True
        
    def get_framerate_min(self):
        return 1
        
    def get_framerate_max(self):
        return 100 