from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.minio_service import minio_service
from app.services.ocr_service import ocr_service
from app.services.llm_service import llm_service
from app.services.sql_service import sql_service
from app.models.api import UploadResponse, ClassificationResponse
from typing import List
from app.models.api import DocumentListItem
import logging
import datetime
import uuid


router = APIRouter()
logger = logging.getLogger(__name__)


from fastapi import BackgroundTasks

def process_full_document(
    document_id: str,
    ocr_text: str,
    bill_type: str,
    bill_subtype: str,
    filename: str,
    object_key: str,
    content_type: str,
    created_at: datetime.datetime
):
    try:
        logger.info(f"Background processing started for {document_id}")
        
        # 3. LLM Extraction (taking where classification left off)
        logger.info("Extracting structured data")
        structured_data = llm_service.extract_structured_data(
            ocr_text=ocr_text,
            document_type=bill_type
        )
        logger.info(f"Extracted Data: {structured_data}")
        
        logger.info("Transforming for NetSuite")
        netsuite_payload = llm_service.transform_for_netsuite(
            structured_data=structured_data,
            document_type=bill_type
        )
        logger.info(f"NetSuite Payload: {netsuite_payload}")
        
        # 4. Persist metadata in MySQL
        sql_service.insert_document(
            document_id=document_id,
            filename=filename,
            object_key=object_key,
            content_type=content_type,
            bill_type=bill_type,
            bill_subtype=bill_subtype,
            extracted_data=structured_data,
            netsuite_data=netsuite_payload,
            created_at=created_at,
        )
        logger.info(f"Background processing complete for {document_id}")
        
    except Exception as e:
        logger.exception(f"Background processing failed for {document_id}: {e}")

@router.post("/upload", response_model=ClassificationResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    try:
        contents = await file.read()
        logger.info(f"Received file: {file.filename}")

        document_id = str(uuid.uuid4())
        created_at = datetime.datetime.utcnow()

        # -------------------------
        # 1. Store image in MinIO
        # -------------------------
        object_key = minio_service.upload_image(
            contents=contents,
            filename=file.filename,
            content_type=file.content_type,
            document_id=document_id,
        )

        # -------------------------
        # 2. OCR
        # -------------------------
        ocr_text = ocr_service.extract_text(contents)
        logger.info("OCR extraction complete")

        # -------------------------
        # 3. LLM Classification (Immediate)
        # -------------------------
        classification = llm_service.classify_document(ocr_text)
        bill_type = classification.get("bill_type", "Unknown")
        bill_subtype = classification.get("bill_subtype", "Unknown")

        if isinstance(bill_type, list):
            bill_type = bill_type[0] if bill_type else "Unknown"
        if isinstance(bill_subtype, list):
            bill_subtype = bill_subtype[0] if bill_subtype else "Unknown"

        if not bill_type or not bill_subtype:
             logger.warning("Classification might be incomplete")

        # Schedule the rest
        background_tasks.add_task(
            process_full_document,
            document_id=document_id,
            ocr_text=ocr_text,
            bill_type=bill_type,
            bill_subtype=bill_subtype,
            filename=file.filename,
            object_key=object_key,
            content_type=file.content_type,
            created_at=created_at
        )

        # -------------------------
        # 5. Return IMMEDIATE response
        # -------------------------
        # We need to return valid JSON matching the new requirements. 
        # But wait, the router decorator says response_model=UploadResponse. 
        # I need to update that too.
        # Since this tool call is replacing the function body, I will handle the decorator change in a separate call or try to include it if I can match the lines perfectly.
        # I will return a dictionary that matches ClassificationResponse structure for now, and update the decorator in the next step or if I can match it here.
        # It's safer to update the decorator separately or via multi-replace if I want to be atomic.
        # I'll stick to replacing the function logic here, but I must make sure I don't break the response validation.
        # Actually I can't return ClassificationResponse if the model is UploadResponse.
        
        # User requested: {"status": "classified", "bill_type": bill_type, "bill_subtype": subtype}
        return {
            "status": "classified",
            "bill_type": bill_type,
            "bill_subtype": bill_subtype,
            "document_id": document_id
        }

    except Exception:
        logger.exception("Document upload failed")
        raise HTTPException(status_code=500, detail="Document upload failed")


@router.get("/all", response_model=List[UploadResponse])
async def get_all_documents():
    try:
        # 1. Fetch all records from MySQL
        documents = sql_service.get_all_documents()
        
        response_data = []
        for doc in documents:
            # 2. Generate a temporary link (valid for 1 hour) for the frontend
            image_url = minio_service.get_presigned_url(doc.object_key)
            
            response_data.append(UploadResponse(
                document_id=doc.document_id,
                created_at=doc.created_at,
                bill_type=doc.bill_type,
                bill_subtype=doc.bill_subtype,
                extracted_data=doc.extracted_data,
                netsuite_data=doc.netsuite_data,
                uploaded_img=image_url if image_url else ""
            ))
            logger.info(f"\n\nResponse Data: {response_data}")
            
        return response_data
    except Exception as e:
        logger.error(f"Failed to fetch documents: {e}")
        raise HTTPException(status_code=500, detail="Could not retrieve data")