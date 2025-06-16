# main.py
"""
실시간 투표 플랫폼 백엔드 메인 애플리케이션
FastAPI 서버 및 WebSocket 서버 실행
"""

import uvicorn
import asyncio
import logging
import logging.config
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.core.config import settings, get_cors_origins, get_logging_config
from app.database.session import init_db
from app.api.routes import users, polls, chat, memos
from app.websocket.manager import websocket_manager
from app.websocket.events import setup_websocket_events


# 로깅 설정
logging.config.dictConfig(get_logging_config())
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시 실행
    logger.info("🚀 실시간 투표 플랫폼 백엔드 서버 시작")
    
    # 데이터베이스 초기화
    logger.info("📊 데이터베이스 초기화 중...")
    await init_db()
    logger.info("✅ 데이터베이스 초기화 완료")
    
    # WebSocket 매니저 초기화
    app.state.websocket_manager = websocket_manager
    logger.info("🔌 WebSocket 매니저 초기화 완료")
    
    yield
    
    # 종료 시 실행
    logger.info("🛑 서버 종료 중...")
    if hasattr(app.state, 'websocket_manager'):
        await app.state.websocket_manager.cleanup()
    logger.info("👋 서버 종료 완료")


# FastAPI 애플리케이션 생성
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="WebSocket 기반 실시간 투표 및 채팅 플랫폼",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)


# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# 글로벌 예외 처리기
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """전역 예외 처리"""
    logger.error(f"글로벌 예외 발생: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "내부 서버 오류가 발생했습니다",
            "detail": str(exc) if settings.debug else "서버 오류"
        }
    )


# 기본 라우트
@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": f"🗳️ {settings.app_name} API 서버",
        "version": settings.app_version,
        "status": "healthy",
        "docs": "/docs" if settings.debug else "비활성화됨"
    }


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "timestamp": "2025-01-16T15:30:00Z",
        "environment": "development" if settings.debug else "production"
    }


# API 라우터 등록
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(polls.router, prefix="/api/polls", tags=["polls"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(memos.router, prefix="/api/memos", tags=["memos"])


# WebSocket 이벤트 설정
setup_websocket_events(app)


# 정적 파일 서빙 (개발 환경에서만)
if settings.debug:
    try:
        app.mount("/static", StaticFiles(directory="static"), name="static")
    except:
        pass  # static 디렉토리가 없으면 무시


def run_server():
    """서버 실행 함수"""
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
        access_log=settings.debug,
        workers=1 if settings.debug else 4
    )


if __name__ == "__main__":
    logger.info(f"🌟 {settings.app_name} 서버를 시작합니다...")
    logger.info(f"🔧 환경: {'개발' if settings.debug else '프로덕션'}")
    logger.info(f"🌐 주소: http://{settings.host}:{settings.port}")
    logger.info(f"📚 API 문서: http://{settings.host}:{settings.port}/docs" if settings.debug else "")
    
    run_server()
