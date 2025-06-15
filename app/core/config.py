# app/core/config.py
"""
실시간 투표 플랫폼 백엔드 설정 관리
환경 변수 및 애플리케이션 설정을 중앙 집중화
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """애플리케이션 설정 클래스"""
    
    # 애플리케이션 기본 정보
    app_name: str = Field(default="실시간 투표 플랫폼", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    secret_key: str = Field(..., env="SECRET_KEY")
    
    # 서버 설정
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    socket_port: int = Field(default=8001, env="SOCKET_PORT")
    
    # CORS 설정
    allowed_origins: List[str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173"],
        env="ALLOWED_ORIGINS"
    )
    
    # 데이터베이스 설정
    database_url: str = Field(default="sqlite:///./voting_app.db", env="DATABASE_URL")
    database_echo: bool = Field(default=False, env="DATABASE_ECHO")
    
    # JWT 토큰 설정
    jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # 로깅 설정
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(
        default="%(levelname)s:     %(message)s", 
        env="LOG_FORMAT"
    )
    
    # WebSocket 설정
    ws_max_connections: int = Field(default=1000, env="WS_MAX_CONNECTIONS")
    ws_heartbeat_interval: int = Field(default=30, env="WS_HEARTBEAT_INTERVAL")
    
    # 개발 환경 설정
    reload: bool = Field(default=False, env="RELOAD")
    
    class Config:
        """Pydantic 설정"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


# 전역 설정 인스턴스
settings = Settings()


def get_settings() -> Settings:
    """설정 인스턴스 반환 (의존성 주입용)"""
    return settings


# 개발/프로덕션 환경 판단
def is_development() -> bool:
    """개발 환경 여부 확인"""
    return settings.debug


def is_production() -> bool:
    """프로덕션 환경 여부 확인"""
    return not settings.debug


# 데이터베이스 URL 생성
def get_database_url() -> str:
    """데이터베이스 URL 반환"""
    return settings.database_url


# CORS 설정 생성
def get_cors_origins() -> List[str]:
    """CORS 허용 원본 목록 반환"""
    if is_development():
        # 개발 환경에서는 추가 원본 허용
        return settings.allowed_origins + [
            "http://localhost:3000",
            "http://localhost:3001", 
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001"
        ]
    return settings.allowed_origins


# 로깅 설정
def get_logging_config() -> dict:
    """로깅 설정 딕셔너리 반환"""
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": settings.log_format,
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "formatter": "detailed",
                "class": "logging.FileHandler",
                "filename": "app.log",
            },
        },
        "root": {
            "level": settings.log_level,
            "handlers": ["default"] if is_development() else ["default", "file"],
        },
    }
