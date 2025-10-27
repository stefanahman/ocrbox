"""Core file processing pipeline for OCR."""

import logging
import hashlib
import shutil
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime

from .gemini_client import GeminiOCRClient
from .storage import ProcessedFilesDB
from .notifications import NotificationManager

logger = logging.getLogger(__name__)

# Supported image extensions
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff", ".tif"}


class FileProcessor:
    """Processes image files through OCR pipeline."""
    
    def __init__(
        self,
        gemini_client: GeminiOCRClient,
        processed_db: ProcessedFilesDB,
        notification_manager: NotificationManager,
        output_dir: str,
        archive_dir: str,
    ):
        """Initialize file processor.
        
        Args:
            gemini_client: Gemini OCR client
            processed_db: Processed files database
            notification_manager: Notification manager
            output_dir: Directory for output text files
            archive_dir: Directory for archived image files
        """
        self.gemini_client = gemini_client
        self.processed_db = processed_db
        self.notification_manager = notification_manager
        self.output_dir = Path(output_dir)
        self.archive_dir = Path(archive_dir)
        
        # Ensure directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def is_image_file(file_path: str) -> bool:
        """Check if a file is a supported image format.
        
        Args:
            file_path: Path to file
            
        Returns:
            True if file is a supported image
        """
        return Path(file_path).suffix.lower() in IMAGE_EXTENSIONS
    
    @staticmethod
    def compute_file_hash(file_path: str) -> str:
        """Compute SHA256 hash of a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            Hexadecimal hash string
        """
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def process_file(
        self,
        file_path: str,
        file_identifier: Optional[str] = None,
        account_id: Optional[str] = None,
        account_email: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """Process a single image file through OCR pipeline.
        
        Args:
            file_path: Path to image file (local filesystem)
            file_identifier: Unique identifier for the file (for idempotency)
            account_id: Dropbox account ID (for multi-tenant tracking)
            account_email: User's email (for notifications)
            
        Returns:
            Tuple of (success: bool, output_path: Optional[str])
        """
        path = Path(file_path)
        
        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return False, None
        
        if not self.is_image_file(file_path):
            logger.warning(f"Skipping non-image file: {file_path}")
            return False, None
        
        # Use file path as identifier if not provided
        if file_identifier is None:
            file_identifier = str(path.absolute())
        
        # Check if already processed (idempotency)
        if self.processed_db.is_processed(file_identifier):
            logger.info(f"File already processed, skipping: {path.name}")
            return False, None
        
        logger.info(f"Processing file: {path.name}")
        
        try:
            # Compute file hash for duplicate detection
            file_hash = self.compute_file_hash(file_path)
            
            # Extract text using Gemini
            extracted_text = self.gemini_client.extract_text_from_file(file_path)
            
            # Generate output filename
            output_filename = path.stem + ".txt"
            output_path = self.output_dir / output_filename
            
            # Handle filename conflicts
            counter = 1
            while output_path.exists():
                output_filename = f"{path.stem}_{counter}.txt"
                output_path = self.output_dir / output_filename
                counter += 1
            
            # Save extracted text
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(extracted_text)
            
            logger.info(f"Saved extracted text to: {output_path}")
            
            # Archive original image
            archive_path = self.archive_dir / path.name
            
            # Handle filename conflicts in archive
            counter = 1
            while archive_path.exists():
                archive_path = self.archive_dir / f"{path.stem}_{counter}{path.suffix}"
                counter += 1
            
            shutil.move(str(path), str(archive_path))
            logger.info(f"Archived original image to: {archive_path}")
            
            # Mark as processed
            self.processed_db.mark_processed(
                file_path=file_identifier,
                status="success",
                account_id=account_id,
                file_hash=file_hash,
                output_path=str(output_path),
            )
            
            # Send success notification
            account_display = account_email or account_id
            self.notification_manager.notify_success(
                filename=path.name,
                text_excerpt=extracted_text,
                output_path=str(output_path),
                account=account_display,
            )
            
            return True, str(output_path)
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error processing file {path.name}: {error_msg}")
            
            # Mark as error
            self.processed_db.mark_processed(
                file_path=file_identifier,
                status="error",
                account_id=account_id,
                error_message=error_msg,
            )
            
            # Send error notification
            account_display = account_email or account_id
            self.notification_manager.notify_error(
                filename=path.name,
                error_message=error_msg,
                account=account_display,
            )
            
            return False, None
    
    def process_bytes(
        self,
        image_data: bytes,
        filename: str,
        file_identifier: str,
        account_id: Optional[str] = None,
        account_email: Optional[str] = None,
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Process image data (from Dropbox or upload) through OCR pipeline.
        
        Args:
            image_data: Image bytes
            filename: Original filename
            file_identifier: Unique identifier for the file (for idempotency)
            account_id: Dropbox account ID (for multi-tenant tracking)
            account_email: User's email (for notifications)
            
        Returns:
            Tuple of (success: bool, output_text: Optional[str], output_path: Optional[str])
        """
        # Check if already processed (idempotency)
        if self.processed_db.is_processed(file_identifier):
            logger.info(f"File already processed, skipping: {filename}")
            return False, None, None
        
        logger.info(f"Processing file: {filename}")
        
        try:
            # Compute file hash for duplicate detection
            file_hash = hashlib.sha256(image_data).hexdigest()
            
            # Extract text using Gemini
            extracted_text = self.gemini_client.extract_text(image_data, filename)
            
            # Generate output filename
            base_name = Path(filename).stem
            output_filename = base_name + ".txt"
            output_path = self.output_dir / output_filename
            
            # Handle filename conflicts
            counter = 1
            while output_path.exists():
                output_filename = f"{base_name}_{counter}.txt"
                output_path = self.output_dir / output_filename
                counter += 1
            
            # Save extracted text
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(extracted_text)
            
            logger.info(f"Saved extracted text to: {output_path}")
            
            # Mark as processed
            self.processed_db.mark_processed(
                file_path=file_identifier,
                status="success",
                account_id=account_id,
                file_hash=file_hash,
                output_path=str(output_path),
            )
            
            # Send success notification
            account_display = account_email or account_id
            self.notification_manager.notify_success(
                filename=filename,
                text_excerpt=extracted_text,
                output_path=str(output_path),
                account=account_display,
            )
            
            return True, extracted_text, str(output_path)
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error processing file {filename}: {error_msg}")
            
            # Mark as error
            self.processed_db.mark_processed(
                file_path=file_identifier,
                status="error",
                account_id=account_id,
                error_message=error_msg,
            )
            
            # Send error notification
            account_display = account_email or account_id
            self.notification_manager.notify_error(
                filename=filename,
                error_message=error_msg,
                account=account_display,
            )
            
            return False, None, None

