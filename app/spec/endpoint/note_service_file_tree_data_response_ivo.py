# Swagger에서 입력받을 데이터 구조 정의
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel


class TreeType(str, Enum):
    FOLDER = "folder"
    NOTE = "note"


class NoteServiceFileTreeDataResponseIVO(BaseModel):
    id: str  # 식별 아이디 (폴더: 'ID' + 폴더명 / 파일: 파일 고유 아이디)
    name: str
    type: TreeType
    parentId: Optional[str]
    path: str
    order: int
    expanded: Optional[bool] = None  # 화면에서 사용하는 폴더 열고 닫고, 백엔드에서는 null 응답
    children: Optional[List["NoteServiceFileTreeDataResponseIVO"]] = None


# 재귀 모델 선언을 위해 필요한 메소드
NoteServiceFileTreeDataResponseIVO.model_rebuild()
