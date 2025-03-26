import cv2
import numpy as np
import pyqtgraph as pg

class ImgHistDisplay:
    """Class to manage and display a histogram for image data."""

    def __init__(self, plot_widget):
        self.plot_widget = plot_widget
        self.plot_widget.setBackground('#2f353c')  # Set background color
        self.plot_widget.plotItem.setContentsMargins(0, 0, 0, 0)  # Remove padding
        self.plot_widget.plotItem.setDefaultPadding(0)  # Disable default padding
        self.plot_widget.plotItem.hideAxis('left')  # Hide Y-axis
        self.plot_widget.plotItem.hideAxis('bottom')  # Hide X-axis
        self.plot_widget.plotItem.getViewBox().setLimits(xMin=0, xMax=256)  # Lock x-axis range
        self.plot_widget.plotItem.getViewBox().enableAutoRange(axis=pg.ViewBox.YAxis, enable=True)  # Auto-scale Y-axis

    def update(self, image_data):
        """Update the histogram with new image data."""
        if len(image_data.shape) == 3:
            image_data = cv2.cvtColor(image_data, cv2.COLOR_RGB2GRAY)

        hist, bins = np.histogram(image_data.flatten(), bins=256, range=[0, 256])
        self.plot_widget.clear()

        x = bins[:-1]
        line_plot = pg.PlotCurveItem(x, hist, pen=pg.mkPen(color='#97c1ff', width=2))
        self.plot_widget.addItem(line_plot)

        fill_plot = pg.FillBetweenItem(
            pg.PlotDataItem(x, hist),
            pg.PlotDataItem(x, np.zeros_like(hist)),
            brush=pg.mkBrush(color=(151, 193, 255, 100))
        )
        self.plot_widget.addItem(fill_plot)

    def reset(self):
        """Clear the histogram."""
        self.plot_widget.clear()