"""
HDF5 logging for camera acquisitions.
"""
import h5py, time, threading, logging
import numpy as np
from datetime import datetime
from interface.status_bar.update_notif import update_notif

logger = logging.getLogger(__name__)

class HDF5Handler:
    
    def __init__(self):
        self.create_hdf5 = None
        self.dataset = None
        self.timestamps = None
        self.frame_count = 0
        self.is_saving = False
        self.saving_thread = None
        
    def init_h5File(self, metadata=None):
        if self.create_hdf5:
            return False            
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.create_hdf5 = h5py.File(f"recording_{timestamp}.h5", 'w')
            # Store metadata if provided
            if metadata:
                self.create_hdf5.attrs.update(metadata)
            
            return True
            
        except Exception as e:
            logger.error(f"Error initialising h5 file: {e}")
            self._cleanup()
            return False
    
    def init_saving_thread(self, queue):
        if self.is_saving:
            return False
        
        self.is_saving = True
        self.saving_thread = threading.Thread(target=self._save_frames, args=(queue,), daemon=True)
        self.saving_thread.start()
        return True
        
    def stop_saving_thread(self):
        self.is_saving = False
        if self.saving_thread:
            self.saving_thread.join(timeout=5.0)
            
    def _save_frames(self, queue):
        last_update = 0
        start_time = time.time()
        
        while self.is_saving or not queue.is_empty():
            try:
                frame, timestamp = queue.get_frame(timeout=0.1)
                if frame is None:
                    continue
                
                if self._save_frame(frame, timestamp):
                    queue.frames_saved += 1
                    
                current_time = time.time()
                if not self.is_saving and current_time - last_update >= 1.0:
                    self._update_save_status(queue, current_time, start_time)
                    last_update = current_time
                    
            except Exception as e:
                logger.error(f"Error saving frame: {e}")
                time.sleep(0.1)
                
    def _save_frame(self, frame, timestamp):
        """Save a single frame to the HDF5 create_hdf5."""
        if not self.create_hdf5:
            return False
            
        try:
            # Initialize datasets on first frame
            if self.dataset is None:
                self.dataset = self.create_hdf5.create_dataset(
                    'frames',
                    shape=(0,) + frame.shape,
                    maxshape=(None,) + frame.shape,
                    dtype=frame.dtype,
                    chunks=True
                )
                self.timestamps = self.create_hdf5.create_dataset(
                    'timestamps',
                    shape=(0,),
                    maxshape=(None,),
                    dtype=np.float64
                )
            
            # Resize datasets before writing
            new_size = self.frame_count + 1
            self.dataset.resize(new_size, axis=0)
            self.timestamps.resize(new_size, axis=0)
            
            # Save frame and timestamp
            self.dataset[self.frame_count] = frame
            self.timestamps[self.frame_count] = timestamp
            self.frame_count = new_size
            
            # Periodic flush to disk
            if self.frame_count % 100 == 0:
                self.create_hdf5.flush()
                
            return True
            
        except Exception as e:
            logger.error(f"Error saving frame: {e}")
            return False
            
    def _update_save_status(self, queue, current_time, start_time):
        queue_size = queue.get_queue_size()
        update_notif(f"Saving Remaining Data in Queue... {queue_size}")
                
    def cleanup(self, queue, was_streaming, window):
        try:
            # Stop saving thread first to prevent new frames from being added
            self.stop_saving_thread()
            
            # Wait for frames to be saved without timeout
            while not queue.is_empty():
                self._update_save_status(queue, time.time(), time.time())
                time.sleep(0.2)
            
            # Print initial statistics
            logger.info(f"\nRecording Statistics:\n"
                  f"Total frames recorded: {queue.frames_recorded}\n"
                  f"Total frames saved: {queue.frames_saved}\n"
                  f"Frames dropped: {queue.frames_dropped}\n"
                  f"Frames remaining in queue: {queue.img_data_queue.qsize()}")
            
            # Save remaining frames in batches
            batch_size = 100  # Process frames in smaller batches
            frames_to_save = []
            timestamps_to_save = []
            
            while True:
                try:
                    frame, timestamp = queue.get_frame(timeout=1.0)  # Increased timeout for reliability
                    if frame is None:
                        break
                        
                    frames_to_save.append(frame)
                    timestamps_to_save.append(timestamp)
                    
                    # Save batch when it reaches batch_size
                    if len(frames_to_save) >= batch_size:
                        self._save_batch(frames_to_save, timestamps_to_save)
                        queue.frames_saved += len(frames_to_save)
                        frames_to_save = []
                        timestamps_to_save = []
                        
                except Exception as e:
                    logger.error(f"Error during batch saving: {e}")
                    # Don't break here, try to continue saving
                    time.sleep(0.1)
                    continue
            
            # Save any remaining frames
            if frames_to_save:
                self._save_batch(frames_to_save, timestamps_to_save)
                queue.frames_saved += len(frames_to_save)
            
            # Verify all frames were handled
            frames_handled = queue.frames_saved + queue.frames_dropped
            if frames_handled < queue.frames_recorded:
                logger.warning(f"Warning: {queue.frames_recorded - frames_handled} frames were lost during cleanup")
            
            # Show completion message
            update_notif("Acquisition finished and saved to disk.", duration=2000)
            
            # Restart streaming if it was active
            if was_streaming:
                window.start_stream.trigger()
                
        except Exception as e:
            update_notif(f"Error during cleanup: {e}", duration=2000)
            
        finally:
            self._cleanup()
            
    def _save_batch(self, frames, timestamps):
        """Save a batch of frames and timestamps efficiently."""
        if not self.create_hdf5 or not frames:
            return False
            
        try:
            # Initialize datasets if needed
            if self.dataset is None:
                self.dataset = self.create_hdf5.create_dataset(
                    'frames',
                    shape=(0,) + frames[0].shape,
                    maxshape=(None,) + frames[0].shape,
                    dtype=frames[0].dtype,
                    chunks=True
                )
                self.timestamps = self.create_hdf5.create_dataset(
                    'timestamps',
                    shape=(0,),
                    maxshape=(None,),
                    dtype=np.float64
                )
            
            # Calculate new size and resize datasets
            current_size = self.frame_count
            new_size = current_size + len(frames)
            self.dataset.resize(new_size, axis=0)
            self.timestamps.resize(new_size, axis=0)
            
            # Save frames and timestamps in batch
            for i, (frame, timestamp) in enumerate(zip(frames, timestamps)):
                self.dataset[current_size + i] = frame
                self.timestamps[current_size + i] = timestamp
            
            self.frame_count = new_size
            self.create_hdf5.flush()  # Flush after batch save
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving batch: {e}")
            return False
            
    def _cleanup(self):
        """Clean up resources."""
        if self.create_hdf5:
            try:
                self.create_hdf5.flush()
                self.create_hdf5.close()
            except Exception as e:
                logger.error(f"Error closing HDF5 create_hdf5: {e}")
            finally:
                self.create_hdf5 = None
                self.dataset = None
                self.timestamps = None
                self.frame_count = 0 