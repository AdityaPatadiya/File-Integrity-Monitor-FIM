"""
fim_models.py
--------------
Contains ORM models for File Integrity Monitoring (fim_db)
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from datetime import datetime
from src.api.database.connection import FimBase


class Directory(FimBase):
    __tablename__ = "directories"

    id = Column(Integer, primary_key=True, index=True)
    path = Column(String(500), unique=True, nullable=False)
    hash = Column(String(128), nullable=False)
    last_modified = Column(DateTime, nullable=False)
    last_checked = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<MonitoredFile(path='{self.path}')>"


class FileMetadata(FimBase):
    __tablename__ = "file_metadata"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False)  # e.g., "modified", "deleted"
    details = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    verified = Column(Boolean, default=False)

    def __repr__(self):
        return f"<IntegrityLog(file_id={self.file_id}, status='{self.status}')>"
