from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.minio_service import minio_service
from app.services.ocr_service import ocr_service
from app.services.llm_service import llm_service
from app.services.sql_service import sql_service
from app.models.api import UploadResponse
from typing import List
from app.models.api import DocumentListItem
import logging
import datetime
import uuid


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
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
        # 3. LLM Classification
        # -------------------------
        llm_result = llm_service.structure_document(ocr_text)

        bill_type = llm_result["bill_type"]
        bill_subtype = llm_result["bill_subtype"]
        extracted_data = llm_result["structured_data"]
        netsuite_data = llm_result["netsuite_payload"]

        logger.info(
            f"LLM complete | type={bill_type}, subtype={bill_subtype}"
        )

        # -------------------------
        # 4. Persist metadata in MySQL
        # -------------------------
        sql_service.insert_document(
            document_id=document_id,
            filename=file.filename,
            object_key=object_key,
            content_type=file.content_type,
            bill_type=bill_type,
            bill_subtype=bill_subtype,
            extracted_data=extracted_data,
            netsuite_data=netsuite_data,
            created_at=created_at,
        )

        # -------------------------
        # 5. Return FINAL response
        # -------------------------
        return UploadResponse(
            document_id=document_id,
            created_at=created_at,
            bill_type=bill_type,
            bill_subtype=bill_subtype,
            extracted_data=extracted_data,
            netsuite_data=netsuite_data,
            uploaded_img=object_key,
        )

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
            
        return response_data
    except Exception as e:
        logger.error(f"Failed to fetch documents: {e}")
        raise HTTPException(status_code=500, detail="Could not retrieve data")