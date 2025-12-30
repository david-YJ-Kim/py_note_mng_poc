# Swagger에서 입력받을 데이터 구조 정의
from pydantic import BaseModel


class NoteSaveRequest(BaseModel):
    title: str
    content: str
    user_name: str
    last_hash: str | None = None # 클라이언트가 알고 있는 마지막 커밋 해시