# app/core/security.py
"""
실시간 투표 플랫폼 보안 관련 기능
JWT 토큰 생성/검증, 비밀번호 해싱 등
"""

from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt
from fastapi import HTTPException, status
from .config import settings


# 비밀번호 해싱 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
    data: dict, 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    JWT 액세스 토큰 생성
    
    Args:
        data: 토큰에 포함할 데이터 (user_id, nickname 등)
        expires_delta: 토큰 만료 시간 (기본값: 30분)
    
    Returns:
        str: JWT 토큰 문자열
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.jwt_secret_key, 
        algorithm=settings.jwt_algorithm
    )
    
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    JWT 토큰 검증 및 디코딩
    
    Args:
        token: JWT 토큰 문자열
    
    Returns:
        dict: 토큰 페이로드 (성공)
        None: 토큰 검증 실패
    """
    try:
        payload = jwt.decode(
            token, 
            settings.jwt_secret_key, 
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    비밀번호 검증
    
    Args:
        plain_password: 평문 비밀번호
        hashed_password: 해시된 비밀번호
    
    Returns:
        bool: 비밀번호 일치 여부
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    비밀번호 해시화
    
    Args:
        password: 평문 비밀번호
    
    Returns:
        str: 해시된 비밀번호
    """
    return pwd_context.hash(password)


def create_user_token(user_id: str, nickname: str) -> dict:
    """
    사용자용 토큰 생성 (편의 함수)
    
    Args:
        user_id: 사용자 ID
        nickname: 사용자 닉네임
    
    Returns:
        dict: 토큰 정보 (token, token_type, expires_in)
    """
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    
    token_data = {
        "sub": user_id,  # subject (사용자 ID)
        "nickname": nickname,
        "type": "access"
    }
    
    access_token = create_access_token(
        data=token_data, 
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60  # 초 단위
    }


def extract_user_from_token(token: str) -> Optional[dict]:
    """
    토큰에서 사용자 정보 추출
    
    Args:
        token: JWT 토큰
    
    Returns:
        dict: 사용자 정보 (user_id, nickname)
        None: 토큰 검증 실패
    """
    payload = verify_token(token)
    if not payload:
        return None
    
    user_id = payload.get("sub")
    nickname = payload.get("nickname")
    
    if not user_id or not nickname:
        return None
    
    return {
        "user_id": user_id,
        "nickname": nickname
    }


class SecurityError(Exception):
    """보안 관련 예외"""
    pass


def validate_token_or_raise(token: str) -> dict:
    """
    토큰 검증 또는 HTTP 예외 발생
    
    Args:
        token: JWT 토큰
    
    Returns:
        dict: 사용자 정보
        
    Raises:
        HTTPException: 토큰 검증 실패시 401 에러
    """
    user_data = extract_user_from_token(token)
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_data


# 토큰 유형별 생성 함수들
def create_refresh_token(user_id: str) -> str:
    """리프레시 토큰 생성 (추후 구현)"""
    data = {"sub": user_id, "type": "refresh"}
    expires_delta = timedelta(days=7)  # 7일
    return create_access_token(data, expires_delta)


def create_temporary_token(user_id: str, purpose: str) -> str:
    """임시 토큰 생성 (비밀번호 재설정 등)"""
    data = {
        "sub": user_id, 
        "type": "temporary",
        "purpose": purpose
    }
    expires_delta = timedelta(minutes=15)  # 15분
    return create_access_token(data, expires_delta)


# 닉네임 검증 함수들
def validate_nickname(nickname: str) -> bool:
    """
    닉네임 유효성 검증
    
    Args:
        nickname: 검증할 닉네임
    
    Returns:
        bool: 유효성 여부
    """
    if not nickname or len(nickname.strip()) == 0:
        return False
    
    # 길이 검증 (1-20자)
    if len(nickname) > 20:
        return False
    
    # 특수문자 제한 (기본적인 검증)
    import re
    if not re.match(r'^[a-zA-Z0-9가-힣_\s]+$', nickname):
        return False
    
    return True


def sanitize_nickname(nickname: str) -> str:
    """
    닉네임 정제 (공백 제거 등)
    
    Args:
        nickname: 원본 닉네임
    
    Returns:
        str: 정제된 닉네임
    """
    return nickname.strip()
