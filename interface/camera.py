
from instruments.camera import Camera

class ui_camera(Camera):
    def __init__(self):
        Camera.__init__(self)
        self.cam_meta = self.get_cam_meta()
        self.setup_ui_camera()

    # def setup_ui_camera(self):
    #     self.roi_width.setRange(self.cam_meta['width_min'], self.cam_meta['width_max'])