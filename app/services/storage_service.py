from pymongo import MongoClient
import gridfs
from bson import ObjectId
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self):
        try:
            self.client = MongoClient(settings.MONGO_URI)
            self.db = self.client[settings.DB_NAME]
            self.fs = gridfs.GridFS(self.db)
            logger.info("Connected to MongoDB")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    def save_image(self, file_data: bytes, filename: str, content_type: str) -> str:
        """Stores the raw image in GridFS and returns the file ID."""
        file_id = self.fs.put(file_data, filename=filename, content_type=content_type)
        return str(file_id)

    def get_image(self, file_id: str) -> bytes:
        """Retrieves an image from GridFS by ID."""
        try:
            grid_out = self.fs.get(ObjectId(file_id))
            return grid_out.read()
        except Exception as e:
            logger.error(f"Error retrieving file {file_id}: {e}")
            raise

    # def save_document_data(
    # self,
    # document_id: str,
    # created_at: str,
    # bill_type: str,
    # bill_subtype: str,
    # uploaded_img: str,
    # extracted_data: dict,
    # netsuite_data: dict,
    # metadata: dict,
    # ):
    #     """Stores the processed document data in the documents collection."""
    #     document = {
    #         "document_id": document_id,
    #         "created_at": created_at,
    #         "bill_type": bill_type,
    #         "bill_subtype": bill_subtype,
    #         "uploaded_img": uploaded_img,
    #         "extracted_data": extracted_data,
    #         "netsuite_data": netsuite_data,
    #         "metadata": metadata,
    #     }



    #     result = self.db.documents.insert_one(document)
    #     return str(result.inserted_id)
    def save_document_data(self, document: dict, metadata: dict):
        document["metadata"] = metadata

        self.db.documents.insert_one(document)



    def get_document(self, document_id: str) -> dict | None:
        """Retrieves document metadata by ID."""
        try:
            return self.db.documents.find_one({"_id": ObjectId(document_id)})
        except Exception as e:
            logger.error(f"Error retrieving document {document_id}: {e}")
            return None

storage_service = StorageService()
