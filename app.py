import sys, os, logging
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from interface import AppUI, UIMethods

from instruments import CameraControl, CameraSequences

from acquisitions.live_stream_handler import LiveStreamHandler

from interface.status_bar.update_notif import set_main_window

from utils import PopupNotifManager
from utils.last_session import save_last_session, load_last_session

# Configure global logging
def setup_logging():
    base_dir = Path(__file__).resolve().parent
    logs_dir = base_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = logs_dir / f"microTool_{timestamp}.log"

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(levelname)s - %(threadName)s - %(filename)s - %(name)s:%(funcName)s() - %(message)s',
        handlers=[
            logging.FileHandler(str(log_file)),
            logging.StreamHandler()  # Also log to console
        ]
    )
    logging.info("Starting microTool application")

class microTool():
    def __init__(self):
        # Passing sys.argv so any command-line arguments are forwarded. 
        self.app = QApplication(sys.argv)
        self.window = AppUI()
                
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

        # Restore last-session settings (ROI, exposure, acquisition
        # configuration) now that the UI and camera controls are
        # initialised.
        try:
            load_last_session(self.window, self.camera_control)
        except Exception as e:
            logging.error(f"Error loading last session settings: {e}")

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
        # Experiment acquisition: fixed number of frames
        if hasattr(self.window, "start_experiment"):
            self.window.start_experiment.triggered.connect(self.ui_methods.handle_experiment)
        
        # TODO: ui_methods should be an attribute of window
        self.ui_methods.status_bar_manager.update_all()
        
    def cleanup(self, event):
        try:
            # Persist front-panel settings for the next run
            try:
                save_last_session(self.window, self.camera_control)
            except Exception as e:
                logging.error(f"Error saving last session settings: {e}")

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
        # Start the application in full screen
        self.window.showFullScreen()
        sys.exit(self.app.exec())
        
if __name__ == "__main__":
    setup_logging()
    app = microTool()
    app.run()