import sys
from PyQt6.QtWidgets import QApplication
from interface.ui import ui
from interface.ui_methods import UIMethods

from instruments.xicam.cam_methods import CameraControl, CameraSettings, CameraSequences  
from acquisitions.stream_camera import StreamCamera

class CamTool():
    def __init__(self):
        """UI Window"""
        self.app = QApplication(sys.argv)
        self.window = ui()
       
        """Camera Control"""
        self.camera_control = CameraControl()
        self.camera_settings = CameraSettings(self.camera_control)
        self.camera_sequences = CameraSequences(self.camera_control)
        self.camera_sequences.connect_camera()
        self.stream_camera = StreamCamera(self.camera_control)
       
        """UI Methods"""
        self.window.start_stream.triggered.connect(self.stream_camera.start_stream)
        self.window.stop_stream.triggered.connect(self.stream_camera.stop_stream)
        self.ui_methods = UIMethods(self.window, self.stream_camera)
       
        """Connect the stream to update the image display"""
        self.stream_camera.frame_ready.connect(self.ui_methods.update_ui_image)
       
        """Connect the window close event to our cleanup method"""
        self.window.closeEvent = self.cleanup
    
    """Clean up resources before the application closes."""
    def cleanup(self, event):
        if hasattr(self, 'stream_camera'):
            self.stream_camera.stop_stream()
        if hasattr(self, 'camera_sequences'):
            self.camera_sequences.disconnect_camera()
        event.accept()
        print("CamTool.cleanup(): Resources cleaned up.")
    
    def run(self):
        self.window.show()
        # with open(os.path.join('interface', "style.css"), "r") as f:
        #     self.window.setStyleSheet(f.read())
        sys.exit(self.app.exec())
        
    def __del__(self):
        # Keep the __del__ method as a backup, but the closeEvent handler is the primary cleanup method
        if hasattr(self, 'stream_camera'):
            self.stream_camera.stop_stream()
        if hasattr(self, 'camera_sequences'):
            self.camera_sequences.disconnect_camera()
        print("CamTool.__del__(): Resources cleaned up.")

if __name__ == "__main__":
    app = CamTool()
    app.run()