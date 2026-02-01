from pydantic import BaseModel
from typing import Dict, Any, Optional

class DocumentResponse(BaseModel):
    document_id: str
    ocr_text: str
    classification: Dict[str, Any]
    structured_data: Dict[str, Any]
    metadata: Dict[str, Any]

class ForwardRequest(BaseModel):
    document_id: str
    target_url: Optional[str] = None
