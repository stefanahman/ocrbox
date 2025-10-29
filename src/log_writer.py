"""Logging system for OCRBox v2."""

import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class LogWriter:
    """Writes comprehensive logs for OCR processing."""
    
    def __init__(
        self,
        logs_dir: str,
        enabled: bool = True
    ):
        """Initialize log writer.
        
        Args:
            logs_dir: Root directory for all logs (flat structure)
            enabled: Whether logging is enabled
        """
        self.logs_dir = Path(logs_dir)
        self.enabled = enabled
        
        # Ensure directory exists
        if self.enabled:
            self.logs_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_log_filename(self, input_filename: str, suffix: str = "") -> str:
        """Generate log filename from input filename.
        
        Args:
            input_filename: Original input file name
            suffix: Optional suffix to add
            
        Returns:
            Log filename (without extension)
        """
        # Remove extension from input filename
        stem = Path(input_filename).stem
        
        # Add suffix if provided
        if suffix:
            return f"{stem}_{suffix}"
        return stem
    
    def write_llm_response_log(
        self,
        input_filename: str,
        raw_response: Dict[str, Any],
        available_tags: List[str]
    ) -> bool:
        """Write LLM response log.
        
        Args:
            input_filename: Original input file name
            raw_response: Raw JSON response from Gemini
            available_tags: List of tags that were available
            
        Returns:
            True if written successfully
        """
        if not self.enabled:
            return False
        
        try:
            base_name = self._get_log_filename(input_filename)
            log_filename = f"{base_name}_llm_response.json"
            log_path = self.logs_dir / log_filename
            
            log_data = {
                "input_file": input_filename,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "raw_response": raw_response,
                "available_tags": available_tags
            }
            
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Wrote LLM response log: {log_filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing LLM response log: {e}")
            return False
    
    def write_processing_log(
        self,
        input_filename: str,
        output_filename: str,
        processing_duration_ms: int,
        status: str,
        selected_tags: List[str],
        confidence_scores: List[float],
        error_message: Optional[str] = None
    ) -> bool:
        """Write processing audit log.
        
        Args:
            input_filename: Original input file name
            output_filename: Generated output file name
            processing_duration_ms: Processing time in milliseconds
            status: Processing status (success, error, skipped)
            selected_tags: Tags that were selected
            confidence_scores: Confidence scores for each tag
            error_message: Optional error message if status is error
            
        Returns:
            True if written successfully
        """
        if not self.enabled:
            return False
        
        try:
            base_name = self._get_log_filename(input_filename)
            log_filename = f"{base_name}_processing.json"
            log_path = self.logs_dir / log_filename
            
            log_data = {
                "input_file": input_filename,
                "output_file": output_filename,
                "processed_at": datetime.utcnow().isoformat() + "Z",
                "processing_duration_ms": processing_duration_ms,
                "status": status,
                "selected_tags": selected_tags,
                "confidence_scores": confidence_scores
            }
            
            if error_message:
                log_data["error_message"] = error_message
            
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Wrote processing log: {log_filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing processing log: {e}")
            return False
    
    def write_tags_snapshot_log(
        self,
        tags_from_file: List[str],
        tags_learned: List[str],
        total_available: List[str]
    ) -> bool:
        """Write tag availability snapshot log.
        
        Args:
            tags_from_file: Tags loaded from tags.txt
            tags_learned: Tags learned from filenames
            total_available: Combined list of available tags
            
        Returns:
            True if written successfully
        """
        if not self.enabled:
            return False
        
        try:
            # Use timestamp as filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            log_filename = f"tags_snapshot_{timestamp}.json"
            log_path = self.logs_dir / log_filename
            
            log_data = {
                "snapshot_at": datetime.utcnow().isoformat() + "Z",
                "tags_from_file": sorted(tags_from_file),
                "tags_learned": sorted(tags_learned),
                "total_available": sorted(total_available)
            }
            
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Wrote tags snapshot log: {log_filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing tags snapshot log: {e}")
            return False
    
    def write_error_log(
        self,
        input_filename: str,
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None,
        retry_attempt: Optional[int] = None
    ) -> bool:
        """Write error log.
        
        Args:
            input_filename: Original input file name
            error_type: Type/class of error
            error_message: Error message
            stack_trace: Optional stack trace
            retry_attempt: Optional retry attempt number
            
        Returns:
            True if written successfully
        """
        if not self.enabled:
            return False
        
        try:
            base_name = self._get_log_filename(input_filename)
            log_filename = f"{base_name}_error.json"
            log_path = self.logs_dir / log_filename
            
            log_data = {
                "input_file": input_filename,
                "error_at": datetime.utcnow().isoformat() + "Z",
                "error_type": error_type,
                "error_message": error_message
            }
            
            if stack_trace:
                log_data["stack_trace"] = stack_trace
            
            if retry_attempt is not None:
                log_data["retry_attempt"] = retry_attempt
            
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Wrote error log: {log_filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing error log: {e}")
            return False
    
    def cleanup_old_logs(self, days_to_keep: int = 30) -> int:
        """Clean up log files older than specified days.
        
        Args:
            days_to_keep: Number of days to keep logs
            
        Returns:
            Number of files deleted
        """
        if not self.enabled:
            return 0
        
        from datetime import timedelta
        import time
        
        cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
        deleted_count = 0
        
        try:
            for log_file in self.logs_dir.glob("*.json"):
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    deleted_count += 1
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old log files")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old logs: {e}")
            return deleted_count

