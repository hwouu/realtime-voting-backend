# app/api/deps.py
"""
실시간 투표 플랫폼 API 의존성 주입
FastAPI 의존성 주입 함수들을 정의
"""

from typing import Optional
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..database.session import get_db
from ..core.security import validate_token_or_raise
from ..models.user import User
from ..models.poll import Poll

# HTTP Bearer 토큰 스키마
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    현재 인증된 사용자 정보 조회
    
    Args:
        credentials: JWT Bearer 토큰
        db: 데이터베이스 세션
    
    Returns:
        User: 현재 사용자 객체
        
    Raises:
        HTTPException: 토큰이 없거나 유효하지 않은 경우
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header가 필요합니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 토큰 검증
    user_data = validate_token_or_raise(credentials.credentials)
    
    # 데이터베이스에서 사용자 조회
    user = db.query(User).filter(User.id == user_data["user_id"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    return user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    선택적 사용자 인증 (토큰이 없어도 에러를 발생시키지 않음)
    
    Args:
        credentials: JWT Bearer 토큰 (선택적)
        db: 데이터베이스 세션
    
    Returns:
        Optional[User]: 사용자 객체 또는 None
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


def get_poll_or_404(poll_id: str, db: Session = Depends(get_db)) -> Poll:
    """
    투표 조회 또는 404 에러
    
    Args:
        poll_id: 투표 ID
        db: 데이터베이스 세션
    
    Returns:
        Poll: 투표 객체
        
    Raises:
        HTTPException: 투표를 찾을 수 없는 경우
    """
    poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if not poll:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="투표를 찾을 수 없습니다"
        )
    return poll


def verify_poll_owner(poll: Poll, current_user: User) -> Poll:
    """
    투표 소유권 검증
    
    Args:
        poll: 투표 객체
        current_user: 현재 사용자
    
    Returns:
        Poll: 투표 객체
        
    Raises:
        HTTPException: 투표 소유자가 아닌 경우
    """
    if poll.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 투표를 수정할 권한이 없습니다"
        )
    return poll


def verify_active_poll(poll: Poll) -> Poll:
    """
    활성 투표 검증
    
    Args:
        poll: 투표 객체
    
    Returns:
        Poll: 투표 객체
        
    Raises:
        HTTPException: 투표가 비활성 상태인 경우
    """
    if not poll.is_active or poll.is_ended:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="종료된 투표에는 참여할 수 없습니다"
        )
    return poll


async def get_user_id_from_header(
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
) -> Optional[str]:
    """
    헤더에서 사용자 ID 추출 (WebSocket이나 간단한 인증용)
    
    Args:
        x_user_id: X-User-ID 헤더 값
    
    Returns:
        Optional[str]: 사용자 ID 또는 None
    """
    return x_user_id


# 페이지네이션 의존성
class PaginationParams:
    """페이지네이션 파라미터"""
    
    def __init__(
        self,
        page: int = 1,
        per_page: int = 20,
        max_per_page: int = 100
    ):
        self.page = max(1, page)
        self.per_page = min(max(1, per_page), max_per_page)
        self.offset = (self.page - 1) * self.per_page
    
    @property
    def limit(self) -> int:
        return self.per_page


def get_pagination_params(
    page: int = 1,
    per_page: int = 20
) -> PaginationParams:
    """페이지네이션 파라미터 생성"""
    return PaginationParams(page=page, per_page=per_page)


# 정렬 의존성
class SortParams:
    """정렬 파라미터"""
    
    def __init__(
        self,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ):
        self.sort_by = sort_by
        self.sort_order = sort_order.lower()
        
        if self.sort_order not in ["asc", "desc"]:
            self.sort_order = "desc"
    
    def get_order_by(self, model_class):
        """SQLAlchemy Order By 절 생성"""
        from sqlalchemy import asc, desc
        
        if not hasattr(model_class, self.sort_by):
            # 기본 정렬 필드로 fallback
            field = getattr(model_class, "created_at", None)
        else:
            field = getattr(model_class, self.sort_by)
        
        if field is None:
            return None
        
        return desc(field) if self.sort_order == "desc" else asc(field)


def get_sort_params(
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> SortParams:
    """정렬 파라미터 생성"""
    return SortParams(sort_by=sort_by, sort_order=sort_order)


# 검색 필터 의존성
class SearchParams:
    """검색 파라미터"""
    
    def __init__(
        self,
        query: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ):
        self.query = query.strip() if query else None
        self.date_from = date_from
        self.date_to = date_to
    
    @property
    def has_query(self) -> bool:
        return bool(self.query)
    
    @property
    def has_date_filter(self) -> bool:
        return bool(self.date_from or self.date_to)


def get_search_params(
    query: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
) -> SearchParams:
    """검색 파라미터 생성"""
    return SearchParams(
        query=query,
        date_from=date_from,
        date_to=date_to
    )
