from PyQt6.QtGui import QImage, QPixmap, QPainter
from PyQt6.QtCore import Qt
from .draw_roi import DrawROI
from interface.status_bar.update_notif import update_notif
import logging, time
from interface.camera_controls.control_manager import CameraControlManager


logger = logging.getLogger(__name__)

class UIDisplayMethods:
    
    def __init__(self, window, image_container, stream_camera, camera_control, status_bar_manager):
        self.window = window
        self.image_container = image_container
        self.stream_camera = stream_camera
        self.camera_control = camera_control
        self.draw_roi = DrawROI()
        self.original_image_size = None
        self._last_container_size = None
        self._cached_image_shape = None
        self.status_bar_manager = status_bar_manager
    
    def update_img_display(self):

        np_image_data = self.stream_camera.get_img_from_queue()
        if np_image_data is None:
            return
        
        # Cache the container size and check if it's changed
        current_size = self.window.image_container.size()
        size_changed = not hasattr(self, '_last_container_size') or self._last_container_size != current_size
        self._last_container_size = current_size

        # Only recalculate scaling if the image size or container has changed
        if not hasattr(self, '_cached_image') or size_changed or self._cached_image_shape != np_image_data.shape:
            self._cached_image_shape = np_image_data.shape
            # Do the expensive scaling calculations here
            height, width = np_image_data.shape
            bytes_per_line = width
            image_data = QImage(np_image_data.data, width, height, bytes_per_line, QImage.Format.Format_Grayscale8)
            image = QPixmap(image_data)

            container_size = self.window.image_container.size()

            scaled_image = image.scaled(container_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

            offset_x = (container_size.width() - scaled_image.width()) // 2
            offset_y = (container_size.height() - scaled_image.height()) // 2
            
            scale_factor_x = scaled_image.width() / width
            scale_factor_y = scaled_image.height() / height
            
            # Update the ROI drawing parameters
            self.draw_roi.update_scale_and_offset(
                scale_factor_x, scale_factor_y, 
                offset_x, offset_y,
                scaled_image.width(), scaled_image.height(),
                width, height
            )
            
            # Create a new pixmap for drawing ROIs
            final_image = QPixmap(container_size)
            final_image.fill(Qt.GlobalColor.transparent)
            
            # Draw the scaled image
            painter = QPainter(final_image)
            painter.drawPixmap(offset_x, offset_y, scaled_image)
            
            # Draw the ROI if any
            self.draw_roi.draw_rectangle(painter)
            painter.end()
            
            self.window.image_container.setPixmap(final_image)
            self.original_image_size = (width, height)

            self.window.histogram_plot.update(np_image_data)

    def handle_apply_roi(self):

        if self.draw_roi.current_rect:
            
            rect = self.draw_roi.current_rect
            x = rect.x()
            y = rect.y()
            width = rect.width()
            height = rect.height()

            """Get current ROI offset"""
            current_offset_x = self.window.roi_offset_x.value()
            logger.debug(f"Current ROI offset X: {current_offset_x}")
            current_offset_y = self.window.roi_offset_y.value()
            logger.debug(f"Current ROI offset Y: {current_offset_y}")
            
            """Add current offset to the new rectangle position"""
            new_offset_x = current_offset_x + x
            logger.debug(f"New ROI offset X: {new_offset_x}")
            new_offset_y = current_offset_y + y
            logger.debug(f"New ROI offset Y: {new_offset_y}")
            
            """Sanity check the ROI values"""
            width = self._sanity_check_roi("width", width)
            height = self._sanity_check_roi("height", height)
            new_offset_x = self._sanity_check_roi("offset_x", new_offset_x)
            new_offset_y = self._sanity_check_roi("offset_y", new_offset_y)
            
            logger.debug(f"Sanity checked ROI: width = {width}, height = {height}, offset_x = {new_offset_x}, offset_y = {new_offset_y}")
            
            """Update the ROI spinboxes"""
            self.window.roi_width.setValue(width)
            self.window.roi_height.setValue(height)
            time.sleep(0.2) # Wait for the offset to update
            self.window.roi_offset_x.setValue(new_offset_x)
            self.window.roi_offset_y.setValue(new_offset_y)
            
            """Update status bar"""
            self.status_bar_manager.update_on_control_change("roi")
            
            """Clear the  rectangle"""
            self.draw_roi.current_rect = None
        else:
            update_notif("No ROI Selected", duration=2000)
    
    def _sanity_check_roi(self, command, value):
        """Sanity check the ROI values."""
        inc = int(self.camera_control.call_camera_command(f"{command}_inc", "get"))
        min_val = int(self.camera_control.call_camera_command(f"{command}_min", "get"))

        safe_value = None
        
        if value % inc == 0:
            safe_value = value
        elif value < min_val:
            safe_value = min_val
        else:
            safe_value = value - (value % inc)
                
        return safe_value
    
    def handle_reset_roi(self):
        
        """Handle Reset ROI button click."""
        try:
            """Update the ROI spinboxes to max values"""
            self.window.roi_offset_x.setValue(0)
            self.window.roi_offset_y.setValue(0)
            time.sleep(0.05) # Wait for the offset to update
            max_width = int(self.camera_control.call_camera_command("width_max", "get"))
            max_height = int(self.camera_control.call_camera_command("height_max", "get"))
            self.window.roi_width.setValue(max_width)
            self.window.roi_height.setValue(max_height)
            
            """Clear the current rectangle"""
            self.draw_roi.current_rect = None
            self.window.image_container.update()
            
            """Update status bar"""
            self.status_bar_manager.update_on_control_change("roi")
            
        except Exception as e:
            logger.error(f"Error resetting ROI: {str(e)}")
            update_notif("Failed to Reset ROI", duration=2000)
    
    
    def handle_mouse_press(self, event):
        self.draw_roi.mousePressEvent(event)

    def handle_mouse_move(self, event):
        self.draw_roi.mouseMoveEvent(event, self.image_container)

    def handle_mouse_release(self, event):
        self.draw_roi.mouseReleaseEvent(event, self.image_container)

    def handle_paint(self, painter):
        self.draw_roi.draw_rectangle(painter)