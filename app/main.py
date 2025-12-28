from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from watchfiles import awatch

from app.database.note_mng.connection import init_models, get_db
from app.database.note_mng.model.note_model import NoteMetadata
from app.service.git_manage_service.git_poc import GitService
from app.service.note_mng.note_mng_biz_service import NoteService, get_note_service

git_service = GitService()

# Swagger에서 입력받을 데이터 구조 정의
class NoteSaveRequest(BaseModel):
    title: str
    content: str
    user_name: str


# 1. Lifespan 설정 (startup/shutdown 통합 관리)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버 시작 시 실행 (startup)
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



@app.post("/notes/save")
async def save_note(request: NoteSaveRequest, service: NoteService = Depends(get_note_service)):

    try:


        # 핵심 로직 실행
        result = await service.save_or_update_note(
            title=request.title,
            content=request.content,
            user_name=request.user_name,
        )

        return {
            "status": "success",
            **result,
        }
    except Exception as e:
        # 에러 발생 시 get_db에서 자동으로 rollback 처리 됨
        print(f"❌ Error in save_note: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/notes")
async def list_notes(service: NoteService = Depends(get_note_service)):
    return await service.get_all_notes()

@app.get("/notes/{title}/history")
async def get_note_history(title: str, service: NoteService = Depends(get_note_service)):
    detail = await service.get_note_detail(title)
    if not detail:
        raise HTTPException(status_code=404, detail="Not Found")
    return detail

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=9900, reload=True)