"""Dropbox App Folder watcher for multi-tenant OCR processing."""

import logging
import time
from typing import Dict, Optional, List
import dropbox
from dropbox.exceptions import ApiError, AuthError
from dropbox.files import FileMetadata

from .storage import TokenStorage
from .file_processor import FileProcessor
from .dropbox_oauth import OAuthManager

logger = logging.getLogger(__name__)


class DropboxWatcher:
    """Watches Dropbox App Folders for new files."""
    
    def __init__(
        self,
        token_storage: TokenStorage,
        file_processor: FileProcessor,
        oauth_manager: OAuthManager,
        poll_interval: int = 30,
    ):
        """Initialize Dropbox watcher.
        
        Args:
            token_storage: Token storage instance
            file_processor: File processor instance
            oauth_manager: OAuth manager for token refresh
            poll_interval: Seconds between polling for new files
        """
        self.token_storage = token_storage
        self.file_processor = file_processor
        self.oauth_manager = oauth_manager
        self.poll_interval = poll_interval
        
        # Track cursors for each account (for delta sync)
        self.cursors: Dict[str, Optional[str]] = {}
        
        # Track initialized accounts (to avoid re-creating folders)
        self.initialized_accounts = set()
        
        logger.info("Initialized Dropbox watcher")
    
    def get_dropbox_client(self, account_id: str) -> Optional[dropbox.Dropbox]:
        """Get authenticated Dropbox client for an account.
        
        Args:
            account_id: Dropbox account ID
            
        Returns:
            Dropbox client or None if token invalid
        """
        token_data = self.token_storage.load_token(account_id)
        
        if not token_data:
            logger.error(f"No token found for account: {account_id}")
            return None
        
        try:
            dbx = dropbox.Dropbox(token_data["access_token"])
            # Test the connection
            dbx.users_get_current_account()
            return dbx
            
        except AuthError as e:
            logger.warning(f"Token expired for account {account_id}, attempting refresh...")
            
            # Try to refresh token
            if self.oauth_manager.refresh_token(account_id):
                # Try again with refreshed token
                token_data = self.token_storage.load_token(account_id)
                dbx = dropbox.Dropbox(token_data["access_token"])
                return dbx
            else:
                logger.error(f"Failed to refresh token for account: {account_id}")
                return None
        
        except Exception as e:
            logger.error(f"Error creating Dropbox client for {account_id}: {e}")
            return None
    
    def list_new_files(self, account_id: str) -> List[FileMetadata]:
        """List new files in the App Folder for an account.
        
        Args:
            account_id: Dropbox account ID
            
        Returns:
            List of new file metadata
        """
        dbx = self.get_dropbox_client(account_id)
        
        if not dbx:
            return []
        
        try:
            new_files = []
            cursor = self.cursors.get(account_id)
            
            if cursor:
                # Get changes since last check
                result = dbx.files_list_folder_continue(cursor)
            else:
                # First time - list all files
                result = dbx.files_list_folder("", recursive=True)
            
            # Update cursor for next time
            self.cursors[account_id] = result.cursor
            
            # Collect new image files (excluding processed and output folders)
            for entry in result.entries:
                if isinstance(entry, FileMetadata):
                    # Skip files in processed or output folders
                    if entry.path_lower.startswith('/processed/') or entry.path_lower.startswith('/ocr_output/'):
                        continue
                    if self.file_processor.is_image_file(entry.path_lower):
                        new_files.append(entry)
            
            # Handle pagination
            while result.has_more:
                result = dbx.files_list_folder_continue(result.cursor)
                self.cursors[account_id] = result.cursor
                
                for entry in result.entries:
                    if isinstance(entry, FileMetadata):
                        # Skip files in processed or output folders
                        if entry.path_lower.startswith('/processed/') or entry.path_lower.startswith('/ocr_output/'):
                            continue
                        if self.file_processor.is_image_file(entry.path_lower):
                            new_files.append(entry)
            
            return new_files
            
        except ApiError as e:
            logger.error(f"Dropbox API error for account {account_id}: {e}")
            return []
        
        except Exception as e:
            logger.error(f"Error listing files for account {account_id}: {e}")
            return []
    
    def download_and_process_file(
        self,
        account_id: str,
        account_email: str,
        file_metadata: FileMetadata
    ) -> bool:
        """Download and process a file from Dropbox.
        
        Args:
            account_id: Dropbox account ID
            account_email: User's email
            file_metadata: File metadata from Dropbox
            
        Returns:
            True if processed successfully
        """
        dbx = self.get_dropbox_client(account_id)
        
        if not dbx:
            return False
        
        try:
            # Download file
            logger.info(f"Downloading file from Dropbox: {file_metadata.name}")
            metadata, response = dbx.files_download(file_metadata.path_lower)
            image_data = response.content
            
            # Create unique identifier for idempotency
            file_identifier = f"dropbox:{account_id}:{file_metadata.id}"
            
            # Process file
            success, text, output_path = self.file_processor.process_bytes(
                image_data=image_data,
                filename=file_metadata.name,
                file_identifier=file_identifier,
                account_id=account_id,
                account_email=account_email,
            )
            
            if success and text:
                # Upload the extracted text back to Dropbox
                import os
                text_filename = os.path.basename(output_path)
                self.upload_text_to_dropbox(dbx, text_filename, text)
                
                # Move the processed image to /processed/ folder
                self.move_to_processed(dbx, file_metadata)
            
            return success
            
        except Exception as e:
            logger.error(f"Error downloading/processing file {file_metadata.name}: {e}")
            return False
    
    def upload_text_to_dropbox(
        self,
        dbx: dropbox.Dropbox,
        filename: str,
        text_content: str
    ) -> bool:
        """Upload extracted text back to Dropbox App Folder.
        
        Args:
            dbx: Dropbox client
            filename: Output filename
            text_content: Extracted text
            
        Returns:
            True if uploaded successfully
        """
        try:
            # Upload to /ocr_output/ subfolder in App Folder
            output_path = f"/ocr_output/{filename}"
            
            dbx.files_upload(
                text_content.encode("utf-8"),
                output_path,
                mode=dropbox.files.WriteMode.overwrite,
            )
            
            logger.info(f"Uploaded text file to Dropbox: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error uploading text to Dropbox: {e}")
            return False
    
    def move_to_processed(
        self,
        dbx: dropbox.Dropbox,
        file_metadata: FileMetadata
    ) -> bool:
        """Move processed image to /processed/ folder in Dropbox.
        
        Args:
            dbx: Dropbox client
            file_metadata: Original file metadata
            
        Returns:
            True if moved successfully
        """
        try:
            # Build destination path
            dest_path = f"/processed/{file_metadata.name}"
            
            # Move the file
            dbx.files_move_v2(
                file_metadata.path_lower,
                dest_path,
                autorename=True  # Auto-rename if destination exists
            )
            
            logger.info(f"Moved processed image to: {dest_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error moving file to processed folder: {e}")
            return False
    
    def initialize_folder_structure(self, account_id: str) -> bool:
        """Initialize required folder structure in Dropbox App Folder.
        
        Creates:
        - /ocr_output/ - For extracted text files
        - /processed/ - For processed images
        
        Args:
            account_id: Dropbox account ID
            
        Returns:
            True if initialization successful
        """
        # Skip if already initialized
        if account_id in self.initialized_accounts:
            return True
        
        dbx = self.get_dropbox_client(account_id)
        
        if not dbx:
            return False
        
        folders_to_create = ['/ocr_output', '/processed']
        
        try:
            for folder_path in folders_to_create:
                try:
                    # Try to create the folder
                    dbx.files_create_folder_v2(folder_path)
                    logger.info(f"Created folder: {folder_path}")
                except ApiError as e:
                    # Folder might already exist, which is fine
                    error_str = str(e)
                    if 'conflict' in error_str.lower() or 'already exists' in error_str.lower():
                        logger.debug(f"Folder already exists: {folder_path}")
                    else:
                        logger.warning(f"Could not create folder {folder_path}: {e}")
                        # Don't fail completely, just continue
            
            # Create a README file in the root
            readme_content = """# OCRBox - Automated OCR Processing

This is your OCRBox App Folder. Here's how it works:

📁 **Folder Structure:**
- **Root folder** - Drop your images or screenshots here for processing
- **/ocr_output/** - Extracted text files appear here
- **/processed/** - Original images are moved here after processing

📸 **Usage:**
1. Upload an image (PNG, JPG, GIF, WebP, BMP, TIFF) to this folder
2. OCRBox automatically extracts the text
3. Find the text file in /ocr_output/
4. Original image moves to /processed/

⚙️ **Processing:**
- Automatic detection of new images
- Powered by Google Gemini AI
- Typically completes in 5-10 seconds

💡 **Tips:**
- Supported formats: PNG, JPEG, GIF, WebP, BMP, TIFF
- Files in /processed/ and /ocr_output/ are not re-processed
- Check notifications for processing status

🔒 **Privacy:**
Your files are processed securely. Only image bytes are sent to Google Gemini for OCR.

---
Powered by OCRBox - Self-Hosted OCR Service
"""
            
            try:
                # Upload README (only if it doesn't exist)
                dbx.files_upload(
                    readme_content.encode('utf-8'),
                    '/README.txt',
                    mode=dropbox.files.WriteMode.add,  # Don't overwrite if exists
                )
                logger.info("Created README.txt in App Folder")
            except ApiError as e:
                error_str = str(e)
                if 'conflict' not in error_str.lower():
                    logger.warning(f"Could not create README: {e}")
                else:
                    logger.debug("README.txt already exists")
            
            # Mark as initialized
            self.initialized_accounts.add(account_id)
            
            token_data = self.token_storage.load_token(account_id)
            account_email = token_data.get("account_email", account_id) if token_data else account_id
            logger.info(f"✓ Initialized folder structure for: {account_email}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing folder structure: {e}")
            return False
    
    def process_account(self, account_id: str) -> int:
        """Process all new files for a single account.
        
        Args:
            account_id: Dropbox account ID
            
        Returns:
            Number of files processed
        """
        token_data = self.token_storage.load_token(account_id)
        
        if not token_data:
            logger.warning(f"No token data for account: {account_id}")
            return 0
        
        account_email = token_data.get("account_email", account_id)
        
        # Initialize folder structure on first poll
        if account_id not in self.initialized_accounts:
            self.initialize_folder_structure(account_id)
        
        # List new files
        new_files = self.list_new_files(account_id)
        
        if not new_files:
            return 0
        
        logger.info(f"Found {len(new_files)} new file(s) for {account_email}")
        
        # Process each file
        processed_count = 0
        for file_metadata in new_files:
            try:
                if self.download_and_process_file(account_id, account_email, file_metadata):
                    processed_count += 1
            except Exception as e:
                logger.error(f"Error processing file {file_metadata.name}: {e}")
        
        return processed_count
    
    def poll_once(self) -> int:
        """Poll all accounts once for new files.
        
        Returns:
            Total number of files processed
        """
        accounts = self.token_storage.list_accounts()
        
        if not accounts:
            logger.debug("No authorized accounts to poll")
            return 0
        
        logger.debug(f"Polling {len(accounts)} account(s) for new files...")
        
        total_processed = 0
        for account_id in accounts:
            try:
                count = self.process_account(account_id)
                total_processed += count
            except Exception as e:
                logger.error(f"Error polling account {account_id}: {e}")
        
        return total_processed
    
    def run(self):
        """Run the watcher (blocking)."""
        logger.info(f"Started Dropbox watcher (polling every {self.poll_interval}s)")
        
        # Check for authorized accounts
        accounts = self.token_storage.list_accounts()
        if not accounts:
            logger.warning(
                "No authorized Dropbox accounts found. "
                "Please complete OAuth authorization first."
            )
        else:
            logger.info(f"Monitoring {len(accounts)} authorized account(s)")
        
        try:
            while True:
                self.poll_once()
                time.sleep(self.poll_interval)
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Watcher error: {e}")
            raise

