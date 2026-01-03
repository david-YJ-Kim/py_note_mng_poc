from pydantic import BaseModel
from sqlalchemy import DateTime

from app.spec.constant.ModelEnums import UseStatEnum


class NoteResponseIvo(BaseModel):
    id: str
    title: str
    filePath: str
    updateUser: str
    useStatCd: UseStatEnum
    crtDate: DateTime
    updateDate: DateTime
