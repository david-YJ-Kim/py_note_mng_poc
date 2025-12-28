from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.note_mng.connection import init_models, get_db
from app.database.note_mng.model.note_model import NoteMetadata
from app.service.git_manage_service.git_poc import GitService

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
async def save_note(request: NoteSaveRequest, db: AsyncSession = Depends(get_db)):
    # 여기서 Git 연동 로직과 DB 저장을 함께 수행

    file_name = f"{request.title}.md"

    try:
        # 1. Git에 파일 쓰고 커밋 (해시 반환)
        new_hash = git_service.write_and_commit(
            file_name, request.content, request.user_name, f"Save {request.title}"
        )
        
        # 2. DB에 메터 데이터 저장
        new_note = NoteMetadata(
            title=request.title,
            file_path=file_name,
            last_commit_hash=new_hash,
        )
        db.add(new_note)
        # 여기서 await db_commit()을 명시적으로 안해도 get_db의 yield 이후에 실행 됨
        return {
            "status": "success",
            "file": file_name,
            "commit_hash": new_hash,
        }
    except Exception as e:
        # 에러 발생 시 get_db에서 자동으로 rollback 처리 됨
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=9900, reload=True)