from PyQt6.QtCore import QObject

class HistogramUpdater(QObject):
    """
    A class that can update the histogram in the main window.
    This should be instantiated with a reference to the main window.
    """
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

    def update_histogram_from_image(self, image_data):
        """
        Update the histogram in the main window with new image data.
        
        Args:
            image_data (numpy.ndarray): The image data to create histogram from
        """
        if hasattr(self.main_window, 'update_histogram'):
            self.main_window.update_histogram(image_data)
        else:
            print("Warning: Main window does not have update_histogram method")

# Example usage:
"""
# In your main window class:
from histogram_updater import HistogramUpdater

class MainWindow(uiScaffolding):
    def __init__(self):
        super().__init__()
        self.histogram_updater = HistogramUpdater(self)
        
    def process_new_image(self, image_data):
        # Update histogram whenever new image data is available
        self.histogram_updater.update_histogram_from_image(image_data)
""" 