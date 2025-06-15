# app/api/routes/polls.py
"""
실시간 투표 플랫폼 투표 API 라우터
투표 생성, 조회, 참여, 결과 확인 엔드포인트
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from ...database.session import get_db
from ...api.deps import (
    get_current_user, get_optional_current_user, get_poll_or_404,
    verify_poll_owner, verify_active_poll, get_pagination_params, PaginationParams
)
from ...models.user import User
from ...models.poll import Poll, PollOption, Vote
from ...models.message import ChatMessage
from ...schemas.poll import (
    PollCreateRequest,
    PollResponse,
    PollBasicInfo,
    PollListResponse,
    VoteRequest,
    VoteResponse,
    PollUpdateRequest,
    PollResultsResponse,
    PollStatsResponse
)
from ...schemas.user import SuccessResponse
from ...websocket.manager import websocket_manager

router = APIRouter()


async def broadcast_poll_created(poll: Poll, creator_nickname: str):
    """새 투표 생성 브로드캐스트"""
    try:
        message = {
            "type": "poll_created",
            "data": {
                "poll": poll.to_dict(),
                "creator_nickname": creator_nickname
            }
        }
        await websocket_manager.broadcast_message(message)
    except Exception as e:
        print(f"투표 생성 브로드캐스트 실패: {e}")


async def broadcast_vote_result(poll: Poll, voter_nickname: str):
    """투표 결과 브로드캐스트"""
    try:
        message = {
            "type": "vote_result",
            "data": {
                "poll_id": poll.id,
                "results": poll.get_results(),
                "total_votes": poll.total_votes,
                "voter_nickname": voter_nickname
            }
        }
        await websocket_manager.broadcast_message(message)
    except Exception as e:
        print(f"투표 결과 브로드캐스트 실패: {e}")


@router.post("/", response_model=PollResponse)
async def create_poll(
    poll_data: PollCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    새 투표 생성
    
    Args:
        poll_data: 투표 생성 요청 데이터
        background_tasks: 백그라운드 작업
        current_user: 현재 인증된 사용자
        db: 데이터베이스 세션
    
    Returns:
        PollResponse: 생성된 투표 정보
    """
    try:
        # 새 투표 생성
        new_poll = Poll(
            title=poll_data.title,
            description=poll_data.description,
            created_by=current_user.id,
            ends_at=poll_data.ends_at,
            is_active=True
        )
        
        db.add(new_poll)
        db.commit()
        db.refresh(new_poll)
        
        # 투표 옵션 생성
        for option_text in poll_data.options:
            option = PollOption(
                poll_id=new_poll.id,
                text=option_text
            )
            db.add(option)
        
        db.commit()
        
        # 옵션들 다시 로드
        db.refresh(new_poll)
        
        # 채팅 시스템 메시지 생성
        system_message = ChatMessage.create_poll_created_message(
            poll_title=new_poll.title,
            creator_nickname=current_user.nickname
        )
        db.add(system_message)
        db.commit()
        
        # 백그라운드에서 WebSocket 브로드캐스트
        background_tasks.add_task(
            broadcast_poll_created,
            new_poll,
            current_user.nickname
        )
        
        return PollResponse.from_orm(new_poll)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="투표 생성 중 오류가 발생했습니다"
        )


@router.get("/", response_model=PollListResponse)
async def get_polls_list(
    pagination: PaginationParams = Depends(get_pagination_params),
    active_only: bool = False,
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    투표 목록 조회
    
    Args:
        pagination: 페이지네이션 파라미터
        active_only: 활성 투표만 조회할지 여부
        current_user: 현재 사용자 (선택적)
        db: 데이터베이스 세션
    
    Returns:
        PollListResponse: 투표 목록
    """
    try:
        # 기본 쿼리
        query = db.query(Poll)
        
        # 활성 투표만 필터링
        if active_only:
            query = query.filter(Poll.is_active == True)
        
        # 전체 개수
        total = query.count()
        
        # 활성 투표 개수
        active_count = db.query(Poll).filter(Poll.is_active == True).count()
        
        # 최신순으로 정렬하여 조회
        polls = query.order_by(desc(Poll.created_at))\
                    .offset(pagination.offset)\
                    .limit(pagination.limit)\
                    .all()
        
        # 응답 생성
        poll_responses = [PollResponse.from_orm(poll) for poll in polls]
        
        return PollListResponse(
            polls=poll_responses,
            total=total,
            active_count=active_count
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="투표 목록 조회 중 오류가 발생했습니다"
        )


@router.get("/{poll_id}", response_model=PollResponse)
async def get_poll_detail(
    poll: Poll = Depends(get_poll_or_404),
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    특정 투표 상세 조회
    
    Args:
        poll: 조회할 투표 객체
        current_user: 현재 사용자 (선택적)
        db: 데이터베이스 세션
    
    Returns:
        PollResponse: 투표 상세 정보
    """
    try:
        return PollResponse.from_orm(poll)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="투표 조회 중 오류가 발생했습니다"
        )


