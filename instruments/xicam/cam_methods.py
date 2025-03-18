"""
Provides camera control and settings management for Ximea cameras. Here we define methods that speak directly to the camera using the XiAPI.
For a different camera, we would need to rewrite this module to speak to the new camera.

CameraControl: Handles core camera operations like:
- Initializing/closing the camera connection
- Starting/stopping image acquisition 
- Capturing individual images and accessing image data

CameraSettings: Manages camera configuration parameters through:
- Command parsing from commands.json
- Setting exposure, gain, etc.

CameraSequences: (Defined elsewhere) Implements higher-level acquisition patterns like:
- Time series capture
- Continuous streaming

Usage:
This module is primarily used by app.py which:
1. Creates instances of these classes
2. Uses them to control camera operations
3. Implements the main application workflow

Dependencies:
- ximea.xiapi for low-level camera interface
- commands.json for camera parameter definitions
"""

import json
from ximea import xiapi

# Load the JSON file
with open('instruments/xicam/commands.json', 'r') as file:
    commands = json.load(file)

class CameraControl:
    """
    CameraControl class provides core camera operations for Ximea cameras.

    Methods:
        __init__(): Initializes camera connection using xiapi
        ImageObject(): Creates image object to store camera data
        start(): Begins camera acquisition
        get_image(): Captures single image into image object
        get_image_data(): Returns numpy array of image data
        get_image_timestamp(): Returns image timestamp in microseconds
        stop(): Stops camera acquisition
        close(): Closes camera connection

    The class uses the ximea.xiapi library to interface directly with Ximea cameras.
    Images are stored in xiapi.Image objects which contain both pixel data and metadata. See https://www.ximea.com/support/wiki/apis/XiAPI_Python_Manual#xiApiPython_Image-XI_IMG

    TODO: We should set a custom size for ImageObject() according to the camera resolution
    TODO: We should also set the image format to mono8 or mono16 depending on the camera
    """
    def __init__(self):
        """Initialize the camera object but do not start it."""
        self.camera = None
        self.image = None
        
    def initialize_camera(self):
        """Initialize the camera object."""
        if self.camera is None:
            self.camera = xiapi.Camera()
            print("CameraControl.initialize_camera(): Camera initialized.")
        else:
            print("CameraControl.initialize_camera(): Camera already initialized.")
        # return self.camera

    def open_camera(self):
        if self.camera: 
            self.camera.open_device()
            print("CameraControl.open_camera(): Camera opened.")
        else:
            print("CameraControl.open_camera(): Camera not initialized.")

    def ImageObject(self):
        if self.image is None:
            self.image = xiapi.Image()
            print("CameraControl.ImageObject(): Image initialized.")
        else:
            print("CameraControl.ImageObject(): Image already initialized.")

    def start(self):
        if self.camera:
            self.camera.start_acquisition()
            print("CameraControl.start(): Camera acquisition started.")
        else:
            print("CameraControl.start(): Camera not initialized.")
    
    def get_image(self):
        if self.image:
            self.camera.get_image(self.image)
            return self.image
        else:
            print("CameraControl.get_image(): Image not initialized.")

    def get_image_data(self):
        if self.image:
            return self.image.get_image_data_numpy()
        else:
            print("CameraControl.get_image_data(): Image not initialized.")
    
    def get_image_timestamp(self):
        if self.image:
            return self.image.tsUSec
        else:
            print("CameraControl.get_image_timestamp(): Image not initialized.")
    
    def stop(self):
        if self.camera:
            self.camera.stop_acquisition()
            print("CameraControl.stop(): Camera acquisition stopped.")
        else:
            print("CameraControl.stop(): Camera not initialized.")

    def close(self):
        if self.camera:
            self.camera.close_device()
            print("CameraControl.close(): Camera closed.")
            self.camera = None  # Reset the camera instance
        else:
            print("CameraControl.close(): Camera not initialized.")
  

class CameraSequences():
    """
    CameraSequences class handles high-level camera acquisition patterns.

    Methods:
        __init__(camera_control): Takes a CameraControl instance to manage camera operations
        connect_camera(): Initializes and starts the camera connection
        disconnect_camera(): Stops and closes the camera connection
        stream_camera(): Continuously captures and displays images in real-time
        acquire_time_series(num_images): Captures a specified number of sequential images

    The class uses a CameraControl instance to:
    - Initialize and manage camera connections
    - Stream live camera feed
    - Capture sequences of images
    - Handle image acquisition and data retrieval

    Example usage:
        ctrl = CameraControl()
        sequences = CameraSequences(ctrl)
        sequences.connect_camera()
        sequences.acquire_time_series(100)  # Capture 100 images
        sequences.disconnect_camera()
    """
    def __init__(self, camera_control):
        """Takes a CameraControl instance and uses its camera."""
        self.camera_control = camera_control
        # self.stop_event = threading.Event()  # Create an event object

    def connect_camera(self):
        self.camera_control.initialize_camera()
        self.camera_control.open_camera()
        self.camera_control.start()
        self.camera_control.ImageObject()

    def disconnect_camera(self):
        self.camera_control.stop()
        self.camera_control.close()

    # def start_stream(self):
    #     self.stop_event.clear()  # Clear the event to start the stream
    #     self.stream_camera()
        
    # def stop_stream(self):
    #     self.stop_event.set()  # Set the event to stop the stream
    #     print("Stream stopped.")  # Debug print to confirm the method is called

    # def stream_camera(self):
    #     while not self.stop_event.is_set():  # Check if the event is set
    #         self.camera_control.get_image()
    #         image_data = self.camera_control.get_image_data()
    #         print(image_data)
    #     print("Stream loop ended.")  # Debug print to confirm the loop has ended

    def acquire_time_series(self, num_images):
        for i in range(num_images):
            self.camera_control.get_image()
            image_data = self.camera_control.get_image_data()
            print(image_data)


class CameraSettings:  
    """
    CameraSettings class provides configuration methods for Ximea cameras.

    Methods:
        __init__(camera_control): Takes a CameraControl instance to manage camera settings
        call_camera_command(cmd_name, method, value=None): Executes camera configuration commands
            - cmd_name: Name of the command (e.g. "exposure", "gain")
            - method: "get" to read current value, "set" to change value
            - value: New value when using "set" method (optional)

    The class uses commands.json to map friendly parameter names to the actual
    camera API commands. It dynamically calls the appropriate get/set methods
    on the camera object using reflection.

    Example usage:
        ctrl = CameraControl()
        settings = CameraSettings(ctrl)
        settings.call_camera_command("exposure", "set", 10000)  # Set 10ms exposure
        current_exp = settings.call_camera_command("exposure", "get")  # Read exposure

    Returns None if camera is not initialized or command fails.
    Prints error message explaining the failure reason.
    """
    def __init__(self, camera_control):
        """Takes a CameraControl instance and uses its camera."""
        self.camera_control = camera_control

    def call_camera_command(self, cmd_name, method, value=None):
        if not self.camera_control.camera:
            print("Camera not initialized.")
            return None

        for cmd in commands[method]:
            if cmd['cmd'] == cmd_name:
                method_name = f"{method}_{cmd_name}"
                if not hasattr(self.camera_control.camera, method_name):
                    print(f"Method {method_name} not found in xiapi.Camera")
                    return None

                camera_method = getattr(self.camera_control.camera, method_name)
                if method == "set" and value is not None:
                    return camera_method(value)
                elif method == "get":
                    return camera_method()
                else:
                    print(f"Invalid method or missing value for {method_name}")
                    return None

        print(f"Command {cmd_name} not found in {method} commands.")
        return None
