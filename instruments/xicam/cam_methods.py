import json
from ximea import xiapi
from queue import Queue
from threading import Lock, Thread

from . import logger

class CameraControl:
    
    # TODO: We should set a custom size for ImageObject() according to the camera resolution
    # TODO: We should also set the image format to mono8 or mono16 depending on the camera

    def __init__(self):
        
        """Initialize the camera object."""
        self.camera = None
        self.image = None
        self.set_commands = {}
        self.get_commands = {}
        self.set_commands_by_name = {}
        self.get_commands_by_name = {}
        # Setup queue for camera commands
        self.command_queue = Queue()
        # Setup lock for camera access, ensures only one command is sent to the camera at a time
        self.camera_lock = Lock()
        self.command_thread = None
        self.running = True
                
    def _load_commands_from_json(self):
               
        with open('instruments/xicam/commands.json', 'r') as file:
            commands = json.load(file)
        self.set_commands = {cmd['cmd']: cmd for cmd in commands['set']}
        self.get_commands = {cmd['cmd']: cmd for cmd in commands['get']}
        self.set_commands_by_name = {cmd['name']: cmd for cmd in commands['set']}
        self.get_commands_by_name = {cmd['name']: cmd for cmd in commands['get']}
    
    def start_command_thread(self):
        
        if self.command_thread is None:
            self.running = True
            self.command_thread = Thread(target=self._process_commands_from_queue, name="CameraControlThread")
            self.command_thread.daemon = True
            self.command_thread.start()
    
    def stop_command_thread(self):
        
        self.running = False
        if self.command_thread:
            self.command_thread.join()
            self.command_thread = None
    
    def _process_commands_from_queue(self):
        
        while self.running:
            try:
                command = self.command_queue.get(timeout=0.1)
                if command is None:
                    continue
                
                friendly_name, method, value, result_queue = command
                
                with self.camera_lock:
                    try:
                        result = self._execute_camera_command(friendly_name, method, value)
                        if result_queue:
                            result_queue.put(result)
                    except Exception as e:
                        logger.error(f"Error executing camera command: {str(e)}")
                        if result_queue:
                            result_queue.put(None)
                
                self.command_queue.task_done()
            except:
                """Timeout on queue, continue loop"""
                continue
    
    def _execute_camera_command(self, friendly_name, method, value=None):
        if not self.camera:
            logger.error("Camera not initialized.")
            return None

        cmd_dict = self.set_commands_by_name if method == "set" else self.get_commands_by_name
        if friendly_name not in cmd_dict:
            logger.error(f"Command with friendly name '{friendly_name}' not found in {method} commands.")
            return None

        cmd_info = cmd_dict[friendly_name]
        api_cmd_name = cmd_info['cmd']
        method_name = f"{method}_{api_cmd_name}"
        
        if not hasattr(self.camera, method_name):
            logger.error(f"Method {method_name} not found in xiapi.Camera")
            return None

        try:
            camera_method = getattr(self.camera, method_name)
            if method == "set":
                # Convert value to the correct type
                value_type = cmd_info.get('type', 'float')
                try:
                    if value_type == 'float':
                        value = float(value)
                    elif value_type == 'int':
                        value = int(value)
                except (ValueError, TypeError) as e:
                    logger.error(f"Error converting value to {value_type}: {str(e)}")
                    return None
                    
                logger.debug(f"Setting {friendly_name} to {value} ({type(value)})")  # Debug print
                camera_method(value)
                return value
            else:  # method == "get"
                logger.debug(f"Getting {friendly_name} value")  # Debug print
                result = camera_method()
                return result
            
        except Exception as e:
            logger.error(f"Error executing camera command {method_name}: {str(e)}")
            return None
    
    def call_camera_command(self, friendly_name, method, value=None):
        
        """Queue a camera command and wait for its result."""
        result_queue = Queue() if method == "get" else None
        self.command_queue.put((friendly_name, method, value, result_queue))
        
        if result_queue:
            try:
                result = result_queue.get(timeout=2.0)  # 2 second timeout for get operations
                return result
            except:
                logger.error("Timeout waiting for camera command result")
                return None
        return None
        
    def initialize_camera(self):
        
        """Initialize the camera object."""
        if self.camera is None:
            with self.camera_lock:
                self.camera = xiapi.Camera()
                logger.debug("CameraControl.initialize_camera(): Camera object created.")
                self._load_commands_from_json()  # Load commands first
                logger.debug("CameraControl.initialize_camera(): Commands loaded.")
                self.start_command_thread()
                logger.debug("CameraControl.initialize_camera(): Command thread started.")
        else:
            logger.debug("CameraControl.initialize_camera(): Camera already initialized.")

    def open_camera(self):
        
        """Open the camera."""
        if self.camera:
            with self.camera_lock:
                self.camera.open_device()
                logger.debug("CameraControl.open_camera(): Camera connection established.")
        else:
            logger.error("CameraControl.open_camera(): Camera connection not established.")

    def ImageObject(self):
        
        """Create an image object."""
        if self.image is None:
            self.image = xiapi.Image()
            logger.debug("CameraControl.ImageObject(): Image object created.")
        else:
            logger.debug("CameraControl.ImageObject(): Image object already created.")

    def start_camera(self):
        
        """Start the camera."""
        if self.camera:
            with self.camera_lock:
                self.camera.start_acquisition()
                logger.debug("CameraControl.start_camera(): Camera acquisition started.")
        else:
            logger.error("CameraControl.start_camera(): Camera failed to start acquisition.")
    
    def get_image(self):
        
        """Get an image from the camera."""
        if self.image:
            with self.camera_lock:
                return self.camera.get_image(self.image)
        else:
            logger.error("CameraControl.get_image(): Image object doesn't exist.")

    def get_image_data(self):
        
        """Get the image data as a numpy array."""
        if self.image:
            return self.image.get_image_data_numpy()
        else:
            logger.error("CameraControl.get_image_data(): Failed to get image numpy data.")
    
    def get_image_timestamp(self):
        
        """Get the image timestamp."""
        if self.image:
            tsSec = self.image.tsSec
            tsUSec = self.image.tsUSec
            timestamp = tsSec + tsUSec / 1e6
            return timestamp
        else:
            logger.error("CameraControl.get_image_timestamp(): Failed to get image timestamp.")
    
    def stop_camera(self):
        
        """Stop the camera."""
        if self.camera:
            with self.camera_lock:
                self.camera.stop_acquisition()
                logger.debug("CameraControl.stop_camera(): Camera acquisition stopped.")
        else:
            logger.error("CameraControl.stop_camera(): Camera failed to stop acquisition.")

    def close(self):
        
        """Close the camera."""
        self.stop_command_thread()
        if self.camera:
            with self.camera_lock:
                self.camera.close_device()
                logger.debug("CameraControl.close(): Camera closed.")
                self.camera = None
        else:
            logger.error("CameraControl.close(): Camera failed to close.")

class CameraSequences():
    """
    Handles high-level camera acquisition patterns like streaming and time series capture.

    Called by:
    - app.py: Main application initializes CameraSequences on startup
    - interface/ui_methods.py: UIMethods uses sequences for camera operations
    - acquisitions/stream_camera.py: LiveStreamHandler uses sequences for streaming

    Example usage:
        # Initialize camera control and sequences
        ctrl = CameraControl()
        sequences = CameraSequences(ctrl)

        # Start streaming
        sequences.connect_camera()
        sequences.stream_camera()  # Continuous acquisition
        
        # Or capture time series
        sequences.acquire_time_series(100)  # 100 frames
        
        # Cleanup
        sequences.disconnect_camera()
    """
    def __init__(self, camera_control):
        
        """Takes a CameraControl instance and uses its camera."""
        self.camera_control = camera_control

    def connect_camera(self):
        
        """Connection sequence for the Ximea camera."""
        self.camera_control.initialize_camera()
        self.camera_control.open_camera()
        self.camera_control.ImageObject()
    
    def disconnect_camera(self):
        
        """Disconnect from the Ximea camera."""
        self.camera_control.close()

    def acquire_time_series(self, num_images):
        for i in range(num_images):
            return self.camera_control.get_image()
