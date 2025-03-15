from ximea import xiapi
"""
This module provides a Camera class to interface with XIMEA cameras using the xiAPI library.

The Camera class acts as a universal interface for methods related to camera functionality. 
If we need to change the camera library or the camera model, we only need to modify the Camera class.
"""

class Camera:
    def __init__(self):
        # Camera class. It wraps xiApi C library and provides its functionality.
        # Create an instance of Camera.xicam
        self.xicam = xiapi.Camera()
        self.xicam.open_device()
        self.img = xiapi.Image()
    
    def start_cam(self):
        self.xicam.start_acquisition()
    
    def capture_image(self):
        try:
            self.xicam.get_image(self.img)
            # Return the data as a NumPy.Array with dimension Image.height x Image.width (in case imgdataformat is XI_MONO8, XI_MONO16, XI_RAW8 or XI_RAW16), Image.height x Image.width x 3 (in case imgdataformat is XI_RGB24) or Image.height x Image.width x 4 (in case imgdataformat is XI_RGB24)
            image_data = self.img.get_image_data_numpy()
            return image_data
        except xiapi.Xi_error:
            return None

    def stop_cam(self):
        self.xicam.stop_acquisition()

    def close(self):
        if self.xicam is not None:
            self.xicam.close_device()
            self.xicam = None

    def update_exposure(self, value):
        self.xicam.set_exposure(value)
        return value
    
    def update_roi(self, value):
        """Update the camera's region of interest settings."""
        width = value['width']
        height = value['height']
        offset_x = value['offset_x']
        offset_y = value['offset_y']
        try:
            self.xicam.set_width(width)
            self.xicam.set_height(height)
            self.xicam.set_offsetX(offset_x)
            self.xicam.set_offsetY(offset_y)
        except xiapi.Xi_error as e:
            print(f"Error updating ROI: {e}")
        
    def get_cam_meta(self):
        cam_meta = {
            'min_exposure': int(self.xicam.get_exposure_minimum()),
            'max_exposure': int(self.xicam.get_exposure_maximum()),
            'exposure': int(self.xicam.get_exposure()),
            'framerate': self.xicam.get_framerate(),
            'framerate_min': self.xicam.get_framerate_minimum(),
            'framerate_max': self.xicam.get_framerate_maximum(),
            'framerate_inc': self.xicam.get_framerate_increment(),
            'width': self.xicam.get_width(),
            'width_min': self.xicam.get_width_minimum(),
            'width_max': self.xicam.get_width_maximum(),
            'width_inc': self.xicam.get_width_increment(),
            'height': self.xicam.get_height(),
            'height_min': self.xicam.get_height_minimum(),
            'height_max': self.xicam.get_height_maximum(),
            'height_inc': self.xicam.get_height_increment(),
            'offset_x': self.xicam.get_offsetX(),
            'offset_x_min': self.xicam.get_offsetX_minimum(),
            'offset_x_max': self.xicam.get_offsetX_maximum(),
            'offset_x_inc': self.xicam.get_offsetX_increment(),
            'offset_y': self.xicam.get_offsetY(),
            'offset_y_min': self.xicam.get_offsetY_minimum(),
            'offset_y_max': self.xicam.get_offsetY_maximum(),
            'offset_y_inc': self.xicam.get_offsetY_increment(),
            'device_name': self.xicam.get_device_name().decode('utf-8'),
            'device_model_id': self.xicam.get_device_model_id(),
            'device_type': self.xicam.get_device_type().decode('utf-8'),
        }
        
        return cam_meta
    