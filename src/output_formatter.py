"""Output formatters for different file formats."""

import logging
from datetime import datetime
from typing import Tuple, List, Dict, Any

logger = logging.getLogger(__name__)


class OutputFormatter:
    """Formats OCR output for different file formats."""

    @staticmethod
    def format_output(
        text: str,
        summary: str,
        tags: List[Dict[str, Any]],
        format_type: str = "plaintext"
    ) -> Tuple[str, str]:
        """Format OCR output based on specified format.

        Args:
            text: Extracted text content (may already be in markdown)
            summary: Brief summary of content
            tags: List of tag dictionaries with name and confidence
            format_type: Output format ("plaintext" or "obsidian")

        Returns:
            Tuple of (formatted_content, file_extension)
        """
        if format_type == "obsidian":
            return OutputFormatter._format_obsidian(text, summary, tags)
        else:
            return OutputFormatter._format_plaintext(text)

    @staticmethod
    def _format_plaintext(text: str) -> Tuple[str, str]:
        """Format as plain text (current format).

        Args:
            text: Raw text content

        Returns:
            Tuple of (text, ".txt")
        """
        return (text, ".txt")

    @staticmethod
    def _format_obsidian(
        text: str,
        summary: str,
        tags: List[Dict[str, Any]]
    ) -> Tuple[str, str]:
        """Format as Obsidian markdown with YAML frontmatter.

        Args:
            text: Markdown text content
            summary: Summary text
            tags: List of tag dictionaries with name and confidence

        Returns:
            Tuple of (formatted_markdown, ".md")
        """
        # Create frontmatter
        frontmatter_lines = ["---"]

        # Add summary
        # Escape quotes in summary for YAML
        escaped_summary = summary.replace('"', '\\"')
        frontmatter_lines.append(f'summary: "{escaped_summary}"')

        # Add tags array (with #ocrbox prepended)
        frontmatter_lines.append("tags:")
        frontmatter_lines.append("  - ocrbox")

        tag_names = [tag["name"] for tag in tags]
        for tag_name in tag_names:
            # Remove any existing # prefix and add it
            clean_tag = tag_name.lstrip('#')
            frontmatter_lines.append(f"  - {clean_tag}")

        # Add confidence scores if available
        if tags and all("confidence" in tag for tag in tags):
            frontmatter_lines.append("confidence:")
            for tag in tags:
                tag_name = tag["name"]
                confidence = tag["confidence"]
                frontmatter_lines.append(f"  {tag_name}: {confidence}")

        # Add creation timestamp
        created_timestamp = datetime.now().isoformat()
        frontmatter_lines.append(f"created: {created_timestamp}")

        # Close frontmatter
        frontmatter_lines.append("---")

        # Combine frontmatter and content
        frontmatter = "\n".join(frontmatter_lines)
        formatted_content = f"{frontmatter}\n\n{text}"

        logger.debug(f"Formatted Obsidian markdown with {len(tags)} tags")

        return (formatted_content, ".md")

