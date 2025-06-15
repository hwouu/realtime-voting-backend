# app/api/routes/memos.py
"""
실시간 투표 플랫폼 메모 API 라우터
사용자 메모 생성, 조회, 수정, 삭제 엔드포인트
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, or_

from ...database.session import get_db
from ...api.deps import (
    get_current_user, get_optional_current_user, get_pagination_params, 
    PaginationParams, get_sort_params, SortParams
)
from ...models.user import User
from ...models.memo import UserMemo
from ...models.poll import Poll
from ...schemas.memo import (
    MemoCreateRequest,
    MemoUpdateRequest,
    MemoResponse,
    MemoDetailResponse,
    MemoListResponse,
    MemoQueryRequest,
    MemoStatsResponse,
    MemoSearchRequest,
    MemoSearchResponse,
    MemoCreateResponse,
    MemoUpdateResponse,
    MemoDeleteResponse
)

router = APIRouter()


@router.post("/", response_model=MemoCreateResponse)
async def create_memo(
    memo_data: MemoCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    새 메모 생성
    
    Args:
        memo_data: 메모 생성 요청 데이터
        current_user: 현재 인증된 사용자
        db: 데이터베이스 세션
    
    Returns:
        MemoCreateResponse: 생성된 메모 정보
    """
    try:
        # 투표 ID가 제공된 경우 투표 존재 확인
        if memo_data.poll_id:
            poll = db.query(Poll).filter(Poll.id == memo_data.poll_id).first()
            if not poll:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="해당 투표를 찾을 수 없습니다"
                )
        
        # 새 메모 생성
        new_memo = UserMemo.create_memo(
            user_id=current_user.id,
            content=memo_data.content,
            poll_id=memo_data.poll_id
        )
        
        db.add(new_memo)
        db.commit()
        db.refresh(new_memo)
        
        # 응답 생성
        memo_response = MemoResponse(
            id=new_memo.id,
            content=new_memo.content,
            user_id=new_memo.user_id,
            poll_id=new_memo.poll_id,
            created_at=new_memo.created_at,
            updated_at=new_memo.updated_at,
            content_preview=new_memo.content_preview,
            word_count=new_memo.word_count,
            character_count=new_memo.character_count,
            is_recent=new_memo.is_recent
        )
        
        return MemoCreateResponse(memo=memo_response)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="메모 생성 중 오류가 발생했습니다"
        )


@router.get("/", response_model=MemoListResponse)
async def get_user_memos(
    pagination: PaginationParams = Depends(get_pagination_params),
    sort: SortParams = Depends(get_sort_params),
    poll_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    사용자 메모 목록 조회
    
    Args:
        pagination: 페이지네이션 파라미터
        sort: 정렬 파라미터
        poll_id: 특정 투표의 메모만 조회 (선택적)
        current_user: 현재 인증된 사용자
        db: 데이터베이스 세션
    
    Returns:
        MemoListResponse: 메모 목록
    """
    try:
        # 기본 쿼리 (현재 사용자의 메모만)
        query = db.query(UserMemo).filter(UserMemo.user_id == current_user.id)
        
        # 투표별 필터
        if poll_id:
            query = query.filter(UserMemo.poll_id == poll_id)
        
        # 전체 개수
        total = query.count()
        
        # 투표 관련 메모 개수
        poll_related_count = db.query(UserMemo)\
                              .filter(UserMemo.user_id == current_user.id)\
                              .filter(UserMemo.poll_id.isnot(None))\
                              .count()
        
        # 일반 메모 개수
        general_count = total - poll_related_count
        
        # 정렬 적용
        order_by = sort.get_order_by(UserMemo)
        if order_by is not None:
            query = query.order_by(order_by)
        else:
            query = query.order_by(desc(UserMemo.updated_at))
        
        # 페이지네이션 적용
        memos = query.offset(pagination.offset).limit(pagination.limit).all()
        
        # 응답 생성
        memo_responses = []
        for memo in memos:
            memo_responses.append(MemoResponse(
                id=memo.id,
                content=memo.content,
                user_id=memo.user_id,
                poll_id=memo.poll_id,
                created_at=memo.created_at,
                updated_at=memo.updated_at,
                content_preview=memo.content_preview,
                word_count=memo.word_count,
                character_count=memo.character_count,
                is_recent=memo.is_recent
            ))
        
        return MemoListResponse(
            memos=memo_responses,
            total=total,
            page=pagination.page,
            per_page=pagination.per_page,
            poll_related_count=poll_related_count,
            general_count=general_count
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="메모 목록 조회 중 오류가 발생했습니다"
        )


@router.get("/{memo_id}", response_model=MemoDetailResponse)
async def get_memo_detail(
    memo_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    특정 메모 상세 조회
    
    Args:
        memo_id: 메모 ID
        current_user: 현재 인증된 사용자
        db: 데이터베이스 세션
    
    Returns:
        MemoDetailResponse: 메모 상세 정보
    """
    try:
        memo = db.query(UserMemo).filter(
            UserMemo.id == memo_id,
            UserMemo.user_id == current_user.id
        ).first()
        
        if not memo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="메모를 찾을 수 없습니다"
            )
        
        # 관련 정보 조회
        user_info = {
            "id": current_user.id,
            "nickname": current_user.nickname
        }
        
        poll_info = None
        if memo.poll_id and memo.poll:
            poll_info = {
                "id": memo.poll.id,
                "title": memo.poll.title
            }
        
        return MemoDetailResponse(
            id=memo.id,
            content=memo.content,
            user_id=memo.user_id,
            poll_id=memo.poll_id,
            created_at=memo.created_at,
            updated_at=memo.updated_at,
            user=user_info,
            poll=poll_info,
            content_preview=memo.content_preview,
            word_count=memo.word_count,
            character_count=memo.character_count,
            is_recent=memo.is_recent
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="메모 조회 중 오류가 발생했습니다"
        )


