from datetime import datetime
import tifffile, logging

logger = logging.getLogger(__name__)

class Snapshot:
    """Handles saving individual snapshots from the camera as TIFF files."""
    
    def __init__(self, stream_camera, window):
        """Initialize with references to stream camera and window."""
        self.stream_camera = stream_camera
        self.camera_control = stream_camera.camera_control
        self.window = window
    
    def save_snapshot(self):
        # Check if camera is streaming
        was_streaming = self.stream_camera.live_stream_qthread is not None and self.stream_camera.live_stream_qthread.isRunning()
        
        try:
            if was_streaming:
                self.window.stop_stream.trigger()

            self.camera_control.start_camera()
            self.camera_control.get_image()
            snapshot = self.camera_control.get_image_data()
            self.camera_control.stop_camera()
            
            if snapshot is None:
                logger.error("Failed to capture snapshot")
                return False
                
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # TODO: Create UI to select save location
            filename = f"_data/snapshot_{timestamp}.tiff"
            
            # Save the image as TIFF
            tifffile.imwrite(filename, snapshot)
            logger.info(f"Snapshot saved as {filename}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving snapshot: {str(e)}")
            return False
            
        finally:
            # Restore streaming if it was active by triggering the start button
            if was_streaming:
                self.window.start_stream.trigger() 