"""
Image processing utility functions.
"""
import cv2
import numpy as np
import pyqtgraph as pg

def calc_img_hist(window, image_data):
    """Calculate and display histogram for image data as a line graph with fill."""
    if len(image_data.shape) == 3:
        image_data = cv2.cvtColor(image_data, cv2.COLOR_RGB2GRAY)

    # Calculate histogram
    hist, bins = np.histogram(image_data.flatten(), bins=256, range=[0, 256])

    # Clear the previous plot
    window.hist_display.clear()

    # Create x-axis values (bin centers)
    x = bins[:-1]

    # Plot the line graph
    line_plot = pg.PlotCurveItem(x, hist, pen=pg.mkPen(color='#97c1ff', width=2))  # Line color and width
    window.hist_display.addItem(line_plot)

    # Fill under the line
    fill_plot = pg.FillBetweenItem(
        pg.PlotDataItem(x, hist),  # Upper boundary (line graph)
        pg.PlotDataItem(x, np.zeros_like(hist)),  # Lower boundary (zero line)
        brush=pg.mkBrush(color=(151, 193, 255, 100))  # Fill color with transparency
    )
    window.hist_display.addItem(fill_plot)

    # Set background color
    window.hist_display.setBackground('#2f353c')  # Dark gray background

    # Remove padding around the sides
    window.hist_display.plotItem.setContentsMargins(0, 0, 0, 0)
    window.hist_display.plotItem.setDefaultPadding(0)  # Disable default padding
    window.hist_display.plotItem.getViewBox().setLimits(xMin=0, xMax=256)  # Lock x-axis range
    window.hist_display.plotItem.getViewBox().enableAutoRange(axis=pg.ViewBox.YAxis, enable=True)  # Auto-scale y-axis

    # Hide axes
    window.hist_display.plotItem.hideAxis('left')  # Hide Y-axis
    window.hist_display.plotItem.hideAxis('bottom')  # Hide X-axis