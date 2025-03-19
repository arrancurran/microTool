"""
Simple test to check if the Image Object is persisting.
"""

import sys
import os
import time
# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from instruments.xicam.cam_methods import CameraControl, CameraSequences
import cv2

def test_camera():
    print("Starting camera test...")
    
    print("Creating camera objects...")
    camera_ctrl = CameraControl()
    camera_sequences = CameraSequences(camera_ctrl)
    
    # Connect to camera
    print("Connecting to camera...")
    camera_ctrl.initialize_camera()
    camera_ctrl.open_camera()
    
    camera_ctrl.ImageObject()
    
    for i in range(10):
        print(f"Capturing frame {i+1}...")
        camera_ctrl.start()
        camera_ctrl.get_image()
        frame = camera_ctrl.get_image_data()
        if frame is not None:
            print("Successfully captured frame!")
        
        camera_ctrl.stop()
        time.sleep(1)

    camera_ctrl.close()
    
if __name__ == "__main__":
    test_camera() 