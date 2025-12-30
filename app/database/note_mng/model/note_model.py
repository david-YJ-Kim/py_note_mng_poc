from sqlalchemy import Column, Integer, String, DateTime, func
from app.database.base import Base
from app.database.note_mng.constant.table_name import TableNames


class NoteMetadata(Base):
    __tablename__ = TableNames.NOTE_META
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    file_path = Column(String(500), unique=True, nullable=False)
    last_commit_hash = Column(String(100))
    last_modified_by = Column(String, nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
