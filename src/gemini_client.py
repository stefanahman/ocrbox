"""Gemini API client for OCR processing."""

import logging
import time
import json
from typing import Optional, Dict, Any, List
from pathlib import Path
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from PIL import Image
import io

logger = logging.getLogger(__name__)


class GeminiOCRClient:
    """Client for Gemini API OCR operations."""

    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash", max_retries: int = 3, retry_delay: int = 2):
        """Initialize Gemini client.

        Args:
            api_key: Gemini API key
            model_name: Model to use (gemini-1.5-flash or gemini-1.5-pro)
            max_retries: Maximum number of retry attempts
            retry_delay: Initial retry delay in seconds
        """
        self.api_key = api_key
        self.model_name = model_name
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Configure API
        genai.configure(api_key=api_key)

        # Initialize model
        self.model = genai.GenerativeModel(model_name)

        # Safety settings - be permissive for OCR content
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        logger.info(f"Initialized Gemini client with model: {model_name}")

    def extract_text_structured(
        self,
        image_data: bytes,
        available_tags: List[str],
        filename: str = "image"
    ) -> Dict[str, Any]:
        """Extract text with structured output (tags, summary, confidence).

        Args:
            image_data: Image bytes
            available_tags: List of available tags for categorization
            filename: Original filename (for logging)

        Returns:
            Dictionary with text, summary, and tags array

        Raises:
            Exception: If OCR fails after all retries
        """
        attempt = 0
        last_error = None

        while attempt < self.max_retries:
            try:
                # Load image
                image = Image.open(io.BytesIO(image_data))

                # Build prompt with available tags
                tags_str = ", ".join(available_tags)

                prompt = f"""Extract text from this image and analyze its content. Focus ONLY on the MAIN SUBJECT/ACTOR of the image.

MAIN ACTOR FOCUS:
Focus on extracting text from the PRIMARY SUBJECT of the image. Ignore:
- Background elements, UI chrome, browser toolbars, app navigation
- Decorative text, watermarks, timestamps
- Surrounding interface elements not part of the main content

Examples of MAIN ACTORS to focus on:
- Receipt: Extract only the receipt details (items, prices, totals, store name, date) - ignore surrounding counter, hands, or background
- Instagram screenshot: Extract only the post caption and comments INSIDE the post - ignore app UI, buttons, navigation bars
- Business card: Extract only the card's printed text - ignore background surface
- Menu: Extract only menu items, descriptions, and prices - ignore table, place settings, or surroundings
- Invoice/Bill: Extract only the document text - ignore email headers or forwarding information
- Handwritten note: Extract only the note's content - ignore notebook edges, desk surface
- Product label: Extract only the label text - ignore packaging or shelf
- Sign/Poster: Extract only the sign's text - ignore wall, frame, or mounting
- Letter/Document: Extract only the document content - ignore envelope, folder, or desk
- Whiteboard/Presentation slide: Extract only the written/projected content - ignore frame, projector edges

CRITICAL: Only extract text that is actually visible in the main subject. Do NOT add explanatory text, commentary, or text not present.

Return a JSON response with:

1. "text": The EXACT text from the main subject, formatted in markdown:
   - Use ## for section headers (only if headers exist in image)
   - Use * or - for bullet lists (only if lists exist in image)
   - Use 1. 2. 3. for numbered lists (only if numbered lists exist in image)
   - Create logical paragraph breaks where appropriate
   - Do NOT preserve visual layout or column spacing
   - Do NOT add any introductory text like "Here is the text:" or similar
   - ONLY include text from the main subject/actor

2. "summary": A brief, descriptive summary (5-30 characters) that captures the essence of the content

3. "tags": Select the 2-5 most appropriate tags from this list: [{tags_str}]

   HIERARCHICAL TAGS: Tags with slashes (/) represent hierarchies or categories.
   Examples:
   - "statut/en-cours" means status: in-progress
   - "priorité/haute" means priority: high
   - "revue/mensuelle" means review: monthly

   Use hierarchical tags to provide specific categorization. You can use accented characters.

   Return as array with confidence scores:
   [
     {{"name": "tag_name", "confidence": 0-100, "primary": true/false}}
   ]

   Rules:
   - Mark ONE tag as primary (highest confidence, first in array)
   - Primary tag confidence must be ≥ 80%
   - Additional tags confidence must be ≥ 70%
   - Return 2-5 tags maximum
   - Prefer hierarchical tags (with /) when they fit the content
   - Preserve accents and UTF-8 characters in tag names
   - If no tag meets primary threshold, use "uncategorized" as primary

If no text is found, return {{"text": "No text detected", "summary": "Empty", "tags": [{{"name": "uncategorized", "confidence": 100, "primary": true}}]}}

Return ONLY valid JSON, no other text."""

                # Generate content
                logger.debug(f"Sending structured OCR request for {filename} (attempt {attempt + 1}/{self.max_retries})")
                response = self.model.generate_content(
                    [prompt, image],
                    safety_settings=self.safety_settings
                )

                # Log token usage if available
                if hasattr(response, 'usage_metadata') and response.usage_metadata:
                    usage = response.usage_metadata
                    prompt_tokens = getattr(usage, 'prompt_token_count', 0)
                    candidate_tokens = getattr(usage, 'candidates_token_count', 0)
                    total_tokens = getattr(usage, 'total_token_count', 0)

                    # Gemini 1.5 Flash context window: 1,048,576 tokens
                    # Gemini 1.5 Pro context window: 2,097,152 tokens
                    context_window = 1048576 if '1.5-flash' in self.model_name else 2097152
                    remaining_tokens = context_window - total_tokens
                    usage_percent = (total_tokens / context_window) * 100

                    logger.info(
                        f"Token usage for {filename}: "
                        f"prompt={prompt_tokens}, response={candidate_tokens}, total={total_tokens} "
                        f"({usage_percent:.2f}% of context window, {remaining_tokens:,} tokens remaining)"
                    )

                # Extract and parse JSON from response
                if response.text:
                    result = self._parse_structured_response(response.text, available_tags)
                    logger.info(f"Successfully extracted structured data from {filename}")
                    return result
                else:
                    logger.warning(f"Empty response from Gemini for {filename}")
                    return self._fallback_response()

            except Exception as e:
                last_error = e
                attempt += 1

                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** (attempt - 1))
                    logger.warning(
                        f"Structured OCR attempt {attempt} failed for {filename}: {e}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"All structured OCR attempts failed for {filename}: {e}")

        # All retries exhausted
        raise Exception(f"Failed to extract text after {self.max_retries} attempts: {last_error}")

    def _parse_structured_response(self, response_text: str, available_tags: List[str]) -> Dict[str, Any]:
        """Parse and validate structured JSON response from Gemini.

        Args:
            response_text: Raw text response from Gemini
            available_tags: List of available tags for validation

        Returns:
            Validated structured response
        """
        try:
            # Try to find JSON in the response (sometimes LLM adds markdown code blocks)
            json_str = response_text.strip()

            # Remove markdown code blocks if present
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.startswith("```"):
                json_str = json_str[3:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]

            json_str = json_str.strip()

            # Parse JSON
            data = json.loads(json_str)

            # Validate required fields
            if "text" not in data or "summary" not in data or "tags" not in data:
                logger.warning("Missing required fields in response, using fallback")
                return self._fallback_response(data.get("text", ""))

            # Validate and normalize tags
            if not isinstance(data["tags"], list) or len(data["tags"]) == 0:
                logger.warning("Invalid tags array, using uncategorized")
                data["tags"] = [{"name": "uncategorized", "confidence": 100, "primary": True}]

            # Ensure at least one primary tag
            has_primary = any(tag.get("primary", False) for tag in data["tags"])
            if not has_primary and len(data["tags"]) > 0:
                data["tags"][0]["primary"] = True

            # Validate tag names are in available tags
            validated_tags = []
            for tag in data["tags"]:
                tag_name = tag.get("name", "").lower()
                if tag_name in available_tags or tag_name == "uncategorized":
                    validated_tags.append(tag)
                else:
                    logger.debug(f"Tag '{tag_name}' not in available tags, skipping")

            if not validated_tags:
                validated_tags = [{"name": "uncategorized", "confidence": 100, "primary": True}]

            data["tags"] = validated_tags

            return data

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            # Try to extract text anyway
            return self._fallback_response(response_text)

        except Exception as e:
            logger.error(f"Error parsing structured response: {e}")
            return self._fallback_response()

    @staticmethod
    def _fallback_response(text: str = "No text detected") -> Dict[str, Any]:
        """Generate fallback response when structured parsing fails.

        Args:
            text: Extracted text (if any)

        Returns:
            Fallback structured response
        """
        return {
            "text": text,
            "summary": "Untitled",
            "tags": [{"name": "uncategorized", "confidence": 100, "primary": True}]
        }

    def extract_text(self, image_data: bytes, filename: str = "image") -> str:
        """Extract text from an image using Gemini OCR.

        Args:
            image_data: Image bytes
            filename: Original filename (for logging)

        Returns:
            Extracted text

        Raises:
            Exception: If OCR fails after all retries
        """
        attempt = 0
        last_error = None

        while attempt < self.max_retries:
            try:
                # Load image
                image = Image.open(io.BytesIO(image_data))

                # Create prompt for OCR
                prompt = (
                    "Extract all text from this image. "
                    "Preserve the layout and formatting as much as possible. "
                    "If there is no text in the image, respond with 'No text found.'"
                )

                # Generate content
                logger.debug(f"Sending OCR request for {filename} (attempt {attempt + 1}/{self.max_retries})")
                response = self.model.generate_content(
                    [prompt, image],
                    safety_settings=self.safety_settings
                )

                # Extract text from response
                if response.text:
                    text = response.text.strip()
                    logger.info(f"Successfully extracted text from {filename} ({len(text)} characters)")
                    return text
                else:
                    logger.warning(f"Empty response from Gemini for {filename}")
                    return "No text found."

            except Exception as e:
                last_error = e
                attempt += 1

                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                    logger.warning(
                        f"OCR attempt {attempt} failed for {filename}: {e}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"All OCR attempts failed for {filename}: {e}")

        # All retries exhausted
        raise Exception(f"Failed to extract text after {self.max_retries} attempts: {last_error}")

    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text from an image file.

        Args:
            file_path: Path to image file

        Returns:
            Extracted text
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {file_path}")

        # Read file
        with open(file_path, "rb") as f:
            image_data = f.read()

        return self.extract_text(image_data, path.name)