@router.post("/{poll_id}/vote", response_model=VoteResponse)
async def vote_on_poll(
    poll_id: str,
    vote_data: VoteRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    투표 참여
    
    Args:
        poll_id: 투표 ID
        vote_data: 투표 요청 데이터
        background_tasks: 백그라운드 작업
        current_user: 현재 인증된 사용자
        db: 데이터베이스 세션
    
    Returns:
        VoteResponse: 투표 결과
    """
    try:
        # 투표 조회 및 검증
        poll = get_poll_or_404(poll_id, db)
        verify_active_poll(poll)
        
        # 투표 옵션 검증
        option = db.query(PollOption).filter(
            PollOption.id == vote_data.option_id,
            PollOption.poll_id == poll_id
        ).first()
        
        if not option:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="투표 옵션을 찾을 수 없습니다"
            )
        
        # 기존 투표 확인
        existing_vote = db.query(Vote).filter(
            Vote.poll_id == poll_id,
            Vote.user_id == current_user.id
        ).first()
        
        if existing_vote:
            # 기존 투표가 있으면 변경
            old_option = db.query(PollOption).filter(
                PollOption.id == existing_vote.option_id
            ).first()
            
            if old_option:
                old_option.decrement_vote()
            
            # 새 옵션으로 변경
            existing_vote.option_id = vote_data.option_id
            option.increment_vote()
            
            message = "투표가 변경되었습니다"
            vote_id = existing_vote.id
        else:
            # 새 투표 생성
            new_vote = Vote.create_vote(
                poll_id=poll_id,
                option_id=vote_data.option_id,
                user_id=current_user.id
            )
            
            db.add(new_vote)
            option.increment_vote()
            
            message = "투표가 완료되었습니다"
            vote_id = new_vote.id
        
        db.commit()
        
        # 투표 결과 갱신
        db.refresh(poll)
        poll_results = poll.get_results()
        
        # 채팅 시스템 메시지 생성
        vote_message = ChatMessage.create_vote_update_message(
            poll_title=poll.title,
            user_nickname=current_user.nickname,
            option_text=option.text
        )
        db.add(vote_message)
        db.commit()
        
        # 백그라운드에서 WebSocket 브로드캐스트
        background_tasks.add_task(
            broadcast_vote_result,
            poll,
            current_user.nickname
        )
        
        return VoteResponse(
            success=True,
            message=message,
            vote_id=vote_id,
            poll_results=poll_results
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="투표 중 오류가 발생했습니다"
        )


@router.get("/{poll_id}/results", response_model=PollResultsResponse)
async def get_poll_results(
    poll: Poll = Depends(get_poll_or_404),
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    투표 결과 조회
    
    Args:
        poll: 투표 객체
        current_user: 현재 사용자 (선택적)
        db: 데이터베이스 세션
    
    Returns:
        PollResultsResponse: 투표 결과
    """
    try:
        results = poll.get_results()
        
        return PollResultsResponse(
            poll_id=poll.id,
            poll_title=poll.title,
            total_votes=poll.total_votes,
            results=results,
            is_active=poll.is_active,
            created_at=poll.created_at,
            ends_at=poll.ends_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="투표 결과 조회 중 오류가 발생했습니다"
        )


@router.put("/{poll_id}", response_model=PollResponse)
async def update_poll(
    poll_id: str,
    update_data: PollUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    투표 정보 수정
    
    Args:
        poll_id: 투표 ID
        update_data: 수정할 투표 정보
        current_user: 현재 인증된 사용자
        db: 데이터베이스 세션
    
    Returns:
        PollResponse: 수정된 투표 정보
    """
    try:
        poll = get_poll_or_404(poll_id, db)
        verify_poll_owner(poll, current_user)
        
        # 수정 가능한 필드 업데이트
        if update_data.title is not None:
            poll.title = update_data.title
        
        if update_data.description is not None:
            poll.description = update_data.description
        
        if update_data.is_active is not None:
            poll.is_active = update_data.is_active
        
        if update_data.ends_at is not None:
            poll.ends_at = update_data.ends_at
        
        db.commit()
        db.refresh(poll)
        
        return PollResponse.from_orm(poll)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="투표 수정 중 오류가 발생했습니다"
        )


@router.delete("/{poll_id}", response_model=SuccessResponse)
async def delete_poll(
    poll_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    투표 삭제
    
    Args:
        poll_id: 투표 ID
        current_user: 현재 인증된 사용자
        db: 데이터베이스 세션
    
    Returns:
        SuccessResponse: 삭제 성공 응답
    """
    try:
        poll = get_poll_or_404(poll_id, db)
        verify_poll_owner(poll, current_user)
        
        # 투표 삭제 (cascade로 관련 데이터도 함께 삭제됨)
        db.delete(poll)
        db.commit()
        
        return SuccessResponse(
            success=True,
            message="투표가 성공적으로 삭제되었습니다"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="투표 삭제 중 오류가 발생했습니다"
        )


@router.post("/{poll_id}/close", response_model=PollResponse)
async def close_poll(
    poll_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    투표 종료
    
    Args:
        poll_id: 투표 ID
        current_user: 현재 인증된 사용자
        db: 데이터베이스 세션
    
    Returns:
        PollResponse: 종료된 투표 정보
    """
    try:
        poll = get_poll_or_404(poll_id, db)
        verify_poll_owner(poll, current_user)
        
        # 투표 종료
        poll.close_poll()
        db.commit()
        db.refresh(poll)
        
        return PollResponse.from_orm(poll)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="투표 종료 중 오류가 발생했습니다"
        )


@router.get("/{poll_id}/stats", response_model=PollStatsResponse)
async def get_poll_stats(
    poll: Poll = Depends(get_poll_or_404),
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    투표 통계 조회
    
    Args:
        poll: 투표 객체
        current_user: 현재 사용자 (선택적)
        db: 데이터베이스 세션
    
    Returns:
        PollStatsResponse: 투표 통계 정보
    """
    try:
        # 고유 투표자 수 계산
        unique_voters = db.query(Vote.user_id).filter(Vote.poll_id == poll.id).distinct().count()
        
        # 가장 인기 있는 옵션 찾기
        most_popular_option = None
        if poll.options:
            most_popular = max(poll.options, key=lambda opt: opt.vote_count)
            if most_popular.vote_count > 0:
                most_popular_option = most_popular.to_dict()
        
        # 시간대별 투표 현황 (간단한 버전)
        voting_timeline = []
        
        return PollStatsResponse(
            poll_id=poll.id,
            total_votes=poll.total_votes,
            unique_voters=unique_voters,
            most_popular_option=most_popular_option,
            voting_timeline=voting_timeline
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="투표 통계 조회 중 오류가 발생했습니다"
        )


@router.get("/user/{user_id}", response_model=List[PollBasicInfo])
async def get_user_polls(
    user_id: str,
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    특정 사용자가 생성한 투표 목록 조회
    
    Args:
        user_id: 사용자 ID
        pagination: 페이지네이션 파라미터
        current_user: 현재 사용자 (선택적)
        db: 데이터베이스 세션
    
    Returns:
        List[PollBasicInfo]: 사용자 투표 목록
    """
    try:
        # 사용자 존재 확인
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다"
            )
        
        # 사용자가 생성한 투표 조회
        polls = db.query(Poll)\
                  .filter(Poll.created_by == user_id)\
                  .order_by(desc(Poll.created_at))\
                  .offset(pagination.offset)\
                  .limit(pagination.limit)\
                  .all()
        
        return [PollBasicInfo.from_orm(poll) for poll in polls]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 투표 목록 조회 중 오류가 발생했습니다"
        )
