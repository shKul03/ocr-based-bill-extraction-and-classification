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

    def save_document_data(self, image_id: str, ocr_text: str, classification: dict, structured_data: dict, metadata: dict) -> str:
        """Stores the processed document data in the documents collection."""
        document = {
            "image_id": image_id,
            "ocr_text": ocr_text,
            "classification": classification,
            "structured_data": structured_data,
            "metadata": metadata
        }
        result = self.db.documents.insert_one(document)
        return str(result.inserted_id)

    def get_document(self, document_id: str) -> dict | None:
        """Retrieves document metadata by ID."""
        try:
            return self.db.documents.find_one({"_id": ObjectId(document_id)})
        except Exception as e:
            logger.error(f"Error retrieving document {document_id}: {e}")
            return None

storage_service = StorageService()
