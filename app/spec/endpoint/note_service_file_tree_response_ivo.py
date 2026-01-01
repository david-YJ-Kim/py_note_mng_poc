# Swagger에서 입력받을 데이터 구조 정의
from typing import List

from pydantic import BaseModel

from app.spec.endpoint.note_service_file_tree_data_response_ivo import NoteServiceFileTreeDataResponseIVO


class NoteServiceFileTreeResponseIVO(BaseModel):
    success: bool
    data: List[NoteServiceFileTreeDataResponseIVO]
    message: str
