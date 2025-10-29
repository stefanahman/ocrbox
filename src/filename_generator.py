"""Filename generation for OCRBox v2."""

import logging
import re
import unicodedata
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class FilenameGenerator:
    """Generates sanitized filenames with tag prefixes."""

    def __init__(self, max_title_length: int = 30, max_tags: int = 3):
        """Initialize filename generator.

        Args:
            max_title_length: Maximum characters for title
            max_tags: Maximum number of tags per filename
        """
        self.max_title_length = max_title_length
        self.max_tags = max_tags

    @staticmethod
    def sanitize_tag(tag: str) -> str:
        """Sanitize a tag name for filesystem safety.

        Converts UTF-8 tags (with accents, slashes) to filesystem-safe ASCII.
        Examples:
          - "polarité" → "polarite"
          - "équipe" → "equipe"
          - "statut/en-cours" → "statut-en-cours"
          - "priorité/haute" → "priorite-haute"

        Args:
            tag: Raw tag name (may contain accents, slashes, etc.)

        Returns:
            Sanitized tag (lowercase, ASCII alphanumeric + hyphens)
        """
        # Strip whitespace
        tag = tag.strip()

        # Replace slashes with hyphens (hierarchical tags → flat)
        tag = tag.replace('/', '-')

        # Normalize unicode characters (decompose accents)
        # NFD = Canonical Decomposition (é → e + ´)
        tag = unicodedata.normalize('NFD', tag)

        # Remove accent marks (keep only ASCII)
        tag = tag.encode('ascii', 'ignore').decode('ascii')

        # Lowercase
        tag = tag.lower()

        # Keep only alphanumeric and hyphens
        tag = re.sub(r'[^a-z0-9-]', '', tag)

        # Remove consecutive hyphens
        tag = re.sub(r'-+', '-', tag)

        # Remove leading/trailing hyphens
        tag = tag.strip('-')

        return tag

    def sanitize_title(self, title: str) -> str:
        """Sanitize a title for use in filename.

        Converts UTF-8 titles to filesystem-safe ASCII.

        Args:
            title: Raw title string (may contain accents, special chars)

        Returns:
            Sanitized title (lowercase, hyphens, alphanumeric, max length)
        """
        # Strip whitespace
        title = title.strip()

        # Replace spaces and underscores with hyphens
        title = re.sub(r'[\s_]+', '-', title)

        # Normalize unicode characters (decompose accents)
        title = unicodedata.normalize('NFD', title)

        # Remove accent marks (keep only ASCII)
        title = title.encode('ascii', 'ignore').decode('ascii')

        # Lowercase
        title = title.lower()

        # Keep only alphanumeric and hyphens
        title = re.sub(r'[^a-z0-9-]', '', title)

        # Remove consecutive hyphens
        title = re.sub(r'-+', '-', title)

        # Remove leading/trailing hyphens
        title = title.strip('-')

        # Truncate to max length
        if len(title) > self.max_title_length:
            title = title[:self.max_title_length].rstrip('-')

        # Ensure minimum length
        if len(title) < 5:
            title = "untitled"

        return title

    def generate_filename(
        self,
        tags: List[str],
        title: str,
        output_dir: Optional[str] = None
    ) -> str:
        """Generate filename with tags and title.

        Format: [tag1][tag2][tag3]_title.txt

        Args:
            tags: List of tags (first is primary)
            title: Document title
            output_dir: Optional directory to check for uniqueness

        Returns:
            Generated filename
        """
        # Sanitize and limit tags
        sanitized_tags = []
        for tag in tags[:self.max_tags]:
            clean_tag = self.sanitize_tag(tag)
            if clean_tag:
                sanitized_tags.append(clean_tag)

        # Ensure at least one tag
        if not sanitized_tags:
            sanitized_tags = ['uncategorized']

        # Sanitize title
        clean_title = self.sanitize_title(title)

        # Build tag prefix: [tag1][tag2][tag3]
        tag_prefix = ''.join(f'[{tag}]' for tag in sanitized_tags)

        # Build base filename
        base_filename = f"{tag_prefix}_{clean_title}.txt"

        # Check for uniqueness if output_dir provided
        if output_dir:
            filename = self._ensure_unique_filename(base_filename, output_dir)
        else:
            filename = base_filename

        logger.debug(f"Generated filename: {filename}")
        return filename

    @staticmethod
    def _ensure_unique_filename(filename: str, output_dir: str) -> str:
        """Ensure filename is unique by adding counter if needed.

        Args:
            filename: Base filename
            output_dir: Directory to check

        Returns:
            Unique filename
        """
        output_path = Path(output_dir)

        # If file doesn't exist, we're good
        if not (output_path / filename).exists():
            return filename

        # Extract parts: tags + title + extension
        # Pattern: [tag1][tag2]_title.txt
        match = re.match(r'((?:\[[^\]]+\])+)_([^\.]+)\.txt$', filename)

        if not match:
            # Fallback: just add number before extension
            stem = filename.rsplit('.', 1)[0]
            ext = '.txt'
            tag_prefix = ''
            title = stem
        else:
            tag_prefix = match.group(1)
            title = match.group(2)
            ext = '.txt'

        # Try adding counter
        counter = 1
        while True:
            new_filename = f"{tag_prefix}_{title}-{counter}{ext}"
            if not (output_path / new_filename).exists():
                logger.debug(f"Filename collision, using: {new_filename}")
                return new_filename
            counter += 1

            # Safety limit
            if counter > 1000:
                logger.error("Too many filename collisions, using timestamp")
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                return f"{tag_prefix}_{title}-{timestamp}{ext}"

    @staticmethod
    def extract_tags_from_filename(filename: str) -> List[str]:
        """Extract tags from a filename.

        Args:
            filename: Filename to parse

        Returns:
            List of extracted tags
        """
        # Pattern to match [tag] in filename
        tag_pattern = re.compile(r'\[([a-z0-9-]+)\]')
        tags = tag_pattern.findall(filename)
        return tags

    @staticmethod
    def extract_title_from_filename(filename: str) -> Optional[str]:
        """Extract title from a filename.

        Args:
            filename: Filename to parse

        Returns:
            Extracted title or None
        """
        # Pattern: [tags...]_title.txt
        match = re.match(r'(?:\[[^\]]+\])+_([^\.]+)\.txt$', filename)
        if match:
            return match.group(1)
        return None

