import uuid

from sqlalchemy import Column, Integer, String, DateTime, func, UniqueConstraint

from app.database.default_model_mixin import Base, ObjIdMixin, UseMixin, AuditMixin, TimestampMixin, RecordNoteMixin
from app.database.note_mng.constant.table_name import TableNames


class NoteMetadata(Base, ObjIdMixin, UseMixin, AuditMixin, TimestampMixin, RecordNoteMixin):
    __tablename__ = TableNames.NOTE_META

    __table_args__ = (
        UniqueConstraint('title', name='uk_note_meta_title'),
    )

    id = Column(Integer, primary_key=True, default=lambda: uuid.uuid4().hex)
    title = Column(String(255), nullable=False, unique=True)
    file_path = Column(String(500), unique=True, nullable=False)
    last_commit_hash = Column(String(100))
    last_modified_by = Column(String, nullable=False)
