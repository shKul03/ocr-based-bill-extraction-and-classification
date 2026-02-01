import httpx
import logging
import json
from app.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.LLM_MODEL
        self.client = httpx.Client(base_url=self.base_url, timeout=60.0)

    def _generate(self, prompt: str, json_mode: bool = False) -> str:
        """Helper to call Ollama generate API."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        if json_mode:
            payload["format"] = "json"

        try:
            response = self.client.post("/api/generate", json=payload)
            response.raise_for_status()
            return response.json().get("response", "")
        except httpx.RequestError as e:
            logger.error(f"Ollama API request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise

    def classify_document(self, text: str) -> dict:
        """
        Classifies the document as invoice or expense and identifies category.
        Expected Output: JSON with 'type' and 'category'.
        """
        prompt = f"""
        You are a document classifier. specific instructions to classify document...
        [PLACEHOLDER FOR CLASSIFICATION PROMPT]
        
        Analyze the following text extracted from a bill/receipt:
        {text}
        
        Return a JSON object with:
        - "type": "invoice" or "expense"
        - "category": e.g., "food", "travel", "utilities", "services"
        """
        try:
            response_text = self._generate(prompt, json_mode=True)
            return json.loads(response_text)
        except json.JSONDecodeError:
            logger.warning("Failed to parse classification JSON, returning raw text")
            return {"raw_response": response_text}

    def structure_document(self, text: str, classification: dict) -> dict:
        """
        Extracts structured data from the document based on classification.
        Expected Output: JSON with fields like date, total_amount, vendor, etc.
        """
        doc_type = classification.get("type", "unknown")
        
        prompt = f"""
        You are a data extraction assistant. specific instructions to extract data...
        [PLACEHOLDER FOR STRUCTURING PROMPT]
        
        Document Type: {doc_type}
        
        Extract structured information from the text below:
        {text}
        
        Return a JSON object with fields appropriate for the document type (e.g., date, total, vendor, items).
        """
        try:
            response_text = self._generate(prompt, json_mode=True)
            return json.loads(response_text)
        except json.JSONDecodeError:
            logger.warning("Failed to parse structured JSON, returning raw text")
            return {"raw_response": response_text}

llm_service = LLMService()
