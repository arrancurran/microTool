from datetime import datetime
import tifffile
import os
import logging

logger = logging.getLogger(__name__)

class Snapshot:
    """Handles saving individual frames from the camera as TIFF files."""
    
    def __init__(self, stream_camera, window):
        """Initialize with references to stream camera and window."""
        self.stream_camera = stream_camera
        self.camera_control = stream_camera.camera_control
        self.window = window
    
    def save_snapshot(self):
        """Capture and save the current frame as a TIFF file."""
        # Check if camera is streaming
        was_streaming = self.stream_camera.camera_thread is not None and self.stream_camera.camera_thread.isRunning()
        
        try:
            # Stop streaming if active by triggering the stop button
            if was_streaming:
                self.window.stop_stream.trigger()
            
            # Direct camera acquisition
            self.camera_control.start_camera()
            self.camera_control.get_image()
            frame = self.camera_control.get_image_data()
            self.camera_control.stop_camera()
            
            if frame is None:
                logger.error("Failed to capture frame")
                return False
                
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"snapshot_{timestamp}.tiff"
            
            # Save the image as TIFF
            tifffile.imwrite(filename, frame)
            logger.info(f"Snapshot saved as {filename}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving snapshot: {str(e)}")
            return False
            
        finally:
            # Restore streaming if it was active by triggering the start button
            if was_streaming:
                self.window.start_stream.trigger() 