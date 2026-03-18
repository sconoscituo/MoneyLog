"""데이터베이스 설정 및 세션 관리"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

# SQLite 전용 connect_args
_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

# 비동기 엔진 생성
engine = create_async_engine(
    settings.database_url,
    echo=settings.app_env == "development",
    connect_args=_connect_args,
)

# 세션 팩토리
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """SQLAlchemy 기본 모델 클래스"""
    pass


async def get_db() -> AsyncSession:
    """DB 세션 의존성 주입"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    """데이터베이스 테이블 초기화"""
    # 모델 임포트 (테이블 생성을 위해 필요)
    from app.models import expense, category, budget  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
