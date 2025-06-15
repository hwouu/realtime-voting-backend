# app/schemas/user.py
"""
실시간 투표 플랫폼 사용자 스키마
Pydantic 모델을 사용한 데이터 검증 및 직렬화
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import re


class UserCreateRequest(BaseModel):
    """사용자 생성 요청 스키마"""
    nickname: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="사용자 닉네임 (1-20자)"
    )
    
    @validator('nickname')
    def validate_nickname(cls, v):
        """닉네임 유효성 검증"""
        if not v or len(v.strip()) == 0:
            raise ValueError('닉네임은 필수입니다')
        
        # 공백 제거
        v = v.strip()
        
        # 길이 검증
        if len(v) > 20:
            raise ValueError('닉네임은 20자 이하여야 합니다')
        
        # 특수문자 제한
        if not re.match(r'^[a-zA-Z0-9가-힣_\s]+$', v):
            raise ValueError('닉네임에는 한글, 영문, 숫자, 언더스코어, 공백만 사용 가능합니다')
        
        return v


class UserLoginRequest(BaseModel):
    """사용자 로그인 요청 스키마"""
    nickname: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="사용자 닉네임"
    )
    
    @validator('nickname')
    def validate_nickname(cls, v):
        """닉네임 유효성 검증"""
        if not v or len(v.strip()) == 0:
            raise ValueError('닉네임은 필수입니다')
        return v.strip()


class UserResponse(BaseModel):
    """사용자 응답 스키마"""
    id: str
    nickname: str
    is_online: bool
    joined_at: datetime
    last_seen: Optional[datetime] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserBasicInfo(BaseModel):
    """사용자 기본 정보 스키마 (간소화된 버전)"""
    id: str
    nickname: str
    is_online: bool
    
    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    """사용자 정보 수정 요청 스키마"""
    nickname: Optional[str] = Field(
        None,
        min_length=1,
        max_length=20,
        description="새 닉네임"
    )
    bio: Optional[str] = Field(
        None,
        max_length=200,
        description="자기소개"
    )
    avatar_url: Optional[str] = Field(
        None,
        max_length=255,
        description="아바타 이미지 URL"
    )
    
    @validator('nickname')
    def validate_nickname(cls, v):
        """닉네임 유효성 검증"""
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                raise ValueError('닉네임은 공백일 수 없습니다')
            if not re.match(r'^[a-zA-Z0-9가-힣_\s]+$', v):
                raise ValueError('닉네임에는 한글, 영문, 숫자, 언더스코어, 공백만 사용 가능합니다')
        return v
    
    @validator('avatar_url')
    def validate_avatar_url(cls, v):
        """아바타 URL 검증"""
        if v is not None and v.strip():
            # 기본적인 URL 형식 검증
            if not v.startswith(('http://', 'https://')):
                raise ValueError('유효한 URL 형식이 아닙니다')
        return v


class UserStatusUpdate(BaseModel):
    """사용자 상태 업데이트 스키마"""
    is_online: bool
    
    class Config:
        from_attributes = True


class UserLoginResponse(BaseModel):
    """로그인 응답 스키마"""
    success: bool
    user: UserResponse
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """사용자 목록 응답 스키마"""
    users: list[UserBasicInfo]
    total: int
    online_count: int
    
    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    """사용자 프로필 응답 스키마"""
    id: str
    nickname: str
    is_online: bool
    joined_at: datetime
    last_seen: Optional[datetime] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    
    # 통계 정보
    total_polls_created: int = 0
    total_votes_cast: int = 0
    total_messages_sent: int = 0
    total_memos_written: int = 0
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# 응답 메시지 스키마들
class SuccessResponse(BaseModel):
    """성공 응답 스키마"""
    success: bool = True
    message: str
    data: Optional[dict] = None


class ErrorResponse(BaseModel):
    """에러 응답 스키마"""
    success: bool = False
    error: str
    detail: Optional[str] = None
    status_code: int
