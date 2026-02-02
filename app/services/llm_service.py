import httpx
import logging
import json
from pathlib import Path
from app.config import settings

logger = logging.getLogger(__name__)

# Base path: app/prompts/
PROMPT_BASE_PATH = Path(__file__).resolve().parent.parent / "prompts"


def load_prompt(relative_path: str) -> str:
    """
    Load a prompt file from app/prompts/*
    """
    prompt_path = PROMPT_BASE_PATH / relative_path
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt not found: {prompt_path}")
    return prompt_path.read_text()


class LLMService:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.LLM_MODEL
        self.client = httpx.Client(
            base_url=self.base_url,
            timeout=httpx.Timeout(
                connect=10.0,
                read=300.0,   # ⬅️ allow long generations
                write=10.0,
                pool=10.0,
            ),
        )


        # ---- Load prompts once at startup ----
        self.classifier_prompt = load_prompt(
            "classifier/classifier_prompt.txt"
        )

        self.expense_extraction_prompt = load_prompt(
            "extractors/expense_extraction_prompt.txt"
        )

        self.invoice_extraction_prompt = load_prompt(
            "extractors/invoice_extraction_prompt.txt"
        )

        self.expense_netsuite_prompt = load_prompt(
            "netsuite/expense_netsuite_prompt.txt"
        )

        self.invoice_netsuite_prompt = load_prompt(
            "netsuite/invoice_netsuite_prompt.txt"
        )

    def structure_document(self, ocr_text: str) -> dict:
        logger.info("Classifying document")

        classification = self.classify_document(ocr_text)

        bill_type = classification.get("bill_type")
        bill_subtype = classification.get("bill_subtype")

        logger.info(f"bill type: {bill_type}")
        logger.info(f"bill subtype: {bill_subtype}")

        if not bill_type or not bill_subtype:
            raise ValueError("Bill type or subtype missing from classification")

        logger.info(f"Bill type: {bill_type}, subtype: {bill_subtype}")

        logger.info("Extracting structured data")
        structured_data = self.extract_structured_data(
            ocr_text=ocr_text,
            document_type=bill_type
        )
        logger.info(f"structured data: {structured_data}")

        logger.info("Transforming for NetSuite")
        netsuite_payload = self.transform_for_netsuite(
            structured_data=structured_data,
            document_type=bill_type
        )
        logger.info(f"netsuite payload: {netsuite_payload}")

        return {
            "bill_type": bill_type,
            "bill_subtype": bill_subtype,
            "structured_data": structured_data,
            "netsuite_payload": netsuite_payload,
        }
    def _generate(self, prompt: str, json_mode: bool = False) -> str:
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

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------
    def classify_document(self, ocr_text: str) -> dict:
        """
        Classifies document as invoice or expense.
        """
        prompt = f"""
{self.classifier_prompt}

OCR TEXT:
{ocr_text}
"""

        try:
            response_text = self._generate(prompt, json_mode=True)
            return json.loads(response_text)
        except json.JSONDecodeError:
            logger.warning("Failed to parse classification JSON")
            return {"raw_response": response_text}

    # ------------------------------------------------------------------
    # Extraction (Invoice / Expense)
    # ------------------------------------------------------------------
    def extract_structured_data(
        self,
        ocr_text: str,
        document_type: str
    ) -> dict:
        if document_type == "expense" or document_type == "Expense Bill":
            base_prompt = self.expense_extraction_prompt
        elif document_type == "invoice" or document_type == "Invoice Bill":
            base_prompt = self.invoice_extraction_prompt
        else:
            raise ValueError(f"Unsupported document type: {document_type}")

        prompt = f"""
{base_prompt}

OCR TEXT:
{ocr_text}
"""

        try:
            response_text = self._generate(prompt, json_mode=True)
            return json.loads(response_text)
        except json.JSONDecodeError:
            logger.warning("Failed to parse extraction JSON")
            return {"raw_response": response_text}

    # ------------------------------------------------------------------
    # NetSuite / API Transformation
    # ------------------------------------------------------------------
    def transform_for_netsuite(
        self,
        structured_data: dict,
        document_type: str
    ) -> dict:
        doc_type_clean = document_type.strip().lower()
        if "expense" in doc_type_clean:
            base_prompt = self.expense_netsuite_prompt
        elif "invoice" in doc_type_clean:
            base_prompt = self.invoice_netsuite_prompt
        else:
            raise ValueError(f"Unsupported document type: {document_type}")

        prompt = f"""
{base_prompt}

INPUT JSON:
{json.dumps(structured_data, indent=2)}
"""

        try:
            response_text = self._generate(prompt, json_mode=True)
            return json.loads(response_text)
        except json.JSONDecodeError:
            logger.warning("Failed to parse NetSuite JSON")
            return {"raw_response": response_text}


llm_service = LLMService()
