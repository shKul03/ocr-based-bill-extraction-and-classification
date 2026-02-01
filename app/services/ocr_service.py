import pytesseract
from PIL import Image
import io
import logging
from app.config import settings

logger = logging.getLogger(__name__)

if settings.TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

class OCRService:
    def extract_text(self, image_bytes: bytes) -> str:
        """Extracts text from image bytes using Tesseract OCR."""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            raise

ocr_service = OCRService()
