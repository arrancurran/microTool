
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
        self.xicam.get_image(self.img)
        img_data = self.img.get_image_data_numpy()
        return img_data

    def stop_cam(self):
        self.xicam.stop_acquisition()

    def close(self):
        if self.xicam is not None:
            self.xicam.close_device()
            self.xicam = None
    
    def get_cam_metadata(self):
        metadata = {
            'min_exposure': int(self.xicam.get_exposure_minimum()),
            'max_exposure': int(self.xicam.get_exposure_maximum()),
            'exposure': int(self.xicam.get_exposure()),
            'framerate': self.xicam.get_framerate(),
            'framerate_min': self.xicam.get_framerate_minimum(),
            'framerate_max': self.xicam.get_framerate_maximum(),
            'framerate_inc': self.xicam.get_framerate_increment()
        }
        return metadata

    def set_exposure(self, value):
        self.xicam.set_exposure(value)
        return value
    
    
    