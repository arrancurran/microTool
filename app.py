import sys, os, logging
from datetime import datetime
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from interface.ui import ui
from interface.ui_methods import UIMethods
from instruments.xicam.cam_methods import CameraControl, CameraSequences
from acquisitions.live_stream_handler import LiveStreamHandler
from interface.status_bar.update_notif import set_main_window

# Configure global logging
def setup_logging():
    if not os.path.exists('logs'):
        os.makedirs('logs')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f'logs/microTool_{timestamp}.log'

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(levelname)s - %(threadName)s - %(filename)s - %(name)s:%(funcName)s() - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()  # Also log to console
        ]
    )
    logging.info("Starting microTool application")

class microTool():
    def __init__(self):
        """UI Window"""
        self.app = QApplication(sys.argv)   
        self.window = ui()
       
        """Camera Control"""
        self.camera_control = CameraControl()
        self.camera_sequences = CameraSequences(self.camera_control)
        self.camera_sequences.connect_camera()
        self.stream_camera = LiveStreamHandler(self.camera_control)
       
        """UI Methods"""
        self.ui_methods = UIMethods(self.window, self.stream_camera)
        
        """Connect the UI methods to the image container"""
        self.window.image_container.ui_methods = self.ui_methods

        """Set the main window"""
        set_main_window(self.window)

        # Create a timer to update UI at a reasonable rate
        self.ui_update_timer = QTimer()
        self.ui_update_timer.timeout.connect(self.ui_methods.update_img_display)
        self.ui_update_timer.start(8)  # ~30 FPS for UI updates
        
        """Connect the window close event to our cleanup method"""
        self.window.closeEvent = self.cleanup

        """Connect all signals"""
        self.window.start_stream.triggered.connect(self.stream_camera.start_stream)
        self.window.stop_stream.triggered.connect(self.stream_camera.stop_stream)
        self.window.snapshot.triggered.connect(self.ui_methods.handle_snapshot)
        self.window.start_recording.triggered.connect(self.ui_methods.handle_recording)
    
    """Clean up resources before the application closes."""
    def cleanup(self, event):
        try:
            if hasattr(self, 'stream_camera'):
                self.stream_camera.cleanup()
            if hasattr(self, 'camera_sequences'):
                self.camera_sequences.disconnect_camera()
            event.accept()
            logging.info("Resources cleaned up.")
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")
            event.accept()
        
    def __del__(self):
        """Backup cleanup method, but closeEvent handler is the primary cleanup method"""
        try:
            if hasattr(self, 'stream_camera'):
                self.stream_camera.cleanup()
            if hasattr(self, 'camera_sequences'):
                self.camera_sequences.disconnect_camera()
            logging.info("Resources cleaned up.")
        except Exception as e:
            logging.error(f"Error during __del__ cleanup: {e}")
    
    def run(self):
        self.window.show()
        sys.exit(self.app.exec())
        
if __name__ == "__main__":
    setup_logging()
    app = microTool()
    app.run()