import unittest
import numpy as np
import time
import os
import sys
from queue import Queue
import h5py
import psutil

# Add parent directory to Python path to find acquisitions module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from acquisitions.record_stream import RecordStream
from acquisitions.log_HDF5 import HDF5Logger

class MockCamera:
    def __init__(self, frame_size=(2048, 2048)):
        self.frame_size = frame_size
        self.device_name = b"Test Camera"
        
    def get_device_name(self):
        return self.device_name

class MockCameraControl:
    def __init__(self, frame_size=(2048, 2048), simulate_delay=0.001):
        self.frame_size = frame_size
        self.camera = MockCamera(frame_size)
        self.simulate_delay = simulate_delay
        self.frame_count = 0
        
    def start_camera(self):
        pass
        
    def stop_camera(self):
        pass
        
    def get_image(self):
        time.sleep(self.simulate_delay)  # Simulate camera delay
        self.frame_count += 1
        
    def get_image_data(self):
        return np.random.randint(0, 255, self.frame_size, dtype=np.uint8)
        
    def call_camera_command(self, cmd, action, value=None):
        if cmd == "exposure":
            return 1000
        elif cmd in ["width", "height"]:
            return self.frame_size[0]
        elif cmd in ["offset_x", "offset_y"]:
            return 0
        return 0

class MockStreamCamera:
    def __init__(self, frame_size=(2048, 2048), simulate_delay=0.001):
        self.camera_control = MockCameraControl(frame_size, simulate_delay)
        self.camera_thread = None

class MockWindow:
    def __init__(self):
        self.stop_stream = self
        self.start_stream = self
        
    def trigger(self):
        pass

class TestRecordingSpeed(unittest.TestCase):
    def setUp(self):
        self.frame_size = (2048, 2048)  # 2MP image
        self.test_duration = 5  # Test duration in seconds
        self.camera = MockStreamCamera(self.frame_size)
        self.window = MockWindow()
        
    def test_recording_speed(self):
        """Test recording and saving speeds."""
        print("\nTesting recording performance:")
        print(f"Frame size: {self.frame_size[0]}x{self.frame_size[1]} pixels")
        print(f"Test duration: {self.test_duration} seconds")
        
        # Initialize recorder
        recorder = RecordStream(self.camera, self.window)
        
        # Start recording
        start_time = time.time()
        recorder.start_recording()
        
        # Monitor performance for test duration
        frames_recorded = []
        frames_saved = []
        queue_sizes = []
        
        while time.time() - start_time < self.test_duration:
            frames_recorded.append(recorder.queue.frames_recorded)
            frames_saved.append(recorder.queue.frames_saved)
            queue_sizes.append(recorder.queue.frame_queue.qsize())
            time.sleep(0.1)
        
        # Stop recording and wait for completion
        recorder.stop_recording()
        
        # Wait for cleanup to complete (max 30 seconds)
        cleanup_start = time.time()
        while not recorder.queue.is_empty() and time.time() - cleanup_start < 30:
            time.sleep(0.1)
        
        # Calculate statistics
        total_frames = recorder.queue.frames_recorded
        total_saved = recorder.queue.frames_saved
        total_dropped = recorder.queue.frames_dropped
        avg_queue_size = sum(queue_sizes) / len(queue_sizes)
        
        # Calculate frame rates
        recording_duration = time.time() - start_time
        recording_fps = total_frames / recording_duration if recording_duration > 0 else 0
        saving_fps = total_saved / recording_duration if recording_duration > 0 else 0
        
        # Print results
        print("\nRecording Statistics:")
        print(f"Total frames recorded: {total_frames}")
        print(f"Total frames saved: {total_saved}")
        print(f"Frames dropped: {total_dropped}")
        print(f"Average queue size: {avg_queue_size:.1f}")
        print(f"Recording frame rate: {recording_fps:.1f} fps")
        print(f"Saving frame rate: {saving_fps:.1f} fps")
        
        # Basic assertions
        self.assertGreater(total_frames, 0, "No frames were recorded")
        self.assertGreater(total_saved, 0, "No frames were saved")
        self.assertLessEqual(total_dropped, total_frames * 0.1, "Too many frames were dropped (>10%)")
        
        # Check if queue was properly managed
        self.assertEqual(recorder.queue.frame_queue.qsize(), 0, "Queue was not properly emptied")
        
        # Verify frame rates are reasonable
        self.assertGreater(recording_fps, 0, "Recording frame rate should be positive")
        self.assertGreater(saving_fps, 0, "Saving frame rate should be positive")
        self.assertLessEqual(saving_fps, recording_fps, "Saving rate should not exceed recording rate")

if __name__ == '__main__':
    unittest.main() 