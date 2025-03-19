"""
Provides camera control and settings management for Ximea cameras. Here we define methods that speak directly to the camera using the XiAPI.
For a different camera, we would need to rewrite this module to speak to the new camera.

CameraControl: Handles core camera operations like:
- Initializing/closing the camera connection
- Starting/stopping image acquisition 
- Capturing individual images and accessing image data
- Managing camera configuration parameters through command parsing from commands.json

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
        call_camera_command(): Executes camera commands using friendly names from commands.json

    The class uses the ximea.xiapi library to interface directly with Ximea cameras.
    Images are stored in xiapi.Image objects which contain both pixel data and metadata.
    See https://www.ximea.com/support/wiki/apis/XiAPI_Python_Manual#xiApiPython_Image-XI_IMG

    Example usage:
        ctrl = CameraControl()
        ctrl.initialize_camera()
        ctrl.call_camera_command("exposure", "set", 10000)  # Set 10ms exposure
        current_exp = ctrl.call_camera_command("exposure_min", "get")  # Read minimum exposure

    TODO: We should set a custom size for ImageObject() according to the camera resolution
    TODO: We should also set the image format to mono8 or mono16 depending on the camera
    """
    def __init__(self):
        """Initialize the camera object but do not start it."""
        self.camera = None
        self.image = None
        self.set_commands = {}
        self.get_commands = {}
        self.set_commands_by_name = {}
        self.get_commands_by_name = {}
        
    def _load_commands(self):
        """Load camera commands from the JSON file."""
        with open('instruments/xicam/commands.json', 'r') as file:
            commands = json.load(file)
        self.set_commands = {cmd['cmd']: cmd for cmd in commands['set']}
        self.get_commands = {cmd['cmd']: cmd for cmd in commands['get']}
        self.set_commands_by_name = {cmd['name']: cmd for cmd in commands['set']}
        self.get_commands_by_name = {cmd['name']: cmd for cmd in commands['get']}
        
    def initialize_camera(self):
        """Initialize the camera object."""
        if self.camera is None:
            self.camera = xiapi.Camera()
            self._load_commands()
            print("CameraControl.initialize_camera(): Camera initialized.")
        else:
            print("CameraControl.initialize_camera(): Camera already initialized.")

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

    def start_camera(self):
        if self.camera:
            self.camera.start_acquisition()
            print("CameraControl.start_camera(): Camera acquisition started.")
        else:
            print("CameraControl.start_camera(): Camera not initialized.")
    
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
    
    def stop_camera(self):
        if self.camera:
            self.camera.stop_acquisition()
            print("CameraControl.stop_camera(): Camera acquisition stopped.")
        else:
            print("CameraControl.stop_camera(): Camera not initialized.")

    def close(self):
        if self.camera:
            self.camera.close_device()
            print("CameraControl.close(): Camera closed.")
            self.camera = None  # Reset the camera instance
        else:
            print("CameraControl.close(): Camera not initialized.")

    def call_camera_command(self, friendly_name, method, value=None):
        """
        Call a camera command using a friendly name.
        
        Args:
            friendly_name (str): The friendly name of the command from commands.json
            method (str): Either "set" or "get"
            value: The value to set (only for set commands)
            
        Returns:
            The result of the command for get commands, None for set commands
        """
        if not self.camera:
            print("CameraControl.call_camera_command(): Camera not initialized.")
            return None

        # Look up command by friendly name in the appropriate dictionary
        cmd_dict = self.set_commands_by_name if method == "set" else self.get_commands_by_name
        if friendly_name not in cmd_dict:
            print(f"CameraControl.call_camera_command(): Command with friendly name '{friendly_name}' not found in {method} commands.")
            return None

        # Get the original command name for the API call
        cmd_info = cmd_dict[friendly_name]
        api_cmd_name = cmd_info['cmd']
        method_name = f"{method}_{api_cmd_name}"
        
        if not hasattr(self.camera, method_name):
            print(f"CameraControl.call_camera_command(): Method {method_name} not found in xiapi.Camera")
            return None

        # Check for invalid parameter combinations
        if method == "get" and value is not None:
            print(f"CameraControl.call_camera_command(): Get command '{friendly_name}' should not have a value parameter")
            return None
        elif method == "set" and value is None:
            print(f"CameraControl.call_camera_command(): Set command '{friendly_name}' requires a value parameter")
            return None

        camera_method = getattr(self.camera, method_name)
        if method == "set":
            return camera_method(value)
        else:  # method == "get"
            return camera_method()

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

    def connect_camera(self):
        self.camera_control.initialize_camera()
        self.camera_control.open_camera()
        self.camera_control.ImageObject()
    
    def disconnect_camera(self):
        self.camera_control.close()

    def acquire_time_series(self, num_images):
        for i in range(num_images):
            self.camera_control.get_image()
            image_data = self.camera_control.get_image_data()
            print(image_data)
