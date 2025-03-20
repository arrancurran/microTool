import h5py
import numpy as np
from datetime import datetime

class HDF5Logger:
    """Handles saving image data to HDF5 files."""
    
    def __init__(self):
        self.current_file = None
        self.frame_count = 0
        self.dataset = None
        self.timestamps = None
    
    def start_recording(self, metadata=None):
        """Start a new recording session."""
        if self.current_file:
            print("Recording already in progress")
            return False
            
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{timestamp}.h5"
        
        try:
            # Open HDF5 file
            self.current_file = h5py.File(filename, 'w')
            
            # Store metadata
            if metadata:
                self.current_file.attrs.update(metadata)
            
            return True
            
        except Exception as e:
            print(f"Error starting recording: {str(e)}")
            if self.current_file:
                self.current_file.close()
                self.current_file = None
            return False
    
    def save_frame(self, frame, timestamp):
        """Save a single frame to the HDF5 file."""
        if not self.current_file:
            return False
            
        try:
            # Create dataset if this is the first frame
            if self.dataset is None:
                self.dataset = self.current_file.create_dataset(
                    'frames',
                    shape=(0,) + frame.shape,
                    maxshape=(None,) + frame.shape,
                    dtype=frame.dtype,
                    chunks=True
                )
                self.timestamps = self.current_file.create_dataset(
                    'timestamps',
                    shape=(0,),
                    maxshape=(None,),
                    dtype=np.float64
                )
            
            # Resize datasets
            self.dataset.resize(self.frame_count + 1, axis=0)
            self.timestamps.resize(self.frame_count + 1, axis=0)
            
            # Save data
            self.dataset[self.frame_count] = frame
            self.timestamps[self.frame_count] = timestamp
            
            self.frame_count += 1
            
            # Periodically flush to disk
            if self.frame_count % 100 == 0:
                self.current_file.flush()
                
            return True
            
        except Exception as e:
            print(f"Error saving frame: {str(e)}")
            return False
    
    def stop_recording(self):
        """Stop recording and close the file."""
        if not self.current_file:
            return
            
        try:
            # Final flush
            self.current_file.flush()
            self.current_file.close()
        except Exception as e:
            print(f"Error closing HDF5 file: {str(e)}")
        finally:
            self.current_file = None
            self.dataset = None
            self.timestamps = None
            self.frame_count = 0 