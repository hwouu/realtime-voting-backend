# app/schemas/memo.py
"""
실시간 투표 플랫폼 메모 스키마
사용자 메모 관련 Pydantic 모델
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime


class MemoCreateRequest(BaseModel):
    """메모 생성 요청 스키마"""
    content: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="메모 내용 (1-1000자)"
    )
    user_id: str = Field(
        ...,
        description="작성자 사용자 ID"
    )
    poll_id: Optional[str] = Field(
        None,
        description="관련 투표 ID (선택적)"
    )
    
    @validator('content')
    def validate_content(cls, v):
        """메모 내용 검증"""
        if not v or len(v.strip()) == 0:
            raise ValueError('메모 내용은 공백일 수 없습니다')
        return v.strip()


class MemoUpdateRequest(BaseModel):
    """메모 수정 요청 스키마"""
    content: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="새 메모 내용"
    )
    
    @validator('content')
    def validate_content(cls, v):
        """메모 내용 검증"""
        if not v or len(v.strip()) == 0:
            raise ValueError('메모 내용은 공백일 수 없습니다')
        return v.strip()


class MemoResponse(BaseModel):
    """메모 응답 스키마"""
    id: str
    content: str
    user_id: str
    poll_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # 추가 계산 필드들
    content_preview: Optional[str] = None
    word_count: Optional[int] = None
    character_count: Optional[int] = None
    is_recent: Optional[bool] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MemoDetailResponse(BaseModel):
    """메모 상세 응답 스키마"""
    id: str
    content: str
    user_id: str
    poll_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # 관련 정보
    user: Optional[dict] = None  # 사용자 기본 정보
    poll: Optional[dict] = None  # 투표 기본 정보
    
    # 통계 정보
    content_preview: str
    word_count: int
    character_count: int
    is_recent: bool
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MemoListResponse(BaseModel):
    """메모 목록 응답 스키마"""
    memos: List[MemoResponse]
    total: int
    page: int = 1
    per_page: int = 20
    poll_related_count: int = 0
    general_count: int = 0
    
    class Config:
        from_attributes = True


class MemoQueryRequest(BaseModel):
    """메모 조회 요청 스키마"""
    user_id: Optional[str] = Field(
        None,
        description="사용자 ID 필터"
    )
    poll_id: Optional[str] = Field(
        None,
        description="투표 ID 필터"
    )
    page: int = Field(
        default=1,
        ge=1,
        description="페이지 번호"
    )
    per_page: int = Field(
        default=20,
        ge=1,
        le=100,
        description="페이지당 항목 수 (1-100)"
    )
    include_user: bool = Field(
        default=False,
        description="사용자 정보 포함 여부"
    )
    include_poll: bool = Field(
        default=False,
        description="투표 정보 포함 여부"
    )
    sort_by: str = Field(
        default="updated_at",
        description="정렬 기준 (created_at, updated_at, content)"
    )
    sort_order: str = Field(
        default="desc",
        description="정렬 순서 (asc, desc)"
    )
    
    @validator('sort_by')
    def validate_sort_by(cls, v):
        """정렬 기준 검증"""
        allowed_fields = ['created_at', 'updated_at', 'content', 'character_count']
        if v not in allowed_fields:
            raise ValueError(f'정렬 기준은 {allowed_fields} 중 하나여야 합니다')
        return v
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        """정렬 순서 검증"""
        if v not in ['asc', 'desc']:
            raise ValueError('정렬 순서는 asc 또는 desc여야 합니다')
        return v


class MemoStatsResponse(BaseModel):
    """메모 통계 응답 스키마"""
    total_memos: int
    poll_related_memos: int
    general_memos: int
    total_words: int
    total_characters: int
    most_active_day: Optional[str] = None
    recent_memos_count: int = 0  # 최근 24시간 내 메모 수
    
    class Config:
        from_attributes = True


class MemoSearchRequest(BaseModel):
    """메모 검색 요청 스키마"""
    query: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="검색어"
    )
    user_id: Optional[str] = Field(
        None,
        description="사용자 ID 필터"
    )
    poll_id: Optional[str] = Field(
        None,
        description="투표 ID 필터"
    )
    page: int = Field(
        default=1,
        ge=1,
        description="페이지 번호"
    )
    per_page: int = Field(
        default=20,
        ge=1,
        le=50,
        description="페이지당 항목 수"
    )
    
    @validator('query')
    def validate_query(cls, v):
        """검색어 검증"""
        if not v or len(v.strip()) == 0:
            raise ValueError('검색어는 공백일 수 없습니다')
        return v.strip()


class MemoSearchResponse(BaseModel):
    """메모 검색 응답 스키마"""
    results: List[MemoResponse]
    total: int
    query: str
    page: int
    per_page: int
    
    class Config:
        from_attributes = True


# 응답 메시지 스키마들
class MemoCreateResponse(BaseModel):
    """메모 생성 응답 스키마"""
    success: bool = True
    message: str = "메모가 성공적으로 생성되었습니다"
    memo: MemoResponse
    
    class Config:
        from_attributes = True


class MemoUpdateResponse(BaseModel):
    """메모 수정 응답 스키마"""
    success: bool = True
    message: str = "메모가 성공적으로 수정되었습니다"
    memo: MemoResponse
    
    class Config:
        from_attributes = True


class MemoDeleteResponse(BaseModel):
    """메모 삭제 응답 스키마"""
    success: bool = True
    message: str = "메모가 성공적으로 삭제되었습니다"
    deleted_memo_id: str
    
    class Config:
        from_attributes = True
