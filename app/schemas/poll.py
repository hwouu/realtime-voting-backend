# app/schemas/poll.py
"""
실시간 투표 플랫폼 투표 스키마
투표, 투표 옵션, 투표 결과 관련 Pydantic 모델
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime


class PollOptionCreate(BaseModel):
    """투표 옵션 생성 스키마"""
    text: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="투표 옵션 텍스트"
    )
    
    @validator('text')
    def validate_text(cls, v):
        """옵션 텍스트 검증"""
        if not v or len(v.strip()) == 0:
            raise ValueError('투표 옵션은 공백일 수 없습니다')
        return v.strip()


class PollOptionResponse(BaseModel):
    """투표 옵션 응답 스키마"""
    id: str
    text: str
    votes: int = 0
    percentage: float = 0.0
    
    class Config:
        from_attributes = True


class PollCreateRequest(BaseModel):
    """투표 생성 요청 스키마"""
    title: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="투표 제목"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="투표 설명"
    )
    options: List[str] = Field(
        ...,
        min_items=2,
        max_items=8,
        description="투표 옵션 목록 (2-8개)"
    )
    ends_at: Optional[datetime] = Field(
        None,
        description="투표 종료 시간 (선택적)"
    )
    
    @validator('title')
    def validate_title(cls, v):
        """제목 검증"""
        if not v or len(v.strip()) == 0:
            raise ValueError('투표 제목은 필수입니다')
        return v.strip()
    
    @validator('description')
    def validate_description(cls, v):
        """설명 검증"""
        if v is not None:
            return v.strip()
        return v
    
    @validator('options')
    def validate_options(cls, v):
        """옵션 검증"""
        if not v or len(v) < 2:
            raise ValueError('최소 2개의 투표 옵션이 필요합니다')
        
        if len(v) > 8:
            raise ValueError('최대 8개의 투표 옵션만 허용됩니다')
        
        # 옵션 텍스트 정제 및 중복 제거
        cleaned_options = []
        for option in v:
            if isinstance(option, str):
                cleaned = option.strip()
                if cleaned and cleaned not in cleaned_options:
                    cleaned_options.append(cleaned)
        
        if len(cleaned_options) < 2:
            raise ValueError('유효한 투표 옵션이 2개 이상 필요합니다')
        
        return cleaned_options
    
    @validator('ends_at')
    def validate_ends_at(cls, v):
        """종료 시간 검증"""
        if v is not None and v <= datetime.utcnow():
            raise ValueError('투표 종료 시간은 현재 시간보다 이후여야 합니다')
        return v


class PollResponse(BaseModel):
    """투표 응답 스키마"""
    id: str
    title: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    ends_at: Optional[datetime] = None
    created_by: str
    options: List[PollOptionResponse]
    total_votes: int
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PollBasicInfo(BaseModel):
    """투표 기본 정보 스키마 (목록용)"""
    id: str
    title: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    created_by: str
    total_votes: int
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PollListResponse(BaseModel):
    """투표 목록 응답 스키마"""
    polls: List[PollResponse]
    total: int
    active_count: int
    
    class Config:
        from_attributes = True


class VoteRequest(BaseModel):
    """투표 참여 요청 스키마"""
    option_id: str = Field(
        ...,
        description="선택한 투표 옵션 ID"
    )
    user_id: str = Field(
        ...,
        description="투표자 사용자 ID"
    )


class VoteResponse(BaseModel):
    """투표 참여 응답 스키마"""
    success: bool
    message: str
    vote_id: Optional[str] = None
    poll_results: Optional[List[PollOptionResponse]] = None
    
    class Config:
        from_attributes = True


class PollUpdateRequest(BaseModel):
    """투표 수정 요청 스키마"""
    title: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="새 투표 제목"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="새 투표 설명"
    )
    is_active: Optional[bool] = Field(
        None,
        description="투표 활성 상태"
    )
    ends_at: Optional[datetime] = Field(
        None,
        description="새 투표 종료 시간"
    )
    
    @validator('title')
    def validate_title(cls, v):
        """제목 검증"""
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                raise ValueError('투표 제목은 공백일 수 없습니다')
        return v
    
    @validator('description')
    def validate_description(cls, v):
        """설명 검증"""
        if v is not None:
            return v.strip()
        return v


class PollResultsResponse(BaseModel):
    """투표 결과 응답 스키마"""
    poll_id: str
    poll_title: str
    total_votes: int
    results: List[PollOptionResponse]
    is_active: bool
    created_at: datetime
    ends_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PollStatsResponse(BaseModel):
    """투표 통계 응답 스키마"""
    poll_id: str
    total_votes: int
    unique_voters: int
    most_popular_option: Optional[PollOptionResponse] = None
    voting_timeline: List[dict] = []  # 시간대별 투표 현황
    
    class Config:
        from_attributes = True


# WebSocket 이벤트 스키마들
class VoteUpdateEvent(BaseModel):
    """투표 업데이트 이벤트 스키마"""
    type: str = "vote_result"
    poll_id: str
    results: List[PollOptionResponse]
    total_votes: int
    voter_nickname: Optional[str] = None
    
    class Config:
        from_attributes = True


class PollCreatedEvent(BaseModel):
    """새 투표 생성 이벤트 스키마"""
    type: str = "poll_created"
    poll: PollResponse
    creator_nickname: str
    
    class Config:
        from_attributes = True


class PollClosedEvent(BaseModel):
    """투표 종료 이벤트 스키마"""
    type: str = "poll_closed"
    poll_id: str
    poll_title: str
    final_results: List[PollOptionResponse]
    
    class Config:
        from_attributes = True
