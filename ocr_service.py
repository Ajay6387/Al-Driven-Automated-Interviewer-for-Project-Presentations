import pytesseract
from PIL import Image
import base64
import io
import cv2
import numpy as np
from typing import Dict, Any
import logging
import config

logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)

class OCRService:
    """Service for extracting text from screen captures using OCR"""
    
    def __init__(self):
        self.ocr_lang = config.OCR_LANG
        self.ocr_config = config.OCR_CONFIG
        
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results"""
        # Convert PIL Image to OpenCV format
        img_array = np.array(image)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Apply thresholding to get better contrast
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(thresh)
        
        # Convert back to PIL Image
        return Image.fromarray(denoised)
    
    def detect_content_type(self, text: str, image: Image.Image) -> str:
        """Detect the type of content in the screen capture"""
        text_lower = text.lower()
        
        # Check for code indicators
        code_indicators = ['def ', 'class ', 'function', 'import ', 'const ', 'var ', 
                          'return', '{', '}', '()', '=>', 'public class', 'private']
        if any(indicator in text_lower for indicator in code_indicators):
            return "code"
        
        # Check for slide indicators
        slide_indicators = ['agenda', 'outline', 'introduction', 'conclusion', 
                           'overview', 'objectives', 'thank you']
        if any(indicator in text_lower for indicator in slide_indicators):
            return "slide"
        
        # Check for diagram indicators (based on text/whitespace ratio)
        if len(text.strip()) < 100 and image.size[0] > 800:
            return "diagram"
        
        return "other"
    
    def extract_code_snippets(self, text: str) -> list:
        """Extract identifiable code snippets from text"""
        lines = text.split('\n')
        snippets = []
        current_snippet = []
        in_code_block = False
        
        for line in lines:
            stripped = line.strip()
            # Simple heuristic: lines with code-like patterns
            if any(pattern in stripped for pattern in ['def ', 'class ', '()', '{', '}']):
                in_code_block = True
                current_snippet.append(line)
            elif in_code_block:
                if stripped and not stripped.startswith('#'):
                    current_snippet.append(line)
                else:
                    if current_snippet:
                        snippets.append('\n'.join(current_snippet))
                        current_snippet = []
                    in_code_block = False
        
        if current_snippet:
            snippets.append('\n'.join(current_snippet))
        
        return snippets
    
    def analyze_screen(self, image_base64: str) -> Dict[str, Any]:
        """
        Main method to analyze screen capture
        
        Args:
            image_base64: Base64 encoded image string
            
        Returns:
            Dictionary with extracted text, content type, and metadata
        """
        try:
            # Decode base64 image
            image_data = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_data))
            
            # Preprocess image
            processed_image = self.preprocess_image(image)
            
            # Extract text using OCR
            extracted_text = pytesseract.image_to_string(
                processed_image,
                lang=self.ocr_lang,
                config=self.ocr_config
            )
            
            # Detect content type
            content_type = self.detect_content_type(extracted_text, image)
            
            # Extract additional metadata based on content type
            metadata = {
                "image_dimensions": image.size,
                "text_length": len(extracted_text),
                "line_count": len(extracted_text.split('\n'))
            }
            
            if content_type == "code":
                code_snippets = self.extract_code_snippets(extracted_text)
                metadata["code_snippets"] = code_snippets
                metadata["code_snippet_count"] = len(code_snippets)
            
            logger.info(f"Screen analyzed: {content_type}, extracted {len(extracted_text)} characters")
            
            return {
                "extracted_text": extracted_text,
                "content_type": content_type,
                "metadata": metadata,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"OCR analysis failed: {str(e)}")
            return {
                "extracted_text": "",
                "content_type": "error",
                "metadata": {"error": str(e)},
                "success": False
            }
    
    def extract_key_terms(self, text: str) -> list:
        """Extract key technical terms from text"""
        # Simple keyword extraction (in production, use NLP libraries)
        words = text.split()
        # Filter for likely technical terms (capitalized, longer words, etc.)
        key_terms = [
            word for word in words 
            if len(word) > 4 and (word[0].isupper() or '_' in word)
        ]
        return list(set(key_terms))[:10]  # Return top 10 unique terms