@router.put("/{memo_id}", response_model=MemoUpdateResponse)
async def update_memo(
    memo_id: str,
    update_data: MemoUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    메모 수정
    
    Args:
        memo_id: 메모 ID
        update_data: 수정할 메모 데이터
        current_user: 현재 인증된 사용자
        db: 데이터베이스 세션
    
    Returns:
        MemoUpdateResponse: 수정된 메모 정보
    """
    try:
        memo = db.query(UserMemo).filter(
            UserMemo.id == memo_id,
            UserMemo.user_id == current_user.id
        ).first()
        
        if not memo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="메모를 찾을 수 없습니다"
            )
        
        # 메모 내용 업데이트
        memo.update_content(update_data.content)
        
        db.commit()
        db.refresh(memo)
        
        # 응답 생성
        memo_response = MemoResponse(
            id=memo.id,
            content=memo.content,
            user_id=memo.user_id,
            poll_id=memo.poll_id,
            created_at=memo.created_at,
            updated_at=memo.updated_at,
            content_preview=memo.content_preview,
            word_count=memo.word_count,
            character_count=memo.character_count,
            is_recent=memo.is_recent
        )
        
        return MemoUpdateResponse(memo=memo_response)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="메모 수정 중 오류가 발생했습니다"
        )


@router.delete("/{memo_id}", response_model=MemoDeleteResponse)
async def delete_memo(
    memo_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    메모 삭제
    
    Args:
        memo_id: 메모 ID
        current_user: 현재 인증된 사용자
        db: 데이터베이스 세션
    
    Returns:
        MemoDeleteResponse: 삭제 성공 응답
    """
    try:
        memo = db.query(UserMemo).filter(
            UserMemo.id == memo_id,
            UserMemo.user_id == current_user.id
        ).first()
        
        if not memo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="메모를 찾을 수 없습니다"
            )
        
        # 메모 삭제
        db.delete(memo)
        db.commit()
        
        return MemoDeleteResponse(deleted_memo_id=memo_id)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="메모 삭제 중 오류가 발생했습니다"
        )


