"""
Reprocess documents with empty extracted_data and netsuite_data.

This script fetches documents from the database that have empty data fields,
retrieves their images from MinIO, performs OCR, LLM extraction, and updates
the database with the extracted data.
"""

from app.services.sql_service import sql_service
from app.services.minio_service import minio_service
from app.services.ocr_service import ocr_service
from app.services.llm_service import llm_service

def reprocess_empty_documents():
    """Reprocess all documents with empty extracted_data or netsuite_data."""
    
    # Get all documents
    documents = sql_service.get_all_documents()
    
    empty_docs = [
        doc for doc in documents 
        if not doc.extracted_data or not doc.netsuite_data
    ]
    
    print(f"Found {len(empty_docs)} documents with empty data")
    
    for doc in empty_docs:
        print(f"\nReprocessing document: {doc.document_id}")
        print(f"  Type: {doc.bill_type} / {doc.bill_subtype}")
        
        try:
            # Download image from MinIO
            print(f"  Downloading from MinIO: {doc.object_key}")
            image_data = minio_service.get_object(doc.object_key)
            
            # Perform OCR
            print(f"  Performing OCR...")
            ocr_text = ocr_service.extract_text(image_data)
            
            # Extract structured data
            print(f"  Extracting structured data...")
            structured_data = llm_service.extract_structured_data(
                ocr_text=ocr_text,
                document_type=doc.bill_type
            )
            
            # Transform for NetSuite
            print(f"  Transforming for NetSuite...")
            netsuite_payload = llm_service.transform_for_netsuite(
                structured_data=structured_data,
                document_type=doc.bill_type
            )
            
            # Update database
            print(f"  Updating database...")
            sql_service.update_document_data(
                document_id=doc.document_id,
                extracted_data=structured_data,
                netsuite_data=netsuite_payload
            )
            
            print(f"  ✓ Successfully reprocessed {doc.document_id}")
            
        except Exception as e:
            print(f"  ✗ Failed to reprocess {doc.document_id}: {e}")
            continue

if __name__ == "__main__":
    reprocess_empty_documents()
