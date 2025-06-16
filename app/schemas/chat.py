# app/schemas/chat.py
"""
실시간 투표 플랫폼 채팅 스키마
채팅 메시지 관련 Pydantic 모델
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator


class ChatMessageCreateRequest(BaseModel):
    """채팅 메시지 생성 요청 스키마"""
    message: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="채팅 메시지 내용"
    )
    user_id: str = Field(
        ...,
        description="메시지 작성자 ID"
    )
    
    @validator('message')
    def validate_message(cls, v):
        """메시지 검증"""
        if not v or len(v.strip()) == 0:
            raise ValueError('메시지는 공백일 수 없습니다')
        return v.strip()


class ChatMessageResponse(BaseModel):
    """채팅 메시지 응답 스키마"""
    id: str
    message: str
    type: str
    created_at: datetime
    timestamp: datetime  # 프론트엔드 호환성을 위한 별칭
    user_id: Optional[str] = None
    username: str
    metadata: Optional[dict] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ChatMessageListResponse(BaseModel):
    """채팅 메시지 목록 응답 스키마"""
    messages: List[ChatMessageResponse]
    total: int
    page: int = 1
    per_page: int = 50
    
    class Config:
        from_attributes = True


class SystemMessageCreate(BaseModel):
    """시스템 메시지 생성 스키마"""
    message: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="시스템 메시지 내용"
    )
    message_type: str = Field(
        default="system",
        description="메시지 유형"
    )
    metadata: Optional[dict] = Field(
        None,
        description="메시지 메타데이터"
    )


# WebSocket 이벤트 스키마들
class ChatMessageEvent(BaseModel):
    """채팅 메시지 이벤트 스키마 (WebSocket)"""
    type: str = "chat:message_received"
    message: ChatMessageResponse
    
    class Config:
        from_attributes = True


class UserJoinEvent(BaseModel):
    """사용자 입장 이벤트 스키마"""
    type: str = "user:joined"
    user_id: str
    nickname: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserLeaveEvent(BaseModel):
    """사용자 퇴장 이벤트 스키마"""
    type: str = "user:left"
    user_id: str
    nickname: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class OnlineUsersEvent(BaseModel):
    """온라인 사용자 목록 이벤트 스키마"""
    type: str = "users:online"
    users: List[dict]  # 간소화된 사용자 정보 목록
    count: int
    
    class Config:
        from_attributes = True


class ChatHistoryRequest(BaseModel):
    """채팅 기록 조회 요청 스키마"""
    limit: int = Field(
        default=50,
        ge=1,
        le=100,
        description="조회할 메시지 수 (1-100)"
    )
    before_id: Optional[str] = Field(
        None,
        description="이 메시지 ID 이전의 메시지들 조회"
    )
    message_types: Optional[List[str]] = Field(
        None,
        description="조회할 메시지 유형 필터"
    )


class ChatStatsResponse(BaseModel):
    """채팅 통계 응답 스키마"""
    total_messages: int
    active_users: int
    messages_today: int
    most_active_user: Optional[dict] = None
    message_types_count: dict = {}
    
    class Config:
        from_attributes = True
