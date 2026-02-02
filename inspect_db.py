from app.services.sql_service import sql_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_db():
    logger.info("Fetching documents from DB...")
    docs = sql_service.get_all_documents()
    for doc in docs:
        print(f"ID: {doc.document_id}")
        print(f"Extracted Data ({type(doc.extracted_data)}): {doc.extracted_data}")
        print(f"NetSuite Data ({type(doc.netsuite_data)}): {doc.netsuite_data}")
        print("-" * 20)

if __name__ == "__main__":
    check_db()
