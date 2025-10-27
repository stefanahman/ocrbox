"""Notification system for OCR processing results."""

import logging
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod
from datetime import datetime

logger = logging.getLogger(__name__)


class NotificationProvider(ABC):
    """Abstract base class for notification providers."""
    
    @abstractmethod
    def send(self, message: str, **kwargs) -> bool:
        """Send a notification message.
        
        Args:
            message: Message text
            **kwargs: Additional provider-specific parameters
            
        Returns:
            True if sent successfully, False otherwise
        """
        pass


class TelegramNotification(NotificationProvider):
    """Telegram notification provider."""
    
    def __init__(self, bot_token: str, chat_id: str):
        """Initialize Telegram notifier.
        
        Args:
            bot_token: Telegram bot token
            chat_id: Target chat ID
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    def send(self, message: str, parse_mode: str = "HTML", **kwargs) -> bool:
        """Send a message via Telegram.
        
        Args:
            message: Message text
            parse_mode: Message parsing mode (HTML or Markdown)
            **kwargs: Additional parameters
            
        Returns:
            True if sent successfully
        """
        try:
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode,
            }
            
            response = requests.post(self.api_url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.debug("Telegram notification sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")
            return False


class EmailNotification(NotificationProvider):
    """Email notification provider."""
    
    def __init__(self, smtp_config: Dict[str, Any]):
        """Initialize email notifier.
        
        Args:
            smtp_config: Dictionary with SMTP configuration:
                - smtp_host: SMTP server host
                - smtp_port: SMTP server port
                - username: SMTP username
                - password: SMTP password
                - from_address: Sender email address
                - to_address: Recipient email address
        """
        self.smtp_host = smtp_config["smtp_host"]
        self.smtp_port = smtp_config["smtp_port"]
        self.username = smtp_config["username"]
        self.password = smtp_config["password"]
        self.from_address = smtp_config["from_address"]
        self.to_address = smtp_config["to_address"]
    
    def send(self, message: str, subject: str = "OCRBox Notification", **kwargs) -> bool:
        """Send an email notification.
        
        Args:
            message: Message text
            subject: Email subject
            **kwargs: Additional parameters
            
        Returns:
            True if sent successfully
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.from_address
            msg["To"] = self.to_address
            msg["Subject"] = subject
            
            msg.attach(MIMEText(message, "plain"))
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.debug("Email notification sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False


class NotificationManager:
    """Manages multiple notification providers."""
    
    def __init__(self):
        """Initialize notification manager."""
        self.providers = []
    
    def add_provider(self, provider: NotificationProvider):
        """Add a notification provider.
        
        Args:
            provider: Notification provider instance
        """
        self.providers.append(provider)
        logger.info(f"Added notification provider: {provider.__class__.__name__}")
    
    def notify_success(
        self,
        filename: str,
        text_excerpt: str,
        output_path: str,
        account: Optional[str] = None
    ) -> None:
        """Send success notification.
        
        Args:
            filename: Original image filename
            text_excerpt: Excerpt of extracted text
            output_path: Path to output text file
            account: Account identifier (for multi-tenant)
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create excerpt (first 200 chars)
        excerpt = text_excerpt[:200]
        if len(text_excerpt) > 200:
            excerpt += "..."
        
        # Build message
        message_parts = [
            "✅ <b>OCR Processing Complete</b>",
            "",
            f"<b>File:</b> {filename}",
            f"<b>Time:</b> {timestamp}",
        ]
        
        if account:
            message_parts.append(f"<b>Account:</b> {account}")
        
        message_parts.extend([
            f"<b>Output:</b> {output_path}",
            f"<b>Characters:</b> {len(text_excerpt)}",
            "",
            "<b>Text Preview:</b>",
            f"<code>{excerpt}</code>",
        ])
        
        message = "\n".join(message_parts)
        
        # Send to all providers
        for provider in self.providers:
            provider.send(message)
    
    def notify_error(
        self,
        filename: str,
        error_message: str,
        account: Optional[str] = None
    ) -> None:
        """Send error notification.
        
        Args:
            filename: Original image filename
            error_message: Error message
            account: Account identifier (for multi-tenant)
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Build message
        message_parts = [
            "❌ <b>OCR Processing Failed</b>",
            "",
            f"<b>File:</b> {filename}",
            f"<b>Time:</b> {timestamp}",
        ]
        
        if account:
            message_parts.append(f"<b>Account:</b> {account}")
        
        message_parts.extend([
            "",
            "<b>Error:</b>",
            f"<code>{error_message}</code>",
        ])
        
        message = "\n".join(message_parts)
        
        # Send to all providers
        for provider in self.providers:
            provider.send(message)
    
    def notify_batch_summary(self, stats: Dict[str, int]) -> None:
        """Send batch processing summary.
        
        Args:
            stats: Dictionary with processing statistics
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        total = sum(stats.values())
        
        message_parts = [
            "📊 <b>OCR Batch Summary</b>",
            "",
            f"<b>Time:</b> {timestamp}",
            f"<b>Total Files:</b> {total}",
            "",
        ]
        
        for status, count in stats.items():
            emoji = "✅" if status == "success" else "❌" if status == "error" else "⏭"
            message_parts.append(f"{emoji} {status.title()}: {count}")
        
        message = "\n".join(message_parts)
        
        # Send to all providers
        for provider in self.providers:
            provider.send(message)

