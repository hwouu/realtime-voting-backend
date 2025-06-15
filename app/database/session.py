# app/database/session.py
"""
실시간 투표 플랫폼 데이터베이스 세션 관리
데이터베이스 연결, 세션 생성, 초기화 관리
"""

import logging
from typing import Generator, AsyncGenerator
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from .base import Base, engine, SessionLocal
from ..core.config import settings
from ..models import user, poll, message, memo  # 모든 모델 임포트

logger = logging.getLogger(__name__)


# 동기 세션 팩토리
def get_db() -> Generator[Session, None, None]:
    """
    데이터베이스 세션 의존성 주입용 함수
    FastAPI의 Depends에서 사용
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"데이터베이스 세션 오류: {e}")
        db.rollback()
        raise
    finally:
        db.close()


# 비동기 세션 팩토리 (WebSocket용)
async_engine = None
AsyncSessionLocal = None

if "sqlite" in settings.database_url:
    # SQLite용 비동기 엔진
    async_database_url = settings.database_url.replace("sqlite://", "sqlite+aiosqlite://")
    async_engine = create_async_engine(
        async_database_url,
        echo=settings.database_echo,
        poolclass=StaticPool,
        connect_args={
            "check_same_thread": False,
        },
    )
else:
    # PostgreSQL/MySQL용 비동기 엔진
    async_engine = create_async_engine(
        settings.database_url,
        echo=settings.database_echo,
    )

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """비동기 데이터베이스 세션 생성"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"비동기 데이터베이스 세션 오류: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


def create_db_and_tables():
    """데이터베이스 및 테이블 생성 (동기)"""
    try:
        logger.info("📊 데이터베이스 테이블 생성 중...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ 데이터베이스 테이블 생성 완료")
    except Exception as e:
        logger.error(f"❌ 데이터베이스 테이블 생성 실패: {e}")
        raise


async def create_async_db_and_tables():
    """비동기 데이터베이스 및 테이블 생성"""
    try:
        logger.info("📊 비동기 데이터베이스 테이블 생성 중...")
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ 비동기 데이터베이스 테이블 생성 완료")
    except Exception as e:
        logger.error(f"❌ 비동기 데이터베이스 테이블 생성 실패: {e}")
        raise


async def init_db():
    """데이터베이스 초기화"""
    try:
        # 동기 테이블 생성
        create_db_and_tables()
        
        # 비동기 테이블 생성 (WebSocket용)
        if async_engine:
            await create_async_db_and_tables()
        
        # 초기 데이터 생성
        await create_initial_data()
        
        logger.info("🎉 데이터베이스 초기화 완료")
        
    except Exception as e:
        logger.error(f"❌ 데이터베이스 초기화 실패: {e}")
        raise


async def create_initial_data():
    """초기 데이터 생성"""
    try:
        from ..models.user import User
        from ..models.poll import Poll, PollOption
        
        # 동기 세션으로 초기 데이터 확인
        db = SessionLocal()
        
        # 기존 사용자 확인
        existing_users = db.query(User).count()
        if existing_users == 0:
            logger.info("🔧 초기 데모 데이터 생성 중...")
            
            # 데모 사용자 생성
            demo_user = User.create_user(
                nickname="시스템",
                bio="실시간 투표 플랫폼 시스템 계정"
            )
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)
            
            # 데모 투표 생성
            demo_poll = Poll(
                title="점심 메뉴 투표",
                description="오늘 점심으로 무엇을 먹을까요?",
                created_by=demo_user.id,
                is_active=True
            )
            db.add(demo_poll)
            db.commit()
            db.refresh(demo_poll)
            
            # 투표 옵션 생성
            options = ["한식", "중식", "일식", "양식"]
            for option_text in options:
                option = PollOption(
                    poll_id=demo_poll.id,
                    text=option_text
                )
                db.add(option)
            
            db.commit()
            logger.info("✅ 초기 데모 데이터 생성 완료")
        
        db.close()
        
    except Exception as e:
        logger.error(f"❌ 초기 데이터 생성 실패: {e}")
        # 실패해도 서버 시작을 막지 않음
        pass


def reset_database():
    """데이터베이스 초기화 (개발용)"""
    try:
        logger.warning("⚠️ 데이터베이스 리셋 중... 모든 데이터가 삭제됩니다!")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        logger.info("🔄 데이터베이스 리셋 완료")
    except Exception as e:
        logger.error(f"❌ 데이터베이스 리셋 실패: {e}")
        raise


# SQLite 외래 키 제약 조건 활성화
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """SQLite 외래 키 제약 조건 활성화"""
    if "sqlite" in str(dbapi_connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# 데이터베이스 연결 테스트
def test_connection():
    """데이터베이스 연결 테스트"""
    try:
        db = SessionLocal()
        # 간단한 쿼리 실행
        result = db.execute("SELECT 1").fetchone()
        db.close()
        
        if result:
            logger.info("✅ 데이터베이스 연결 테스트 성공")
            return True
        else:
            logger.error("❌ 데이터베이스 연결 테스트 실패")
            return False
            
    except Exception as e:
        logger.error(f"❌ 데이터베이스 연결 테스트 오류: {e}")
        return False


# 개발용 유틸리티 함수들
def get_db_info():
    """데이터베이스 정보 조회"""
    try:
        from ..models.user import User
        from ..models.poll import Poll
        from ..models.message import ChatMessage
        
        db = SessionLocal()
        
        info = {
            "database_url": settings.database_url,
            "total_users": db.query(User).count(),
            "total_polls": db.query(Poll).count(),
            "total_messages": db.query(ChatMessage).count(),
            "active_polls": db.query(Poll).filter(Poll.is_active == True).count(),
            "online_users": db.query(User).filter(User.is_online == True).count(),
        }
        
        db.close()
        return info
        
    except Exception as e:
        logger.error(f"데이터베이스 정보 조회 실패: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    # 직접 실행시 데이터베이스 초기화
    import asyncio
    
    async def main():
        await init_db()
        print("데이터베이스 초기화 완료!")
        print("데이터베이스 정보:", get_db_info())
    
    asyncio.run(main())
