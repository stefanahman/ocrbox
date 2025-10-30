"""Core file processing pipeline for OCRBox v2."""

import logging
import hashlib
import time
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
from datetime import datetime
import traceback

from .gemini_client import GeminiOCRClient
from .storage import ProcessedFilesDB
from .notifications import NotificationManager
from .tag_manager import TagManager
from .filename_generator import FilenameGenerator
from .log_writer import LogWriter

logger = logging.getLogger(__name__)

# Supported image extensions
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff", ".tif"}


class FileProcessor:
    """Processes image files through v2 OCR pipeline with tags and structured output."""

    def __init__(
        self,
        gemini_client: GeminiOCRClient,
        processed_db: ProcessedFilesDB,
        notification_manager: NotificationManager,
        config,  # Config object with all settings
    ):
        """Initialize file processor.

        Args:
            gemini_client: Gemini OCR client
            processed_db: Processed files database
            notification_manager: Notification manager
            config: Config object with all settings
        """
        self.gemini_client = gemini_client
        self.processed_db = processed_db
        self.notification_manager = notification_manager

        # Initialize components from config
        self.tag_manager = TagManager(outbox_dir=config.outbox_dir)
        self.filename_generator = FilenameGenerator(
            max_summary_length=config.max_summary_length,
            max_tags=config.max_tags_per_file
        )
        self.log_writer = LogWriter(
            logs_dir=config.logs_dir,
            enabled=config.enable_detailed_logs
        )

        self.outbox_dir = Path(config.outbox_dir)
        self.archive_dir = Path(config.archive_dir)
        self.primary_tag_threshold = config.primary_tag_confidence_threshold
        self.additional_tag_threshold = config.additional_tag_confidence_threshold

        # Ensure directories exist
        self.outbox_dir.mkdir(parents=True, exist_ok=True)
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

    def process_bytes(
        self,
        image_data: bytes,
        filename: str,
        file_identifier: str,
        account_id: Optional[str] = None,
        account_email: Optional[str] = None,
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Process image data through v2 OCR pipeline with tags.

        Args:
            image_data: Image bytes
            filename: Original filename
            file_identifier: Unique identifier for idempotency
            account_id: Dropbox account ID
            account_email: User's email

        Returns:
            Tuple of (success, output_text, output_filename)
        """
        start_time = time.time()

        # Check if already processed
        if self.processed_db.is_processed(file_identifier):
            logger.info(f"File already processed, skipping: {filename}")
            return False, None, None

        logger.info(f"Processing file: {filename}")

        try:
            # 1. Get available tags
            available_tags = self.tag_manager.get_available_tags()

            # 2. Call Gemini for structured OCR
            structured_result = self.gemini_client.extract_text_structured(
                image_data=image_data,
                available_tags=available_tags,
                filename=filename
            )

            # 3. Write LLM response log
            self.log_writer.write_llm_response_log(
                input_filename=filename,
                raw_response=structured_result,
                available_tags=available_tags
            )

            # Extract components
            text = structured_result["text"]
            summary = structured_result["summary"]
            tags_data = structured_result["tags"]

            # 4. Filter tags by confidence thresholds
            filtered_tags = self._filter_tags_by_confidence(tags_data)

            # 5. Generate output filename
            tag_names = [tag["name"] for tag in filtered_tags]
            output_filename = self.filename_generator.generate_filename(
                tags=tag_names,
                summary=summary,
                output_dir=str(self.outbox_dir)
            )

            # 6. Save text file
            output_path = self.outbox_dir / output_filename
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(text)

            logger.info(f"Saved text to: {output_path}")

            # 7. Calculate processing duration
            duration_ms = int((time.time() - start_time) * 1000)

            # 8. Write processing log
            confidence_scores = [tag["confidence"] for tag in filtered_tags]
            self.log_writer.write_processing_log(
                input_filename=filename,
                output_filename=output_filename,
                processing_duration_ms=duration_ms,
                status="success",
                selected_tags=tag_names,
                confidence_scores=confidence_scores
            )

            # 9. Mark as processed in database
            file_hash = hashlib.sha256(image_data).hexdigest()
            self.processed_db.mark_processed(
                file_path=file_identifier,
                status="success",
                account_id=account_id,
                file_hash=file_hash,
                output_path=str(output_path)
            )

            # 10. Send notification
            self.notification_manager.notify_success_v2(
                filename=filename,
                output_filename=output_filename,
                tags=filtered_tags,
                text_excerpt=text,
                output_path=str(output_path),
                account=account_email or account_id
            )

            return True, text, output_filename

        except Exception as e:
            error_msg = str(e)
            stack_trace = traceback.format_exc()
            logger.error(f"Error processing file {filename}: {error_msg}")

            # Write error log
            self.log_writer.write_error_log(
                input_filename=filename,
                error_type=type(e).__name__,
                error_message=error_msg,
                stack_trace=stack_trace
            )

            # Mark as error in database
            self.processed_db.mark_processed(
                file_path=file_identifier,
                status="error",
                account_id=account_id,
                error_message=error_msg
            )

            # Send error notification
            self.notification_manager.notify_error(
                filename=filename,
                error_message=error_msg,
                account=account_email or account_id
            )

            return False, None, None

    def _filter_tags_by_confidence(self, tags_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter tags based on confidence thresholds.

        Args:
            tags_data: List of tag dictionaries with confidence scores

        Returns:
            Filtered list of tags meeting thresholds
        """
        filtered = []

        for tag in tags_data:
            is_primary = tag.get("primary", False)
            confidence = tag.get("confidence", 0)

            # Primary tag must meet primary threshold
            if is_primary and confidence >= self.primary_tag_threshold:
                filtered.append(tag)
            # Additional tags must meet additional threshold
            elif not is_primary and confidence >= self.additional_tag_threshold:
                filtered.append(tag)
            else:
                logger.debug(
                    f"Tag '{tag.get('name')}' filtered out: "
                    f"confidence {confidence} below threshold"
                )

        # Ensure at least one tag (uncategorized fallback)
        if not filtered:
            logger.warning("No tags met threshold, using uncategorized")
            filtered = [{"name": "uncategorized", "confidence": 100, "primary": True}]

        return filtered

