"""
Simple test to check if the camera is working.
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from instruments.xicam.cam_methods import CameraControl, CameraSettings, CameraSequences
import cv2

def test_camera():
    print("Starting camera test...")
    
    try:
        # Create camera objects
        print("Creating camera objects...")
        camera_ctrl = CameraControl()
        camera_settings = CameraSettings(camera_ctrl)
        camera_sequences = CameraSequences(camera_ctrl)
        
        # Connect to camera
        print("Connecting to camera...")
        camera_sequences.connect_camera()
        
        # Try to get one frame
        print("Attempting to capture a frame...")
        camera_ctrl.get_image()
        frame = camera_ctrl.get_image_data()
        
        if frame is not None:
            print("Successfully captured frame!")
            print(f"Frame shape: {frame.shape}")
            # Display the frame
            cv2.imshow("Test Frame", frame)
            cv2.waitKey(0)  # Wait for a key press
            cv2.destroyAllWindows()
        else:
            print("Failed to capture frame")
            
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        # Clean up
        print("Cleaning up...")
        try:
            camera_sequences.disconnect_camera()
        except:
            pass
        print("Test complete")

if __name__ == "__main__":
    test_camera() 