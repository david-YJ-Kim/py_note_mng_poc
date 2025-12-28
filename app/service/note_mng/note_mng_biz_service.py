import asyncio
from cmath import acos

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.note_mng.connection import get_db
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
        existing_note = await self._get_note_by_title_first(title)

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

    async def get_all_notes(self):
        """ DB에 저장된 모든 노트 메타데이터 목록 조회 """
        query = select(NoteMetadata).order_by(NoteMetadata.updated_at.desc())
        resource = await self.db.execute(query)
        return resource.scalars().all()


    async def get_note_detail(self, title:str):
        """ 특정 노트의 DB 정보와 Git 히스토리를 함께 조회 """
        # 1. DB 메터데이터 조회
        note_meta = await self._get_note_by_title_first(title)
        if not note_meta:
            return None

        # 2. Git 서비스로부터 해당 파일의 커밋 로그(이력) 가져오기
        # 동기 함수인 get_file_history를 별도 스레드에서 실행
        loop = asyncio.get_event_loop()
        git_history = await loop.run_in_executor(
            None, self.git_service.get_file_history, note_meta.file_path
        )

        # 3. 각 커밋의 Diff 정보를 비동기 병렬로 추출
        # 실행할 작업 (Task) 리스트 생성
        tasks = [
            self._get_diff_async(item, note_meta.file_path)
            for item in git_history
        ]

        # 모든 태스크를 동시에 실행하고 결과 대기
        history_with_diff = await asyncio.gather(*tasks)


        return {
            "metadata": note_meta,
            "git_history": history_with_diff,
        }

    async def _get_diff_async(self, item:dict, file_path: str):
        """ 개별 커밋의 diff를 비동기적으로 가져오는 헬퍼 메서드 """
        loop = asyncio.get_event_loop()
        # 동기 함수인 get_file_diff를 별도 스레드에서 수행
        diff_content = await loop.run_in_executor(
            None,
            self.git_service.get_file_diff,
            item['hash'],
            file_path
        )
        item['diff'] = diff_content
        return item


    async def _get_note_by_title_first(self, title:str) -> NoteMetadata:
        """ 내부용: 제목으로 노트 메타데이터 조회 """
        query = select(NoteMetadata).where(NoteMetadata.title == title)
        result = await self.db.execute(query)
        return result.scalars().first()

## 의존성 주입을 위한 함수 만들기
async def get_note_service(db:AsyncSession = Depends(get_db)) -> NoteService:
    return NoteService(db)
