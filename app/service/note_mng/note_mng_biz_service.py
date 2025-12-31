# note_mng_biz_service.py

import asyncio

from fastapi import Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.note_mng.connection import get_db
from app.database.note_mng.model.note_model import NoteMetadata
from app.exception.NoteConflictError import NoteConflictError
from app.service.git_manage_service.git_poc import GitService
from app.service.lang_analyzer.search_manager import NoteSearchManager
from app.spec.biz.NoteConflictDetail import NoteConflictDetail


class NoteService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.git_service = GitService()
        self.search_manager = NoteSearchManager()

    async def get_notes_with_pagination(self, keyword: str | None = None, page: int = 1, size: int = 20):

        skip = (page - 1) * size

        # 1. 기본 쿼리 생성
        query = select(NoteMetadata)
        count_query = select(func.count()).select_from(NoteMetadata)

        # 2. 검색 조건 추가 (제목 기반 검색)
        if keyword:
            search_term = f"%{keyword}%"
            filter_stmt = NoteMetadata.title.like(search_term)
            query = query.where(filter_stmt)
            count_query = count_query.where(filter_stmt)

        # 3. 정렬 및 페이징 적용
        query = query.order_by(NoteMetadata.updated_at.desc()).offset(skip).limit(size)

        # 4. 실행
        total_count_result = await self.db.execute(count_query)
        total_count = total_count_result.scalar()

        result = await self.db.execute(query)
        items = result.scalars().all()

        return items, total_count

    async def save_or_update_note(self, title: str, content: str, user_name: str, last_hash: str = None):
        """
        노트를 저장하거나 업데이트 하고, Git 커밋 해시를 DB에 기록합니다.
        :param title:
        :param content:
        :param user_name:
        :param last_hash: 사용자가 수정한 마지막 git hash 버전
        :return:
        """
        file_name = f"{title}.md"

        # 1. DB에서 기존 노트 조회
        existing_note = await self._get_note_by_title_first(title)
        if existing_note:
            await self._check_conflict(existing_note, last_hash)
            action = "updated"
        else:
            action = "created"

        # 2. Git 서비스 호출 (파일 쓰기 및 커밋)
        new_hash = self.git_service.write_and_commit(
            file_name, content, user_name, f"Saev/Update note: {title}"
        )

        # 3. DB 메타데이터 처리
        if existing_note:
            existing_note.last_commit_hash = new_hash
            existing_note.last_modified_by = user_name
        else:
            new_node = NoteMetadata(
                title=title,
                file_path=file_name,
                last_commit_hash=new_hash,
                last_modified_by=user_name,
            )
            self.db.add(new_node)

        return {
            "action": action,
            "commit_hash": new_hash,
            "file_name": file_name,
            "author_name": user_name,
        }

    async def get_all_notes(self):
        """ DB에 저장된 모든 노트 메타데이터 목록 조회 """
        query = select(NoteMetadata).order_by(NoteMetadata.updated_at.desc())
        resource = await self.db.execute(query)
        return resource.scalars().all()

    async def get_notes_with_complex_search(self, keyword: str, page: int = 1, size: int = 20):
        """
        제목(DB)와 본문 (Whoosh)을 모두 아우르는 복합 검색
        :param keyword:
        :param page:
        :param size:
        :return:
        """

        skip = (page - 1) * size

        # 1. Whoosh에서 본문 검색 결과 (제목 리스트) 가져오기
        content_matched_titles = []
        if keyword:
            content_matched_titles = self.search_manager.search(keyword, limit=100)

        print(f"keyword:{keyword} content_matched_titles: {content_matched_titles}")

        # 2. DB에서 검색 (제목 검색 + Whoosh에서 넘어온 제목들 포함)
        query = select(NoteMetadata)
        search_term = f"%{keyword}%"
        filter_stmt = (NoteMetadata.title.like(search_term) | NoteMetadata.title.in_(content_matched_titles))
        query = query.where(filter_stmt)

        result = await self.db.execute(query.order_by(NoteMetadata.updated_at.desc()).offset(skip).limit(size))
        items = result.scalars().all()

        count_query = select(func.count()).select_from(NoteMetadata)
        total_count_result = await self.db.execute(count_query)

        return items, total_count_result.scalar()

    async def get_note_detail(self, title: str):
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

    def sync_all_files_to_index(self):
        """
        서버 시작 시 호출하여 기존 모든 파일을 Whoosh에 색인
        :return:
        """

        print(f"[System] 기존 파일 검색 색인 시작...")
        md_files = list(self.git_service.repo_path.glob("**/*.md"))

        # Whoosh writer 오픈
        writer = self.search_manager.ix.writer()
        for file_path in md_files:
            title = file_path.stem
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    # 기존 데이터가 있으면 덮어쓰기(Update)
                    writer.update_document(title=title, content=content)
            except Exception as e:
                print(f"[Error] 파일 읽기 실패 ({title}): {e}")

        writer.commit()
        print(f"[System] 총 {len(md_files)} 개의 문서 색인 완료")

    async def _get_diff_async(self, item: dict, file_path: str):
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

    async def _get_note_by_title_first(self, title: str) -> NoteMetadata:
        """ 내부용: 제목으로 노트 메타데이터 조회 """
        query = select(NoteMetadata).where(NoteMetadata.title == title)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def _check_conflict(self, note: NoteMetadata, client_hash: str):
        """DB 해시와 클라이언트 보유 해시를 비교하여 충돌 시 상세 정보와 함께 예외 발생"""
        if client_hash and note.last_commit_hash != client_hash:
            # 1. 최신 파일 내용 읽기
            server_content = self.git_service.read_file_content(note.file_path)

            # 2. 타입을 맞춘 (ConflictDetail 모델) 객체 생성
            conflict_info = NoteConflictDetail(
                server_last_hash=note.last_commit_hash,
                server_content=server_content,
                updated_at=note.updated_at,
                modified_by=note.last_modified_by,
            )

            # 상세 정보를 예외 객체에 담아 던짐
            raise NoteConflictError(conflict_data=conflict_info)


## 의존성 주입을 위한 함수 만들기
async def get_note_service(db: AsyncSession = Depends(get_db)) -> NoteService:
    return NoteService(db)
