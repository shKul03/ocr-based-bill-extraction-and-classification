from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.sql import func
from app.db.database import Base


class Document(Base):
    __tablename__ = "documents"

    document_id = Column(String(36), primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    object_key = Column(String(512), nullable=False)
    content_type = Column(String(50))

    bill_type = Column(String(50))
    bill_subtype = Column(String(50))

    extracted_data = Column(JSON)
    netsuite_data = Column(JSON)

    created_at = Column(DateTime, server_default=func.now())
