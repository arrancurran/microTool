"""
This script demonstrates real-time camera streaming using OpenCV.

The code:
1. Imports required camera control modules and OpenCV
2. Initializes camera control objects
3. Sets up basic camera parameters (exposure time)
4. Enters a loop to continuously display captured frames
5. Gracefully closes camera and windows when 'q' is pressed
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from instruments.xicam.cam_methods import CameraControl, CameraSettings, CameraSequences
import cv2
import time

def test_stream():
    print("Starting camera initialization...")
    
    # Connect to the camera
    print("Creating camera control objects...")
    camera_ctrl = CameraControl()
    camera_settings = CameraSettings(camera_ctrl)
    camera_sequences = CameraSequences(camera_ctrl)
    
    print("Connecting to camera...")
    camera_sequences.connect_camera()

    # Set exposure
    print("Setting camera exposure...")
    camera_settings.call_camera_command("exposure", "set", 400)

    # Set target frame rate
    target_fps = 60
    frame_interval = 1.0 / target_fps

    print("Stream started. Press 'q' to quit.")
    last_frame_time = 0
    frame_count = 0

    try:
        while True:
            current_time = time.time()
            elapsed = current_time - last_frame_time

            if elapsed >= frame_interval:
                # Capture frame
                camera_ctrl.get_image()
                frame = camera_ctrl.get_image_data()
                
                if frame is not None:
                    # Display the frame
                    cv2.imshow("Camera Stream", frame)
                    last_frame_time = current_time
                    frame_count += 1
                    
                    if frame_count % 30 == 0:  # Print every 30 frames
                        print(f"Frames captured: {frame_count}")
            else:
                # Small sleep to prevent busy waiting
                time.sleep(0.001)

            # Check for 'q' key to quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("Quit key pressed")
                break

    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        # Clean up
        print("Stopping camera stream...")
        camera_sequences.disconnect_camera()
        cv2.destroyAllWindows()
        print("Cleanup complete")

if __name__ == "__main__":
    print("Script started")
    test_stream()
    print("Script finished") 