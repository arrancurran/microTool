"""
This script demonstrates real-time camera streaming using a custom camera interface.

The code:
1. Imports required camera control modules and OpenCV
2. Initializes camera control objects for settings, sequences and streaming
3. Sets up basic camera parameters (exposure time)
4. Creates a StreamCamera instance to handle frame capture in a separate thread
5. Enters a loop to continuously display captured frames using OpenCV
6. Gracefully closes camera and windows when 'q' is pressed

The commented code at the bottom shows alternative camera operations like:
- Time series acquisition
- Direct frame capture
- Stream control
- Camera parameter adjustment

Dependencies:
- Custom camera modules (xicam.cam_methods)
- StreamCamera class for threaded capture
- OpenCV for frame display
"""

from instruments.xicam.cam_methods import CameraControl, CameraSettings, CameraSequences  
from acquisitions.stream_camera import StreamCamera
import cv2

# Connect to the camera
camera_ctrl = CameraControl()
camera_settings = CameraSettings(camera_ctrl)
camera_sequences = CameraSequences(camera_ctrl)
camera_sequences.connect_camera()

camera_settings.call_camera_command("exposure", "set", 400)


# Initialize and start streaming
camera_stream = StreamCamera(camera_ctrl)
camera_stream.start_stream()

try:
    while True:
        frame = camera_stream.get_latest_frame()
        if frame is not None:
            cv2.imshow("Camera Stream", frame)
        
        # Press 'q' to stop
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    camera_stream.stop_stream()
    camera_sequences.disconnect_camera()
    cv2.destroyAllWindows()