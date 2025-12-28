from cmath import acos

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.note_mng.model.note_model import NoteMetadata
from app.service.git_manage_service.git_poc import GitService


class NoteService:
    def __init__(self, db:AsyncSession):
        self.db = db
        self.git_service = GitService()

    async def save_or_update_note(self, title:str, content:str, user_name:str):
        """
        노트를 저장하거나 업데이트 하고, Git 커밋 해시를 DB에 기록합니다.
        :param title:
        :param content:
        :param user_name:
        :return:
        """
        file_name = f"{title}.md"

        # 1. DB에서 기존 노트 조회
        existing_note = await self._get_note_by_title(title)

        # 2. Git 서비스 호출 (파일 쓰기 및 커밋)
        new_hash = self.git_service.write_and_commit(
            file_name, content, user_name, f"Saev/Update note: {title}"
        )

        # 3. DB 메타데이터 처리
        if existing_note:
            action = "updated"
            existing_note.last_commit_hash = new_hash
        else :
            action = "created"
            new_note = NoteMetadata(
                title=title,
                file_path=file_name,
                last_commit_hash=new_hash,
            )
            self.db.add(new_note)

        return {
            "action": action,
            "commit_hash": new_hash,
            "file_name": file_name,
        }


    async def _get_note_by_title(self, title:str) -> NoteMetadata:
        """ 내부용: 제목으로 노트 메타데이터 조회 """
        query = select(NoteMetadata).where(NoteMetadata.title == title)
        result = await self.db.execute(query)
        return result.scalars().first()
