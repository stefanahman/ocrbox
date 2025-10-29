"""Tag management system for OCRBox v2."""

import logging
import os
import re
from pathlib import Path
from typing import List, Set, Optional

logger = logging.getLogger(__name__)

# Default tags to create in tags.txt if file doesn't exist
DEFAULT_TAGS = [
    "receipts",
    "documents",
    "invoices",
    "notes",
    "screenshots",
    "personal",
    "work",
    "travel",
    "health",
    "finance",
]


class TagManager:
    """Manages tags from tags.txt and learns from existing filenames."""
    
    def __init__(self, outbox_dir: str, tags_file_path: Optional[str] = None, enable_learning: bool = True):
        """Initialize tag manager.
        
        Args:
            outbox_dir: Path to outbox directory
            tags_file_path: Path to tags.txt file (defaults to parent of outbox / tags.txt)
            enable_learning: Whether to learn tags from existing filenames
        """
        self.outbox_dir = Path(outbox_dir)
        self.enable_learning = enable_learning
        
        # tags.txt in root directory (parent of Outbox)
        if tags_file_path:
            self.tags_file = Path(tags_file_path)
        else:
            self.tags_file = self.outbox_dir.parent / "tags.txt"
        
        # Ensure outbox directory exists
        self.outbox_dir.mkdir(parents=True, exist_ok=True)
        
        # Create default tags.txt if it doesn't exist
        if not self.tags_file.exists():
            self._create_default_tags_file()
    
    def _create_default_tags_file(self):
        """Create tags.txt with default tags."""
        try:
            with open(self.tags_file, "w", encoding="utf-8") as f:
                f.write("\n".join(DEFAULT_TAGS))
            logger.info(f"Created default tags.txt with {len(DEFAULT_TAGS)} tags")
        except Exception as e:
            logger.error(f"Error creating tags.txt: {e}")
    
    def _load_tags_from_file(self) -> Set[str]:
        """Load tags from tags.txt file.
        
        Returns:
            Set of tag names
        """
        tags = set()
        
        if not self.tags_file.exists():
            logger.warning(f"tags.txt not found at {self.tags_file}")
            return tags
        
        try:
            with open(self.tags_file, "r", encoding="utf-8") as f:
                for line in f:
                    tag = line.strip().lower()
                    if tag and self._is_valid_tag(tag):
                        tags.add(tag)
            
            logger.info(f"Loaded {len(tags)} tags from tags.txt")
            return tags
            
        except Exception as e:
            logger.error(f"Error loading tags.txt: {e}")
            return tags
    
    def _learn_tags_from_filenames(self) -> Set[str]:
        """Learn tags from existing filenames in outbox.
        
        Scans for patterns like: [tag1][tag2]_title.txt
        
        Returns:
            Set of learned tag names
        """
        if not self.enable_learning:
            return set()
        
        learned_tags = set()
        
        # Pattern to match [tag] in filenames
        tag_pattern = re.compile(r'\[([a-z0-9-]+)\]')
        
        try:
            for file_path in self.outbox_dir.glob("*.txt"):
                # Skip tags.txt itself
                if file_path.name == "tags.txt":
                    continue
                
                # Extract tags from filename
                matches = tag_pattern.findall(file_path.name)
                for tag in matches:
                    if self._is_valid_tag(tag):
                        learned_tags.add(tag)
            
            if learned_tags:
                logger.info(f"Learned {len(learned_tags)} tags from existing filenames: {sorted(learned_tags)}")
            else:
                logger.debug("No tags learned from existing filenames")
            
            return learned_tags
            
        except Exception as e:
            logger.error(f"Error learning tags from filenames: {e}")
            return learned_tags
    
    @staticmethod
    def _is_valid_tag(tag: str) -> bool:
        """Validate tag name.
        
        Args:
            tag: Tag name to validate
            
        Returns:
            True if valid
        """
        # Must be alphanumeric + hyphens, lowercase, 2-20 chars
        if not tag or len(tag) < 2 or len(tag) > 20:
            return False
        
        if not re.match(r'^[a-z0-9-]+$', tag):
            return False
        
        # Reserved names
        if tag in ['uncategorized', 'logs', 'archive', 'inbox', 'outbox']:
            return False
        
        return True
    
    def get_available_tags(self) -> List[str]:
        """Get all available tags (from file + learned).
        
        Returns:
            Sorted list of unique tag names
        """
        # Load from tags.txt
        file_tags = self._load_tags_from_file()
        
        # Learn from existing filenames
        learned_tags = self._learn_tags_from_filenames()
        
        # Combine and sort
        all_tags = file_tags.union(learned_tags)
        
        # Always include 'uncategorized' as fallback
        all_tags.add('uncategorized')
        
        sorted_tags = sorted(all_tags)
        
        logger.info(f"Total available tags: {len(sorted_tags)}")
        logger.debug(f"Tags: {sorted_tags}")
        
        return sorted_tags
    
    def add_tag_to_file(self, tag: str) -> bool:
        """Add a new tag to tags.txt.
        
        Args:
            tag: Tag name to add
            
        Returns:
            True if added successfully
        """
        tag = tag.strip().lower()
        
        if not self._is_valid_tag(tag):
            logger.warning(f"Invalid tag name: {tag}")
            return False
        
        # Check if already exists
        existing_tags = self._load_tags_from_file()
        if tag in existing_tags:
            logger.debug(f"Tag already exists: {tag}")
            return True
        
        try:
            # Append to file
            with open(self.tags_file, "a", encoding="utf-8") as f:
                f.write(f"\n{tag}")
            
            logger.info(f"Added new tag to tags.txt: {tag}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding tag to tags.txt: {e}")
            return False

