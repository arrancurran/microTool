import unittest
from unittest.mock import MagicMock, patch
import json
import os
import sys

# Add the parent directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from instruments.xicam.cam_methods import CameraControl
from ximea import xiapi

class TestCameraControl(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.camera_control = CameraControl()
        self.camera_control.camera = MagicMock(spec=xiapi.Camera)

    def test_initialization(self):
        """Test that the CameraControl class initializes correctly."""
        camera_control = CameraControl()
        self.assertIsNone(camera_control.camera)
        self.assertIsNone(camera_control.image)
        self.assertEqual(camera_control.set_commands, {})
        self.assertEqual(camera_control.get_commands, {})
        self.assertEqual(camera_control.set_commands_by_name, {})
        self.assertEqual(camera_control.get_commands_by_name, {})

    def test_load_commands(self):
        """Test that commands are loaded correctly from JSON."""
        self.camera_control._load_commands()
        
        # Verify that dictionaries are populated
        self.assertIn('exposure', self.camera_control.set_commands)
        self.assertIn('exposure_minimum', self.camera_control.get_commands)
        self.assertIn('exposure', self.camera_control.set_commands_by_name)
        self.assertIn('exposure_min', self.camera_control.get_commands_by_name)

    def test_set_command_with_friendly_name(self):
        """Test setting a camera parameter using friendly name."""
        self.camera_control._load_commands()
        self.camera_control.camera.set_exposure = MagicMock(return_value=None)
        
        # Test setting exposure using friendly name
        result = self.camera_control.call_camera_command("exposure", "set", 10000)
        
        # Verify the correct API method was called
        self.camera_control.camera.set_exposure.assert_called_once_with(10000)
        self.assertIsNone(result)

    def test_get_command_with_friendly_name(self):
        """Test getting a camera parameter using friendly name."""
        self.camera_control._load_commands()
        self.camera_control.camera.get_exposure_minimum = MagicMock(return_value=1000)
        
        # Test getting minimum exposure using friendly name
        result = self.camera_control.call_camera_command("exposure_min", "get")
        
        # Verify the correct API method was called and result
        self.camera_control.camera.get_exposure_minimum.assert_called_once()
        self.assertEqual(result, 1000)

    def test_invalid_friendly_name(self):
        """Test that invalid friendly names are handled correctly."""
        self.camera_control._load_commands()
        
        # Test with non-existent friendly name
        result = self.camera_control.call_camera_command("invalid_name", "get")
        self.assertIsNone(result)

    def test_camera_not_initialized(self):
        """Test behavior when camera is not initialized."""
        self.camera_control._load_commands()
        self.camera_control.camera = None
        
        # Test command call
        result = self.camera_control.call_camera_command("exposure", "set", 10000)
        self.assertIsNone(result)

    def test_set_command_without_value(self):
        """Test set command without providing a value."""
        self.camera_control._load_commands()
        
        # Test set command without value
        result = self.camera_control.call_camera_command("exposure", "set")
        self.assertIsNone(result)

    def test_get_command_with_value(self):
        """Test get command with an unexpected value parameter."""
        self.camera_control._load_commands()
        
        # Test get command with value
        result = self.camera_control.call_camera_command("exposure_min", "get", 10000)
        self.assertIsNone(result)

    def test_all_friendly_names(self):
        """Test that all friendly names from commands.json are accessible."""
        self.camera_control._load_commands()
        
        # Load commands.json for verification
        commands_path = os.path.join(project_root, 'instruments', 'xicam', 'commands.json')
        with open(commands_path, 'r') as file:
            commands = json.load(file)
        
        # Test all set commands
        for cmd in commands['set']:
            friendly_name = cmd['name']
            method_name = f"set_{cmd['cmd']}"
            setattr(self.camera_control.camera, method_name, MagicMock(return_value=None))
            
            # Test the command
            result = self.camera_control.call_camera_command(friendly_name, "set", 10000)
            # Verify the method was called
            getattr(self.camera_control.camera, method_name).assert_called_once_with(10000)
            self.assertIsNone(result)
        
        # Test all get commands
        for cmd in commands['get']:
            friendly_name = cmd['name']
            method_name = f"get_{cmd['cmd']}"
            setattr(self.camera_control.camera, method_name, MagicMock(return_value=1000))
            
            # Test the command
            result = self.camera_control.call_camera_command(friendly_name, "get")
            # Verify the method was called and result
            getattr(self.camera_control.camera, method_name).assert_called_once()
            self.assertEqual(result, 1000)

if __name__ == '__main__':
    unittest.main() 