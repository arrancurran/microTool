"""
Image processing utility functions.
"""
import cv2
import numpy as np

def calc_img_hist(window, image_data):
    """Calculate and display histogram for image data."""
    if len(image_data.shape) == 3:
        image_data = cv2.cvtColor(image_data, cv2.COLOR_RGB2GRAY)

    hist = cv2.calcHist([image_data], [0], None, [256], [0, 256])
    window.hist_display.figure.clear()
    ax = window.hist_display.figure.add_subplot(111)
    ax.plot(hist, color='#97c1ff', linestyle='-', linewidth=0.5, marker='')
    
    # Fill the area under the histogram line
    ax.fill_between(np.arange(256), hist[:, 0], color='#97c1ff', alpha=0.2)
    
    ax.set_yscale('log')
    ax.set_xlim([0, 256])
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_frame_on(False)
    
    window.hist_display.figure.patch.set_facecolor('#2f353c')
    window.hist_display.figure.subplots_adjust(left=0, right=1, top=1, bottom=0)
    window.hist_display.draw() 