"""Gemini API client for OCR processing."""

import logging
import time
from typing import Optional
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

