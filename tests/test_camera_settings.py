import unittest
from unittest.mock import MagicMock, patch
import json
import os
import sys

# Add the parent directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from instruments.xicam.cam_methods import CameraSettings, CameraControl

class TestCameraSettings(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a mock camera control
        self.mock_camera_control = MagicMock(spec=CameraControl)
        self.mock_camera_control.camera = MagicMock()
        
        # Create instance of CameraSettings
        self.settings = CameraSettings(self.mock_camera_control)

    def test_initialization(self):
        """Test that the CameraSettings class initializes correctly."""
        # Check that dictionaries are created
        self.assertIsInstance(self.settings.set_commands, dict)
        self.assertIsInstance(self.settings.get_commands, dict)
        self.assertIsInstance(self.settings.set_commands_by_name, dict)
        self.assertIsInstance(self.settings.get_commands_by_name, dict)

    def test_set_command_with_friendly_name(self):
        """Test setting a camera parameter using friendly name."""
        # Set up mock method
        self.mock_camera_control.camera.set_exposure = MagicMock(return_value=None)
        
        # Test setting exposure using friendly name
        self.settings.call_camera_command("exposure", "set", 10000)
        
        # Verify the correct API method was called
        self.mock_camera_control.camera.set_exposure.assert_called_once_with(10000)

    def test_get_command_with_friendly_name(self):
        """Test getting a camera parameter using friendly name."""
        # Set up mock method
        self.mock_camera_control.camera.get_exposure_minimum = MagicMock(return_value=1000)
        
        # Test getting minimum exposure using friendly name
        result = self.settings.call_camera_command("exposure_min", "get")
        
        # Verify the correct API method was called and result
        self.mock_camera_control.camera.get_exposure_minimum.assert_called_once()
        self.assertEqual(result, 1000)

    def test_invalid_friendly_name(self):
        """Test that invalid friendly names are handled correctly."""
        # Test with non-existent friendly name
        result = self.settings.call_camera_command("invalid_name", "get")
        self.assertIsNone(result)

    def test_camera_not_initialized(self):
        """Test behavior when camera is not initialized."""
        # Set camera to None
        self.settings.camera_control.camera = None
        
        # Test command call
        result = self.settings.call_camera_command("exposure", "set", 10000)
        self.assertIsNone(result)

    def test_set_command_without_value(self):
        """Test set command without providing a value."""
        result = self.settings.call_camera_command("exposure", "set")
        self.assertIsNone(result)

    def test_get_command_with_value(self):
        """Test get command with an unexpected value parameter."""
        # Set up mock method
        self.mock_camera_control.camera.get_exposure_minimum = MagicMock(return_value=None)
        
        # Test get command with value (should return None)
        result = self.settings.call_camera_command("exposure_min", "get", 10000)
        self.assertIsNone(result)
        
        # Verify the method was not called
        self.mock_camera_control.camera.get_exposure_minimum.assert_not_called()

    def test_all_friendly_names(self):
        """Test that all friendly names from commands.json are accessible."""
        # Load commands.json
        commands_path = os.path.join(project_root, 'instruments', 'xicam', 'commands.json')
        with open(commands_path, 'r') as file:
            commands = json.load(file)
        
        # Test all set commands
        for cmd in commands['set']:
            friendly_name = cmd['name']
            # Set up mock method
            method_name = f"set_{cmd['cmd']}"
            setattr(self.mock_camera_control.camera, method_name, MagicMock(return_value=None))
            
            # Test the command
            self.settings.call_camera_command(friendly_name, "set", 10000)
            # Verify the method was called
            getattr(self.mock_camera_control.camera, method_name).assert_called_once_with(10000)
        
        # Test all get commands
        for cmd in commands['get']:
            friendly_name = cmd['name']
            # Set up mock method
            method_name = f"get_{cmd['cmd']}"
            setattr(self.mock_camera_control.camera, method_name, MagicMock(return_value=1000))
            
            # Test the command
            result = self.settings.call_camera_command(friendly_name, "get")
            # Verify the method was called and result
            getattr(self.mock_camera_control.camera, method_name).assert_called_once()
            self.assertEqual(result, 1000)

if __name__ == '__main__':
    unittest.main() 