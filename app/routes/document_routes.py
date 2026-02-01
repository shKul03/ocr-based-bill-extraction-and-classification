from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from app.services.storage_service import storage_service
from app.services.ocr_service import ocr_service
from app.services.llm_service import llm_service
from app.models.api import DocumentResponse, ForwardRequest, UploadResponse
from app.config import settings
import httpx
import logging
import datetime
import uuid

router = APIRouter()
logger = logging.getLogger(__name__)

async def _send_to_dashboard(url: str, payload: dict):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=payload, timeout=10.0)
            resp.raise_for_status()
            logger.info("Successfully sent document to dashboard")
        except Exception as e:
            logger.error(f"Dashboard push failed: {e}")



@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
):
    try:
        # 1. Read file
        contents = await file.read()
        logger.info(f"Received file: {file.filename}")

        # 2. Store image
        image_id = storage_service.save_image(
            contents, file.filename, file.content_type
        )

        # 3. OCR
        ocr_text = ocr_service.extract_text(contents)
        logger.info("OCR extraction complete")

        # 4. LLM (classification + extraction + netsuite)
        llm_result = llm_service.structure_document(ocr_text)

        bill_type = llm_result["bill_type"]
        bill_subtype = llm_result["bill_subtype"]
        extracted_data = llm_result["structured_data"]
        netsuite_data = llm_result["netsuite_payload"]

        logger.info(
            f"LLM processing complete | type={bill_type}, subtype={bill_subtype}"
        )


        # extracted_data = llm_result["structured_data"]
        # netsuite_data = llm_result["netsuite_payload"]
        # classification = llm_result["classification"]

        logger.info("LLM processing complete")

        # 5. Canonical timestamps
        document_id = str(uuid.uuid4())
        created_at = datetime.datetime.utcnow()


        canonical_payload = {
            "document_id": document_id,
            "created_at": created_at.isoformat(),
            "bill_type": bill_type,
            "bill_subtype": bill_subtype,
            "extracted_data": extracted_data,
            "netsuite_data": netsuite_data,
            "uploaded_img": str(image_id),
        }

        if settings.DASHBOARD_API_URL:
            background_tasks.add_task(
                _send_to_dashboard,
                settings.DASHBOARD_API_URL,
                canonical_payload,
            )



        # 6. Persist INTERNAL document (rich data)
        doc_id = storage_service.save_document_data(
            image_id=image_id,
            ocr_text=ocr_text,
            bill_type=bill_type,
            bill_subtype=bill_subtype,
            extracted_data=extracted_data,
            netsuite_data=netsuite_data,
            metadata={
                "filename": file.filename,
                "created_at": created_at.isoformat(),
                "llm_model": settings.LLM_MODEL,
            },
        )

        # 7. Canonical object (used everywhere else)
        canonical_payload = {
            "document_id": document_id,
            "created_at": created_at.isoformat(),
            "extracted_data": extracted_data,
            "netsuite_data": netsuite_data,
            "uploaded_img": str(image_id),
        }

        # 8. Send to dashboard (NON-BLOCKING)
        if settings.DASHBOARD_API_URL:
            background_tasks.add_task(
                _send_to_dashboard,
                settings.DASHBOARD_API_URL,
                canonical_payload,
            )

        # 9. Return API response (MATCHES UploadResponse)
        return UploadResponse(
            document_id=canonical_payload["document_id"],
            created_at=created_at,
            bill_type=bill_type,
            bill_subtype=bill_subtype,
            extracted_data=extracted_data,
            netsuite_data=netsuite_data,
            uploaded_img=str(image_id),
        )


    except Exception:
        logger.exception("Error processing document")
        raise HTTPException(status_code=500, detail="Document processing failed")

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
        bill_type=doc["bill_type"],
        bill_subtype=doc["bill_subtype"],
        extracted_data=doc["extracted_data"],
        netsuite_data=doc["netsuite_data"],
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
        "data": doc["extracted_data"],
        "classification": doc["bill_type"]
    }
    
    background_tasks.add_task(_send_forward_request, target_url, payload)
    
    return {"status": "Forwarding initiated", "target_url": target_url}
