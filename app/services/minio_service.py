from minio import Minio
from minio.error import S3Error
import uuid
import logging
from datetime import timedelta # Add this import
from app.config import settings

logger = logging.getLogger(__name__)

class MinioService:
    def __init__(self):
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        self.bucket = settings.MINIO_BUCKET

        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)
            logger.info(f"Created MinIO bucket: {self.bucket}")

    def get_presigned_url(self, object_key: str):
        """
        Generates a secure, temporary URL so the frontend can view the image
        """
        try:
            return self.client.presigned_get_object(
                bucket_name=self.bucket,
                object_name=object_key,
                expires=timedelta(hours=1)
            )
        except S3Error as e:
            logger.error(f"Error generating presigned URL: {e}")
            return None

    def get_object(self, object_key: str) -> bytes:
        """
        Retrieves an object from MinIO as bytes.
        """
        try:
            response = self.client.get_object(
                bucket_name=self.bucket,
                object_name=object_key
            )
            data = response.read()
            response.close()
            response.release_conn()
            logger.info(f"Retrieved object from MinIO: {object_key}")
            return data
        except S3Error as e:
            logger.error(f"Failed to retrieve object from MinIO: {e}")
            raise

    def upload_image(self, contents: bytes, filename: str, content_type: str, document_id: str) -> str:
        import io
        object_key = f"{document_id}/{filename}"
        
        try:
            self.client.put_object(
                bucket_name=self.bucket,
                object_name=object_key,
                data=io.BytesIO(contents),
                length=len(contents),
                content_type=content_type
            )
            logger.info(f"Uploaded image to MinIO: {object_key}")
            return object_key
        except S3Error as e:
            logger.error(f"Failed to upload image to MinIO: {e}")
            raise

minio_service = MinioService()