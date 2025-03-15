# ColloidCam

ColloidCam is a Python application designed to interface with a Ximea camera for capturing and displaying images. It provides a graphical interface for viewing images captured by the camera, utilizing various Python libraries for image processing and GUI development.

## Project Structure

```
ColloidCam
├── instruments
│ ├── camera.py # Camera interface for capturing images
│ └── init.py # Package initialization
├── interface
│ ├── ui_camera.py # User interface components for camera interaction
│ ├── interface.py # Main interface logic
│ └── init.py # Package initialization
├── utils.py # Utility functions for image processing
├── main.py # Entry point of the application
├── requirements.txt # List of dependencies
└── README.md # Project documentation
```

## Installation

To set up the project, follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ColloidCam.git
   cd ColloidCam
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

   **Note:** The Ximea API is not included in pip. You must download it from [Ximea's software downloads](https://www.ximea.com/software-downloads) and install it manually. This project was developed with macOS ARM xiAPI LTS V4.28.00.

## Usage

To run the application, execute the following command:

```bash
python main.py
```

This will initialize the Ximea camera, capture an image, and display it in a window.

## Dependencies

The project requires the following Python packages:

- OpenCV: For image processing.
- Pillow: For image handling.
- QtAwesome and PyQt6: For GUI components.
- Matplotlib: For plotting and visualization.

Make sure to check the `requirements.txt` file for the exact versions needed.

## Contributing

If you would like to contribute to this project, please fork the repository and submit a pull request with your changes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.