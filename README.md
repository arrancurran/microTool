# microTool

microTool is a Python application for interfacing with Ximea cameras, providing real-time image capture, display, and control capabilities. It features a modern Qt-based interface with modular camera controls and efficient image processing.

## Features

- Real-time camera streaming with optimized performance
- Modular camera control system
- Exposure and ROI (Region of Interest) controls
- Live histogram visualization
- Thread-safe camera command execution
- Easy-to-extend control framework

## Project Structure

```
microTool/
├── app.py                          # Main application entry point
├── acquisitions/                # Image acquisition code
│   └── stream_camera.py  # Camera streaming functionality
│
├── interface/             # UI-related code
│   ├── ui.py            # Main UI layout
│   ├── ui_methods.py    # UI event handlers
│   └── camera_controls/ # Camera control components
│       ├── base_control.py     # Base control classes
│       ├── control_manager.py  # Control management
│       ├── exposure_control.py # Exposure settings
│       └── roi_control.py      # ROI settings
│
├── instruments/          # Hardware interaction
│   └── xicam/           # Ximea camera specific code
│       ├── cam_methods.py    # Camera control methods
│       └── commands.json     # Camera command definitions
│
├── utils/               # Utility functions
│   └── image.py        # Image processing utilities
│
├── docs/               # Documentation
└── tests/              # Test files
```

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/microTool.git
   cd microTool
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Ximea Camera API (xiAPI):**
   - Visit [Ximea API Software Package](https://www.ximea.com/support/wiki/apis/XIMEA_API_Software_Package)
   - Download version appropriate for your OS
   - For macOS ARM: Download xiAPI LTS V4.28.00 or later
   - Follow platform-specific installation instructions

## Usage

1. **Start the application:**
   ```bash
   python app.py
   ```

2. **Camera Controls:**
   - Use the exposure slider to adjust exposure time
   - Set ROI parameters (width, height, offset_x, offset_y)
   - Monitor live histogram updates
   - Start/stop camera stream using toolbar buttons

3. **Adding New Controls:**
   - See `docs/adding_camera_controls.md` for detailed instructions
   - Follow the modular control system architecture
   - Use the base control classes for consistency

## Development

1. **Project Requirements:**
   - Python 3.8+
   - Dependencies listed in requirements.txt
   - Ximea camera API (xiAPI)

2. **Code Structure:**
   - Modular design with clear separation of concerns
   - Thread-safe camera operations
   - Extensible control system

3. **Testing:**
   ```bash
   python -m pytest tests/
   ```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the GNU License. See the LICENSE file for details.

## Acknowledgments

- Ximea for their camera API
- PyQt6 for the UI framework
- Contributors and maintainers