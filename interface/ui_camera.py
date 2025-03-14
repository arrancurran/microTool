
from instruments.camera import Camera

class ui_camera(Camera):
    def __init__(self):
        Camera.__init__(self)
        self.active_cam = Camera()
        self.cam_meta = self.active_cam.get_cam_meta()

        self.ui_camera_setup()
    
    def ui_camera_setup(self):
        # Populate the camera ROI controls
        self.cam_roi_height_range = (self.cam_meta['height_min'], self.cam_meta['height_max'])
        self.cam_roi_height_step = self.cam_meta['height_inc']
        self.cam_roi_height = self.cam_meta['height']
        
        self.cam_roi_width_range = (self.cam_meta['width_min'], self.cam_meta['width_max'])
        self.cam_roi_width_step = self.cam_meta['width_inc']
        self.cam_roi_width = self.cam_meta['width']
        
        self.cam_roi_offset_x_range = (0, 4000)
        self.cam_roi_offset_x = 0
        
        self.cam_roi_offset_y_range = (0, 4000)
        self.cam_roi_offset_y = 0
        
        self.cam_exposure_range = (self.cam_meta['min_exposure'], self.cam_meta['max_exposure'])
        self.cam_exposure = self.cam_meta['min_exposure']
        self.cam_exposure_step = (self.cam_meta['max_exposure'] - self.cam_meta['min_exposure']) // 10
        
        self.cam_framerate = self.cam_meta['framerate']
        self.cam_framerate_range = (self.cam_meta['framerate_min'], self.cam_meta['framerate_max'])
        self.cam_framerate_inc = self.cam_meta['framerate_inc']
        self.cam_framerate = self.cam_meta['framerate']
        