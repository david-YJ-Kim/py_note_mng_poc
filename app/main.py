import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from watchfiles import awatch

from app.controller.note_service_controller import note_service_controller
from app.database.note_mng.connection import init_models, get_db, AsyncSessionLocal
from app.database.note_mng.model.note_model import NoteMetadata
from app.service.git_manage_service.git_poc import GitService
from app.service.note_mng.note_mng_biz_service import NoteService, get_note_service

# 로거 설정
logger = logging.getLogger(__name__)

git_service = GitService()


# Swagger에서 입력받을 데이터 구조 정의
# class NoteSaveRequest(BaseModel):
#     title: str
#     content: str
#     user_name: str
#     last_hash: str | None = None # 클라이언트가 알고 있는 마지막 커밋 해시


# 1. Lifespan 설정 (startup/shutdown 통합 관리)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버 시작 시 실행 (startup)

    print(f"start sync Index")
    async with AsyncSessionLocal() as session:
        service = NoteService(session)
        # 별도 쓰레드나 동기 방식으로 실행
        service.sync_all_files_to_index()

    await init_models()
    print("✅ PoC용 SQLite 테이블 생성 완료")

    yield
    # ========== Shutdown (서버 종료 시) ==========
    print("🛑 서버 종료 중...")

    # 데이터베이스 연결 종료
    # await database.disconnect()

    # 백그라운드 작업 정리
    # await cleanup_background_tasks()

    # 리소스 해제
    # await close_connections()

    print("✅ 정리 작업 완료")


app = FastAPI(lifespan=lifespan)
app.include_router(note_service_controller)

if __name__ == '__main__':
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=9900, reload=True)
