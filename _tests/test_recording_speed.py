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
            frames_recorded.append(recorder.frames_recorded)
            frames_saved.append(recorder.frames_saved)
            queue_sizes.append(recorder.frame_queue.qsize())
            time.sleep(0.1)
        
        # Stop recording and wait for completion
        recorder.stop_recording()
        
        # Wait for cleanup to complete (max 30 seconds)
        cleanup_timeout = 30
        cleanup_start = time.time()
        while time.time() - cleanup_start < cleanup_timeout:
            if recorder.frame_queue.empty() and not recorder.is_saving:
                break
            time.sleep(0.1)
        
        # Get final counts
        final_recorded = recorder.frames_recorded
        final_saved = recorder.frames_saved
        final_dropped = recorder.frames_dropped
        
        # Calculate metrics
        total_time = time.time() - start_time
        fps_recorded = final_recorded / self.test_duration  # Use test duration for recording speed
        fps_saved = final_saved / total_time  # Use total time for saving speed
        avg_queue_size = sum(queue_sizes) / len(queue_sizes)
        max_queue_size = max(queue_sizes)
        
        # Get file size
        filename = None
        for file in os.listdir():
            if file.startswith("recording_") and file.endswith(".h5"):
                filename = file
                break
        
        file_size = os.path.getsize(filename) if filename else 0
        mb_per_second = (file_size / 1024 / 1024) / total_time
        
        # Print results
        print("\nPerformance Results:")
        print(f"Frames recorded: {final_recorded}")
        print(f"Frames saved: {final_saved}")
        print(f"Frames dropped: {final_dropped}")
        print(f"Recording speed: {fps_recorded:.1f} fps")
        print(f"Saving speed: {fps_saved:.1f} fps")
        print(f"Average queue utilization: {avg_queue_size:.1f} frames")
        print(f"Maximum queue utilization: {max_queue_size} frames")
        print(f"Data rate: {mb_per_second:.1f} MB/s")
        
        # Additional memory metrics
        frame_size_mb = (self.frame_size[0] * self.frame_size[1]) / (1024 * 1024)
        theoretical_rate = frame_size_mb * fps_recorded
        print(f"Frame size: {frame_size_mb:.1f} MB")
        print(f"Theoretical data rate: {theoretical_rate:.1f} MB/s")
        if mb_per_second > 0:
            print(f"Compression ratio: {theoretical_rate/mb_per_second:.1f}x")
        
        # Cleanup
        if filename:
            os.remove(filename)
        
        # Assertions
        self.assertGreater(fps_recorded, 0, "Recording speed should be positive")
        self.assertGreater(fps_saved, 0, "Saving speed should be positive")
        
        # Verify that all non-dropped frames were saved
        frames_handled = final_saved + final_dropped
        frame_diff = abs(final_recorded - frames_handled)
        max_allowed_diff = 5  # Allow up to 5 frames difference
        self.assertLessEqual(frame_diff, max_allowed_diff, 
                           f"Too many unsaved frames: {frame_diff} (max allowed: {max_allowed_diff})")
        
        # Verify reasonable performance
        min_fps = 10  # Minimum acceptable fps
        self.assertGreater(fps_recorded, min_fps, f"Recording too slow: {fps_recorded:.1f} fps < {min_fps} fps")
        self.assertGreater(fps_saved, min_fps, f"Saving too slow: {fps_saved:.1f} fps < {min_fps} fps")

if __name__ == '__main__':
    unittest.main() 