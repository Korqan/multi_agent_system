from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from src.database import Base

class Industry(Base):
    __tablename__ = "industries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    url_configs = relationship("URLConfig", back_populates="industry")
    documents = relationship("DocumentMeta", back_populates="industry")

class URLConfig(Base):
    __tablename__ = "url_configs"

    id = Column(Integer, primary_key=True, index=True)
    industry_id = Column(Integer, ForeignKey("industries.id"))
    url = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    last_scraped_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    industry = relationship("Industry", back_populates="url_configs")

class DocumentMeta(Base):
    __tablename__ = "document_metas"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    source_url = Column(String, nullable=True) # for web scraped documents
    source_type = Column(String, nullable=False) # 'upload' or 'web'
    status = Column(String, default="pending") # 'pending', 'approved', 'rejected'
    summary = Column(Text, nullable=True)
    industry_id = Column(Integer, ForeignKey("industries.id"))
    file_hash = Column(String, nullable=True) # To prevent duplicate ingestion
    fetch_timestamp = Column(DateTime, default=datetime.utcnow)
    
    industry = relationship("Industry", back_populates="documents")
