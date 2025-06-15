# app/database/base.py
"""
실시간 투표 플랫폼 데이터베이스 기본 설정
SQLAlchemy 기본 설정 및 Base 클래스 정의
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from ..core.config import settings

# 데이터베이스 엔진 생성
engine = create_engine(
    settings.database_url,
    echo=settings.database_echo,  # SQL 로그 출력 여부
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

# 세션 팩토리 생성
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 메타데이터 설정 (테이블 명명 규칙)
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }
)

# Base 클래스 생성
Base = declarative_base(metadata=metadata)
