# 1. 경로 설정 (프로젝트 루트의 data 폴더)
import os
from pathlib import Path
from app.database.default_model_mixin import Base
from typing import AsyncGenerator
from app.database.note_mng.model.note_model import NoteMetadata
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DB_PATH = BASE_DIR / "data" / "db" / "note_poc.db"

# 1. data 폴더가 없으면 생성
if not DB_PATH.parent.exists():
    os.makedirs(DB_PATH.parent)

# 2. SQLite 비동기 URL (aiosqlite 드라이버 사용)
SQLALCHEMY_DATABASE_URI = f"sqlite+aiosqlite:///{DB_PATH}"

# 3. 비동기 엔진 생성
# SQLite는 기본적으로 멀티 스레드에 엄격하므로 check_same_thread=False 설정
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URI,
    connect_args={"check_same_thread": False},
    echo=True,  # PoC 단계에서 SQL 로그 확인용
)

# 4. 세션 팩토리 생성
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


# 5. FastAPI 의존성 주입용 함수
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as sesion:
        try:
            yield sesion
            await sesion.commit()
        except Exception:
            await sesion.rollback()
            raise
        finally:
            await sesion.close()


# 7. 테이블 생성 함수
async def init_models():
    print(f"🔍 현재 Base가 인지한 테이블: {Base.metadata.tables.keys()}, DB Path: {DB_PATH}")
    async with engine.begin() as conn:
        # [중요] 여기에 모델을 임포트해야 합니다.
        # 이렇게 하면 Base가 NoteMetadata 클래스를 인지하게 됩니다.
        # 실제 테이블 생성 실행
        await conn.run_sync(Base.metadata.create_all)
    print("✅ [DB] 테이블 생성 프로세스 완료")
