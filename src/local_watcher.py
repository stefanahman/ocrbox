"""Local folder watcher for development mode."""

import logging
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from .file_processor import FileProcessor

logger = logging.getLogger(__name__)


class ImageFileHandler(FileSystemEventHandler):
    """Handler for new image files in watch directory."""
    
    def __init__(self, file_processor: FileProcessor):
        """Initialize file handler.
        
        Args:
            file_processor: File processor instance
        """
        super().__init__()
        self.file_processor = file_processor
        self.processing = set()  # Track files being processed
    
    def on_created(self, event):
        """Handle file creation events.
        
        Args:
            event: File system event
        """
        if event.is_directory:
            return
        
        file_path = event.src_path
        
        # Check if it's an image file
        if not self.file_processor.is_image_file(file_path):
            return
        
        # Avoid duplicate processing
        if file_path in self.processing:
            return
        
        self.processing.add(file_path)
        
        try:
            # Wait a bit to ensure file is fully written
            time.sleep(0.5)
            
            # Process the file
            logger.info(f"New file detected: {Path(file_path).name}")
            self.file_processor.process_file(file_path)
            
        except Exception as e:
            logger.error(f"Error handling new file {file_path}: {e}")
        
        finally:
            self.processing.discard(file_path)


class LocalFolderWatcher:
    """Watches local folder for new image files."""
    
    def __init__(self, watch_dir: str, file_processor: FileProcessor):
        """Initialize local folder watcher.
        
        Args:
            watch_dir: Directory to watch for new files
            file_processor: File processor instance
        """
        self.watch_dir = Path(watch_dir)
        self.file_processor = file_processor
        self.observer = None
        
        # Ensure watch directory exists
        self.watch_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized local folder watcher for: {self.watch_dir}")
    
    def process_existing_files(self):
        """Process any existing files in the watch directory."""
        logger.info("Checking for existing files in watch directory...")
        
        processed_count = 0
        for file_path in self.watch_dir.iterdir():
            if file_path.is_file() and self.file_processor.is_image_file(str(file_path)):
                try:
                    success, _ = self.file_processor.process_file(str(file_path))
                    if success:
                        processed_count += 1
                except Exception as e:
                    logger.error(f"Error processing existing file {file_path.name}: {e}")
        
        if processed_count > 0:
            logger.info(f"Processed {processed_count} existing file(s)")
        else:
            logger.info("No existing files to process")
    
    def start(self):
        """Start watching the folder."""
        # Process existing files first
        self.process_existing_files()
        
        # Set up file system observer
        event_handler = ImageFileHandler(self.file_processor)
        self.observer = Observer()
        self.observer.schedule(event_handler, str(self.watch_dir), recursive=False)
        self.observer.start()
        
        logger.info(f"Started watching folder: {self.watch_dir}")
        logger.info("Waiting for new image files...")
    
    def stop(self):
        """Stop watching the folder."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info("Stopped local folder watcher")
    
    def run(self):
        """Run the watcher (blocking)."""
        self.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            self.stop()

