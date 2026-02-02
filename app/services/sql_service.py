import logging
from app.db.database import SessionLocal
from app.db.models.document import Document
# If your model name is different in your project, ensure 'Document' matches your SQLAlchemy class name

logger = logging.getLogger(__name__)

class SQLService:
    def insert_document(
        self,
        document_id: str,
        filename: str,
        object_key: str,
        content_type: str,
        bill_type: str,
        bill_subtype: str,
        extracted_data: dict,
        netsuite_data: dict,
        created_at,
    ):
        """
        Inserts a new document record into the MySQL database.
        """
        db = SessionLocal()
        try:
            doc = Document(
                document_id=document_id,
                filename=filename,
                object_key=object_key,
                content_type=content_type,
                bill_type=bill_type,
                bill_subtype=bill_subtype,
                extracted_data=extracted_data,
                netsuite_data=netsuite_data,
                created_at=created_at,
            )

            db.add(doc)
            db.commit()
            logger.info(f"Successfully inserted document {document_id} into MySQL")
            return doc

        except Exception:
            db.rollback()
            logger.exception("Failed to insert document into MySQL")
            raise
        finally:
            db.close()

    def get_all_documents(self):
        """
        Retrieves all document records from MySQL, ordered by newest first.
        """
        db = SessionLocal()
        try:
            documents = db.query(Document).order_by(Document.created_at.desc()).all()
            logger.info(f"Retrieved {len(documents)} documents from MySQL")
            return documents
        except Exception:
            logger.exception("Failed to fetch documents from MySQL")
            raise
        finally:
            db.close()

    def update_document_data(
        self,
        document_id: str,
        extracted_data: dict,
        netsuite_data: dict
    ):
        """
        Updates the extracted_data and netsuite_data for an existing document.
        """
        db = SessionLocal()
        try:
            doc = db.query(Document).filter(Document.document_id == document_id).first()
            if not doc:
                raise ValueError(f"Document {document_id} not found")
            
            doc.extracted_data = extracted_data
            doc.netsuite_data = netsuite_data
            
            db.commit()
            logger.info(f"Successfully updated document {document_id} in MySQL")
            return doc
        except Exception:
            db.rollback()
            logger.exception(f"Failed to update document {document_id} in MySQL")
            raise
        finally:
            db.close()

# Instantiate the service so it can be imported elsewhere
sql_service = SQLService()