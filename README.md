# Ximea Image Capture Application

This project is a Python application that interfaces with a Ximea camera to capture and display images. It provides a simple graphical interface for viewing the images captured by the camera.

## Project Structure

```
ximea-image-app
├── src
│   ├── main.py          # Entry point of the application
│   ├── camera.py        # Camera interface for capturing images
│   └── utils.py         # Utility functions for image display
├── requirements.txt      # List of dependencies
└── README.md             # Project documentation
```

## Installation

To set up the project, follow these steps:

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/ximea-image-app.git
   cd ximea-image-app
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

To run the application, execute the following command:

```
python src/main.py
```

This will initialize the Ximea camera, capture an image, and display it in a window.

## Dependencies

The project requires the following Python packages:

- ximea: For interfacing with the Ximea camera.
- OpenCV or PIL: For displaying images.

Make sure to check the `requirements.txt` file for the exact versions needed.

## Contributing

If you would like to contribute to this project, please fork the repository and submit a pull request with your changes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.