from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from app.services.storage_service import storage_service
from app.services.ocr_service import ocr_service
from app.services.llm_service import llm_service
from app.models.api import DocumentResponse, ForwardRequest
from app.config import settings
import httpx
import logging
import datetime

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Uploads an image, processes it (OCR -> Classify -> Structure), and stores data.
    """
    try:
        # 1. Read File
        contents = await file.read()
        
        # 2. Store Image in GridFS
        image_id = storage_service.save_image(contents, file.filename, file.content_type)
        
        # 3. OCR Extraction
        ocr_text = ocr_service.extract_text(contents)
        
        # 4. Classification
        classification = llm_service.classify_document(ocr_text)
        
        # 5. Structuring
        structured_data = llm_service.structure_document(ocr_text, classification)
        
        # 6. Save Metadata & Results
        metadata = {
            "filename": file.filename,
            "upload_timestamp": datetime.datetime.utcnow().isoformat(),
            "llm_model": settings.LLM_MODEL
        }
        
        doc_id = storage_service.save_document_data(
            image_id=image_id,
            ocr_text=ocr_text,
            classification=classification,
            structured_data=structured_data,
            metadata=metadata
        )
        
        return DocumentResponse(
            document_id=doc_id,
            ocr_text=ocr_text,
            classification=classification,
            structured_data=structured_data,
            metadata=metadata
        )

    except Exception as e:
        logger.error(f"Error processing document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/document/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str):
    """
    Retrieves stored document data.
    """
    doc = storage_service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return DocumentResponse(
        document_id=str(doc["_id"]),
        ocr_text=doc["ocr_text"],
        classification=doc["classification"],
        structured_data=doc["structured_data"],
        metadata=doc["metadata"]
    )

async def _send_forward_request(url: str, payload: dict):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=payload, timeout=10.0)
            resp.raise_for_status()
            logger.info(f"Successfully forwarded document to {url}")
        except Exception as e:
            logger.error(f"Failed to forward document to {url}: {e}")

@router.post("/forward")
async def forward_document(req: ForwardRequest, background_tasks: BackgroundTasks):
    """
    Forwards the document data to an external API.
    """
    doc = storage_service.get_document(req.document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    target_url = req.target_url or settings.EXTERNAL_API_URL
    if not target_url:
        raise HTTPException(status_code=400, detail="Target URL not specified in request or environment")

    payload = {
        "document_id": str(doc["_id"]),
        "data": doc["structured_data"],
        "classification": doc["classification"]
    }
    
    background_tasks.add_task(_send_forward_request, target_url, payload)
    
    return {"status": "Forwarding initiated", "target_url": target_url}
