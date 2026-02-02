from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime

# -----------------------------
# Used for /document/{id}
# -----------------------------
class DocumentResponse(BaseModel):
    document_id: str
    ocr_text: str
    bill_type: str
    bill_subtype: str
    structured_data: Dict[str, Any]
    metadata: Dict[str, Any]


class ClassificationResponse(BaseModel):
    status: str
    bill_type: str
    bill_subtype: str
    document_id: str


# -----------------------------
# Used for /upload + dashboard
# -----------------------------

class UploadResponse(BaseModel):
    document_id: str
    created_at: datetime
    bill_type: Optional[str] = None
    bill_subtype: Optional[str] = None
    extracted_data: Optional[Dict] = None
    netsuite_data: Optional[Dict] = None
    uploaded_img: str



# -----------------------------
# Used for /forward
# -----------------------------
class ForwardRequest(BaseModel):
    document_id: str
    target_url: Optional[str] = None


class DocumentListItem(BaseModel):
    document_id: str
    created_at: datetime
    bill_type: str
    bill_subtype: str
    extracted_data: Dict[str, Any]
    netsuite_data: Dict[str, Any]
    original_image_url: str # This is the link for your <img> tag