@router.post("/search", response_model=MemoSearchResponse)
async def search_memos(
    search_request: MemoSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    메모 검색
    
    Args:
        search_request: 검색 요청 데이터
        current_user: 현재 인증된 사용자
        db: 데이터베이스 세션
    
    Returns:
        MemoSearchResponse: 검색 결과
    """
    try:
        # 기본 쿼리 (현재 사용자의 메모만)
        query = db.query(UserMemo).filter(UserMemo.user_id == current_user.id)
        
        # 검색어 필터 (내용에서 검색)
        if search_request.query:
            query = query.filter(UserMemo.content.contains(search_request.query))
        
        # 투표별 필터
        if search_request.poll_id:
            query = query.filter(UserMemo.poll_id == search_request.poll_id)
        
        # 전체 개수
        total = query.count()
        
        # 최신순 정렬
        query = query.order_by(desc(UserMemo.updated_at))
        
        # 페이지네이션 적용
        offset = (search_request.page - 1) * search_request.per_page
        memos = query.offset(offset).limit(search_request.per_page).all()
        
        # 응답 생성
        memo_responses = []
        for memo in memos:
            memo_responses.append(MemoResponse(
                id=memo.id,
                content=memo.content,
                user_id=memo.user_id,
                poll_id=memo.poll_id,
                created_at=memo.created_at,
                updated_at=memo.updated_at,
                content_preview=memo.content_preview,
                word_count=memo.word_count,
                character_count=memo.character_count,
                is_recent=memo.is_recent
            ))
        
        return MemoSearchResponse(
            results=memo_responses,
            total=total,
            query=search_request.query,
            page=search_request.page,
            per_page=search_request.per_page
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="메모 검색 중 오류가 발생했습니다"
        )


@router.get("/stats/overview", response_model=MemoStatsResponse)
async def get_memo_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    메모 통계 조회
    
    Args:
        current_user: 현재 인증된 사용자
        db: 데이터베이스 세션
    
    Returns:
        MemoStatsResponse: 메모 통계 정보
    """
    try:
        from datetime import datetime, timedelta
        
        # 전체 메모 수
        total_memos = db.query(UserMemo)\
                       .filter(UserMemo.user_id == current_user.id)\
                       .count()
        
        # 투표 관련 메모 수
        poll_related_memos = db.query(UserMemo)\
                              .filter(UserMemo.user_id == current_user.id)\
                              .filter(UserMemo.poll_id.isnot(None))\
                              .count()
        
        # 일반 메모 수
        general_memos = total_memos - poll_related_memos
        
        # 총 단어 수 (대략적 계산)
        memos = db.query(UserMemo)\
                  .filter(UserMemo.user_id == current_user.id)\
                  .all()
        
        total_words = sum(memo.word_count for memo in memos)
        total_characters = sum(memo.character_count for memo in memos)
        
        # 가장 활발한 날 찾기 (최근 30일 내)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        daily_counts = db.query(
            func.date(UserMemo.created_at).label('date'),
            func.count(UserMemo.id).label('count')
        ).filter(
            UserMemo.user_id == current_user.id,
            UserMemo.created_at >= thirty_days_ago
        ).group_by(func.date(UserMemo.created_at))\
         .order_by(desc('count'))\
         .first()
        
        most_active_day = daily_counts.date.strftime('%Y-%m-%d') if daily_counts else None
        
        # 최근 24시간 내 메모 수
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_memos_count = db.query(UserMemo)\
                              .filter(UserMemo.user_id == current_user.id)\
                              .filter(UserMemo.created_at >= yesterday)\
                              .count()
        
        return MemoStatsResponse(
            total_memos=total_memos,
            poll_related_memos=poll_related_memos,
            general_memos=general_memos,
            total_words=total_words,
            total_characters=total_characters,
            most_active_day=most_active_day,
            recent_memos_count=recent_memos_count
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="메모 통계 조회 중 오류가 발생했습니다"
        )


@router.get("/poll/{poll_id}", response_model=List[MemoResponse])
async def get_poll_memos(
    poll_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    특정 투표의 사용자 메모 조회
    
    Args:
        poll_id: 투표 ID
        current_user: 현재 인증된 사용자
        db: 데이터베이스 세션
    
    Returns:
        List[MemoResponse]: 투표 관련 메모 목록
    """
    try:
        # 투표 존재 확인
        poll = db.query(Poll).filter(Poll.id == poll_id).first()
        if not poll:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="투표를 찾을 수 없습니다"
            )
        
        # 해당 투표의 사용자 메모 조회
        memos = db.query(UserMemo)\
                  .filter(UserMemo.user_id == current_user.id)\
                  .filter(UserMemo.poll_id == poll_id)\
                  .order_by(desc(UserMemo.updated_at))\
                  .all()
        
        # 응답 생성
        memo_responses = []
        for memo in memos:
            memo_responses.append(MemoResponse(
                id=memo.id,
                content=memo.content,
                user_id=memo.user_id,
                poll_id=memo.poll_id,
                created_at=memo.created_at,
                updated_at=memo.updated_at,
                content_preview=memo.content_preview,
                word_count=memo.word_count,
                character_count=memo.character_count,
                is_recent=memo.is_recent
            ))
        
        return memo_responses
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="투표 메모 조회 중 오류가 발생했습니다"
        )


@router.get("/recent/list", response_model=List[MemoResponse])
async def get_recent_memos(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    최근 메모 목록 조회
    
    Args:
        limit: 조회할 메모 수 (기본 10개, 최대 50개)
        current_user: 현재 인증된 사용자
        db: 데이터베이스 세션
    
    Returns:
        List[MemoResponse]: 최근 메모 목록
    """
    try:
        # 제한 설정 (최대 50개)
        limit = min(max(1, limit), 50)
        
        # 최근 메모 조회
        memos = db.query(UserMemo)\
                  .filter(UserMemo.user_id == current_user.id)\
                  .order_by(desc(UserMemo.updated_at))\
                  .limit(limit)\
                  .all()
        
        # 응답 생성
        memo_responses = []
        for memo in memos:
            memo_responses.append(MemoResponse(
                id=memo.id,
                content=memo.content,
                user_id=memo.user_id,
                poll_id=memo.poll_id,
                created_at=memo.created_at,
                updated_at=memo.updated_at,
                content_preview=memo.content_preview,
                word_count=memo.word_count,
                character_count=memo.character_count,
                is_recent=memo.is_recent
            ))
        
        return memo_responses
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="최근 메모 조회 중 오류가 발생했습니다"
        )
