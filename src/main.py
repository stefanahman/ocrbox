"""Main entry point for OCRBox service."""

import logging
import signal
import sys
from typing import Optional

from .config import Config
from .storage import TokenStorage, ProcessedFilesDB
from .gemini_client import GeminiOCRClient
from .notifications import NotificationManager, TelegramNotification, EmailNotification
from .file_processor import FileProcessor
from .local_watcher import LocalFolderWatcher
from .dropbox_oauth import OAuthManager
from .dropbox_watcher import DropboxWatcher

logger = logging.getLogger(__name__)


class OCRBoxService:
    """Main OCRBox service orchestrator."""
    
    def __init__(self, config: Config):
        """Initialize OCRBox service.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.watcher = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("=" * 60)
        logger.info("OCRBox - Self-Hosted OCR Service")
        logger.info("=" * 60)
        logger.info(f"Mode: {config.mode}")
        logger.info(f"Gemini Model: {config.gemini_model}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()
        sys.exit(0)
    
    def shutdown(self):
        """Gracefully shutdown the service."""
        if self.watcher:
            if isinstance(self.watcher, LocalFolderWatcher):
                self.watcher.stop()
        logger.info("Service stopped")
    
    def initialize_components(self) -> tuple:
        """Initialize all service components.
        
        Returns:
            Tuple of (gemini_client, processed_db, notification_manager, file_processor)
        """
        # Initialize Gemini client
        logger.info("Initializing Gemini OCR client...")
        gemini_client = GeminiOCRClient(
            api_key=self.config.gemini_api_key,
            model_name=self.config.gemini_model,
            max_retries=self.config.max_retries,
            retry_delay=self.config.retry_delay,
        )
        
        # Initialize processed files database
        logger.info("Initializing processed files database...")
        processed_db = ProcessedFilesDB(self.config.processed_db_path)
        
        # Initialize notification manager
        logger.info("Initializing notification system...")
        notification_manager = NotificationManager()
        
        if self.config.telegram_enabled:
            telegram = TelegramNotification(
                bot_token=self.config.telegram_bot_token,
                chat_id=self.config.telegram_chat_id,
            )
            notification_manager.add_provider(telegram)
            logger.info("✓ Telegram notifications enabled")
        
        if self.config.email_enabled:
            email = EmailNotification(self.config.email_config)
            notification_manager.add_provider(email)
            logger.info("✓ Email notifications enabled")
        
        if not self.config.telegram_enabled and not self.config.email_enabled:
            logger.warning("⚠ No notification providers enabled")
        
        # Initialize file processor
        logger.info("Initializing file processor...")
        file_processor = FileProcessor(
            gemini_client=gemini_client,
            processed_db=processed_db,
            notification_manager=notification_manager,
            output_dir=self.config.output_dir,
            archive_dir=self.config.archive_dir,
        )
        
        return gemini_client, processed_db, notification_manager, file_processor
    
    def run_local_mode(self):
        """Run in local development mode."""
        logger.info("=" * 60)
        logger.info("Starting LOCAL MODE")
        logger.info("=" * 60)
        logger.info(f"Watch directory: {self.config.watch_dir}")
        logger.info(f"Output directory: {self.config.output_dir}")
        logger.info(f"Archive directory: {self.config.archive_dir}")
        logger.info("")
        
        # Initialize components
        _, _, _, file_processor = self.initialize_components()
        
        # Create and run local watcher
        self.watcher = LocalFolderWatcher(
            watch_dir=self.config.watch_dir,
            file_processor=file_processor,
        )
        
        logger.info("Ready to process images! Add files to the watch directory.")
        logger.info("Press Ctrl+C to stop.")
        logger.info("")
        
        self.watcher.run()
    
    def run_dropbox_mode(self):
        """Run in Dropbox mode."""
        logger.info("=" * 60)
        logger.info("Starting DROPBOX MODE")
        logger.info("=" * 60)
        
        # Validate Dropbox configuration
        if not self.config.dropbox_app_key or not self.config.dropbox_app_secret:
            logger.error("Dropbox credentials not configured!")
            logger.error("Please set DROPBOX_APP_KEY and DROPBOX_APP_SECRET environment variables.")
            sys.exit(1)
        
        # Initialize components
        _, _, _, file_processor = self.initialize_components()
        
        # Initialize token storage
        logger.info("Initializing token storage...")
        token_storage = TokenStorage(self.config.tokens_dir)
        
        # Initialize OAuth manager
        oauth_manager = OAuthManager(
            app_key=self.config.dropbox_app_key,
            app_secret=self.config.dropbox_app_secret,
            redirect_uri=self.config.dropbox_redirect_uri,
            token_storage=token_storage,
            allowed_accounts=self.config.allowed_accounts,
        )
        
        # Check for existing authorized accounts
        accounts = token_storage.list_accounts()
        
        if not accounts:
            logger.info("")
            logger.info("=" * 60)
            logger.info("No authorized accounts found")
            logger.info("=" * 60)
            logger.info("Starting OAuth authorization server...")
            logger.info("")
            
            # Run OAuth server to get authorization
            oauth_manager.run_authorization_server(
                host=self.config.oauth_server_host,
                port=self.config.oauth_server_port,
            )
            
            # Check if authorization was successful
            accounts = token_storage.list_accounts()
            if not accounts:
                logger.error("No accounts were authorized. Exiting.")
                sys.exit(1)
            
            logger.info("")
            logger.info(f"✓ Successfully authorized {len(accounts)} account(s)")
            logger.info("Restarting in watcher mode...")
            logger.info("")
        
        # Display authorized accounts
        logger.info(f"Authorized accounts: {len(accounts)}")
        for account_id in accounts:
            token_data = token_storage.load_token(account_id)
            email = token_data.get("account_email", "unknown") if token_data else "unknown"
            logger.info(f"  - {email} ({account_id})")
        
        logger.info("")
        logger.info(f"Output directory: {self.config.output_dir}")
        logger.info(f"Archive directory: {self.config.archive_dir}")
        logger.info(f"Poll interval: {self.config.poll_interval}s")
        logger.info("")
        
        # Create and run Dropbox watcher
        self.watcher = DropboxWatcher(
            token_storage=token_storage,
            file_processor=file_processor,
            oauth_manager=oauth_manager,
            poll_interval=self.config.poll_interval,
        )
        
        logger.info("Ready to process images from Dropbox!")
        logger.info("Press Ctrl+C to stop.")
        logger.info("")
        
        self.watcher.run()
    
    def run(self):
        """Run the service based on configured mode."""
        try:
            if self.config.mode == "local":
                self.run_local_mode()
            elif self.config.mode == "dropbox":
                self.run_dropbox_mode()
            else:
                logger.error(f"Invalid mode: {self.config.mode}")
                sys.exit(1)
        
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
            self.shutdown()
        
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
            self.shutdown()
            sys.exit(1)


def main():
    """Main entry point."""
    try:
        # Load configuration
        config = Config.from_env()
        
        # Setup logging
        config.setup_logging()
        
        # Create and run service
        service = OCRBoxService(config)
        service.run()
    
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

