# Adding New Camera Controls

This guide explains how to add new controls for camera parameters to the ColloidCam application.

## Overview

The camera control system is designed to be modular and extensible. Each control (like exposure, gain, etc.) follows the same pattern and inherits from a base control class.

## Steps to Add a New Control

### 1. Add Camera Commands

First, add the new control's commands to `instruments/xicam/commands.json`. You need to add both set and get commands:

```json
{
    "set": [
        // ... existing commands ...
        {
            "cmd": "your_command",      // The actual camera API command
            "type": "float",           // Data type: "float", "int", or "str"
            "name": "friendly_name"    // Friendly name used in the code
        }
    ],
    "get": [
        // ... existing commands ...
        {
            "cmd": "your_command_minimum",
            "type": "float",
            "name": "friendly_name_min"
        },
        {
            "cmd": "your_command_maximum",
            "type": "float",
            "name": "friendly_name_max"
        },
        {
            "cmd": "your_command",
            "type": "float",
            "name": "friendly_name"
        }
    ]
}
```

### 2. Add UI Elements

Add the required UI elements to `interface/ui.py`. Each control typically needs:
- A slider (`QSlider`)
- A label (`QLabel`)

Example:
```python
# In the ui class
self.your_control_slider = QSlider(Qt.Orientation.Horizontal)
self.your_control_label = QLabel()
self.your_control_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

# Add to layout
layout.addWidget(self.your_control_slider)
layout.addWidget(self.your_control_label)
```

### 3. Create Control Class

Create a new file `interface/camera_controls/your_control.py` that inherits from the appropriate base class:

```python
from .base_control import NumericCameraControl  # For numeric controls

class YourControl(NumericCameraControl):
    def __init__(self, camera_control, window):
        super().__init__(
            camera_control=camera_control,
            window=window,
            command_name="friendly_name",  # Must match commands.json
            display_name="Display Name"
        )
    
    def setup_ui(self) -> bool:
        """Set up the UI elements."""
        # Check UI elements exist
        if not hasattr(self.window, 'your_control_slider'):
            print("Error: your_control_slider not found")
            return False
        if not hasattr(self.window, 'your_control_label'):
            print("Error: your_control_label not found")
            return False
        
        try:
            # Get settings from camera
            settings = super().setup_ui()
            if not settings:
                return False
            
            # Convert values if needed (e.g., float to int for slider)
            min_val = int(round(settings['min']))
            max_val = int(round(settings['max']))
            current = int(round(settings['current']))
            
            # Configure slider
            self.window.your_control_slider.setMinimum(min_val)
            self.window.your_control_slider.setMaximum(max_val)
            
            # Connect signal
            try:
                self.window.your_control_slider.valueChanged.disconnect()
            except Exception:
                pass
            self.window.your_control_slider.valueChanged.connect(self.handle_value_change)
            
            # Set initial value
            self.window.your_control_slider.setValue(current)
            self._format_and_update_label(current)
            
            return True
            
        except Exception as e:
            print(f"Error setting up control: {str(e)}")
            return False
    
    def _format_and_update_label(self, value):
        """Format and update the label."""
        try:
            formatted_value = f"Your Control: {value} units"
            self.window.your_control_label.setText(formatted_value)
        except Exception as e:
            print(f"Error updating label: {str(e)}")
    
    def handle_value_change(self, value):
        """Handle value changes."""
        self._format_and_update_label(value)
        # Convert value if needed (e.g., int to float)
        super().handle_value_change(float(value))
```

### 4. Register the Control

Add your control to the `CONTROL_TYPES` dictionary in `interface/camera_controls/control_manager.py`:

```python
from .your_control import YourControl

class CameraControlManager:
    CONTROL_TYPES = {
        # ... existing controls ...
        'your_control': YourControl,
    }
```

## Control Types

### Numeric Controls
- Inherit from `NumericCameraControl`
- Used for parameters with numeric values (exposure, gain, etc.)
- Handles value conversion between UI and camera
- Includes built-in debouncing

### Boolean Controls
- Inherit from `BooleanCameraControl` (if implemented)
- Used for on/off settings
- Typically uses checkboxes or toggle buttons

### Enum Controls
- Inherit from `EnumCameraControl` (if implemented)
- Used for settings with predefined options
- Typically uses combo boxes or radio buttons

## Best Practices

1. **Type Conversion**
   - Convert between UI types (usually int for sliders) and camera types (often float)
   - Use appropriate rounding and type casting

2. **Error Handling**
   - Always check if UI elements exist
   - Handle exceptions in all operations
   - Provide meaningful error messages

3. **Debug Logging**
   - Add debug prints for initialization
   - Log value changes and camera commands
   - Include relevant values in log messages

4. **Value Formatting**
   - Format displayed values appropriately
   - Include units where applicable
   - Use appropriate precision for floating-point values

5. **Signal Connections**
   - Disconnect existing connections before connecting new ones
   - Use appropriate debounce timing for rapid changes

## Testing

1. Test the control with:
   - Minimum and maximum values
   - Rapid value changes
   - Invalid values
   - Camera disconnection/reconnection
   - UI resize and updates

2. Verify that:
   - Values are correctly converted
   - Labels update properly
   - Camera receives correct commands
   - Error conditions are handled gracefully 