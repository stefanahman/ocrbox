"""Configuration management using environment variables."""

import os
import logging
from dataclasses import dataclass
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class Config:
    """Application configuration from environment variables."""

    # Operation mode
    mode: str

    # Gemini API
    gemini_api_key: str
    gemini_model: str

    # Dropbox OAuth (optional for local mode)
    dropbox_app_key: Optional[str]
    dropbox_app_secret: Optional[str]
    dropbox_redirect_uri: Optional[str]
    allowed_accounts: List[str]

    # Notifications
    telegram_enabled: bool
    telegram_bot_token: Optional[str]
    telegram_chat_id: Optional[str]
    email_enabled: bool
    email_config: dict

    # Logging
    log_level: str

    # Processing
    poll_interval: int
    max_retries: int
    retry_delay: int

    # OAuth Server
    oauth_server_port: int
    oauth_server_host: str
    oauth_always_enabled: bool

    # v2 Tag Features
    enable_tags: bool
    enable_auto_summaries: bool
    enable_tag_learning: bool
    primary_tag_confidence_threshold: int
    additional_tag_confidence_threshold: int
    max_summary_length: int
    max_tags_per_file: int
    enable_detailed_logs: bool

    # Paths
    data_dir: str
    tokens_dir: str
    output_dir: str
    archive_dir: str
    watch_dir: str
    processed_db_path: str

    # v2 Paths
    inbox_dir: str
    outbox_dir: str
    logs_dir: str

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        mode = os.getenv("MODE", "local").lower()

        # Validate mode
        if mode not in ["local", "dropbox"]:
            raise ValueError(f"Invalid MODE: {mode}. Must be 'local' or 'dropbox'")

        # Gemini API (required)
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")

        gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

        # Dropbox OAuth (required for dropbox mode)
        dropbox_app_key = os.getenv("DROPBOX_APP_KEY")
        dropbox_app_secret = os.getenv("DROPBOX_APP_SECRET")
        dropbox_redirect_uri = os.getenv("DROPBOX_REDIRECT_URI", "http://localhost:8080/oauth/callback")

        if mode == "dropbox":
            if not dropbox_app_key or not dropbox_app_secret:
                raise ValueError(
                    "DROPBOX_APP_KEY and DROPBOX_APP_SECRET are required for dropbox mode"
                )

        # Allowed accounts
        allowed_accounts_str = os.getenv("ALLOWED_ACCOUNTS", "")
        allowed_accounts = [
            acc.strip() for acc in allowed_accounts_str.split(",") if acc.strip()
        ]

        if mode == "dropbox" and not allowed_accounts:
            logger.warning(
                "No ALLOWED_ACCOUNTS configured. All Dropbox accounts will be accepted. "
                "This is not recommended for production."
            )

        # Telegram notifications
        telegram_enabled = os.getenv("TELEGRAM_ENABLED", "false").lower() == "true"
        telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

        if telegram_enabled and (not telegram_bot_token or not telegram_chat_id):
            logger.warning(
                "Telegram notifications enabled but TELEGRAM_BOT_TOKEN or "
                "TELEGRAM_CHAT_ID not set. Notifications will be disabled."
            )
            telegram_enabled = False

        # Email notifications
        email_enabled = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
        email_config = {
            "smtp_host": os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com"),
            "smtp_port": int(os.getenv("EMAIL_SMTP_PORT", "587")),
            "username": os.getenv("EMAIL_USERNAME"),
            "password": os.getenv("EMAIL_PASSWORD"),
            "from_address": os.getenv("EMAIL_FROM"),
            "to_address": os.getenv("EMAIL_TO"),
        }

        if email_enabled and not all([
            email_config["username"],
            email_config["password"],
            email_config["from_address"],
            email_config["to_address"]
        ]):
            logger.warning(
                "Email notifications enabled but configuration incomplete. "
                "Notifications will be disabled."
            )
            email_enabled = False

        # Logging
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()

        # Processing options
        poll_interval = int(os.getenv("POLL_INTERVAL", "30"))
        max_retries = int(os.getenv("MAX_RETRIES", "3"))
        retry_delay = int(os.getenv("RETRY_DELAY", "2"))

        # OAuth server
        oauth_server_port = int(os.getenv("OAUTH_SERVER_PORT", "8080"))
        oauth_server_host = os.getenv("OAUTH_SERVER_HOST", "0.0.0.0")
        oauth_always_enabled = os.getenv("OAUTH_ALWAYS_ENABLED", "false").lower() == "true"

        # v2 Tag Features
        enable_tags = os.getenv("ENABLE_TAGS", "true").lower() == "true"
        enable_auto_summaries = os.getenv("ENABLE_AUTO_SUMMARIES", "true").lower() == "true"
        enable_tag_learning = os.getenv("ENABLE_TAG_LEARNING", "true").lower() == "true"
        primary_tag_confidence_threshold = int(os.getenv("PRIMARY_TAG_CONFIDENCE_THRESHOLD", "80"))
        additional_tag_confidence_threshold = int(os.getenv("ADDITIONAL_TAG_CONFIDENCE_THRESHOLD", "70"))
        max_summary_length = int(os.getenv("MAX_SUMMARY_LENGTH", "30"))
        max_tags_per_file = int(os.getenv("MAX_TAGS_PER_FILE", "5"))
        enable_detailed_logs = os.getenv("ENABLE_DETAILED_LOGS", "true").lower() == "true"

        # Paths
        data_dir = os.getenv("DATA_DIR", "/app/data")
        tokens_dir = os.path.join(data_dir, "tokens")

        # v2 Paths (new structure)
        inbox_dir = os.path.join(data_dir, "Inbox")
        outbox_dir = os.path.join(data_dir, "Outbox")
        archive_dir = os.path.join(data_dir, "Archive")
        logs_dir = os.path.join(data_dir, "Logs")
        processed_db_path = os.path.join(data_dir, "processed.db")

        # Legacy paths (for backward compatibility during migration)
        output_dir = os.path.join(data_dir, "output")
        watch_dir = os.path.join(data_dir, "watch")

        # Ensure directories exist
        os.makedirs(tokens_dir, exist_ok=True)

        # v2 directories
        os.makedirs(inbox_dir, exist_ok=True)
        os.makedirs(outbox_dir, exist_ok=True)
        os.makedirs(archive_dir, exist_ok=True)
        os.makedirs(logs_dir, exist_ok=True)

        # Legacy directories (for backward compatibility)
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(watch_dir, exist_ok=True)

        return cls(
            mode=mode,
            gemini_api_key=gemini_api_key,
            gemini_model=gemini_model,
            dropbox_app_key=dropbox_app_key,
            dropbox_app_secret=dropbox_app_secret,
            dropbox_redirect_uri=dropbox_redirect_uri,
            allowed_accounts=allowed_accounts,
            telegram_enabled=telegram_enabled,
            telegram_bot_token=telegram_bot_token,
            telegram_chat_id=telegram_chat_id,
            email_enabled=email_enabled,
            email_config=email_config,
            log_level=log_level,
            poll_interval=poll_interval,
            max_retries=max_retries,
            retry_delay=retry_delay,
            oauth_server_port=oauth_server_port,
            oauth_server_host=oauth_server_host,
            oauth_always_enabled=oauth_always_enabled,
            enable_tags=enable_tags,
            enable_auto_summaries=enable_auto_summaries,
            enable_tag_learning=enable_tag_learning,
            primary_tag_confidence_threshold=primary_tag_confidence_threshold,
            additional_tag_confidence_threshold=additional_tag_confidence_threshold,
            max_summary_length=max_summary_length,
            max_tags_per_file=max_tags_per_file,
            enable_detailed_logs=enable_detailed_logs,
            data_dir=data_dir,
            tokens_dir=tokens_dir,
            output_dir=output_dir,
            archive_dir=archive_dir,
            watch_dir=watch_dir,
            processed_db_path=processed_db_path,
            inbox_dir=inbox_dir,
            outbox_dir=outbox_dir,
            logs_dir=logs_dir,
        )

    def setup_logging(self):
        """Configure logging based on log level."""
        logging.basicConfig(
            level=getattr(logging, self.log_level),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

