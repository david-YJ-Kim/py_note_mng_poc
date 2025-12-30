from datetime import datetime

from pydantic import BaseModel


class NoteConflictDetail(BaseModel):
    """Note 충돌 발생 시, 서버의 상태를 담는 모델"""
    server_last_hash: str
    server_content: str
    modified_by: str
    updated_at: datetime
