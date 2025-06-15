# app/api/routes/chat.py
"""
실시간 투표 플랫폼 채팅 API 라우터
채팅 메시지 조회, 전송, 기록 관리 엔드포인트
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_

from ...database.session import get_db
from ...api.deps import (
    get_current_user, get_optional_current_user, get_pagination_params, PaginationParams
)
from ...models.user import User
from ...models.message import ChatMessage, MessageType
from ...schemas.chat import (
    ChatMessageCreateRequest,
    ChatMessageResponse,
    ChatMessageListResponse,
    SystemMessageCreate,
    ChatHistoryRequest,
    ChatStatsResponse
)
from ...schemas.user import SuccessResponse
from ...websocket.manager import websocket_manager

router = APIRouter()


async def broadcast_chat_message(message: ChatMessage):
    """채팅 메시지 브로드캐스트"""
    try:
        message_data = {
            "type": "chat_message_received",
            "data": message.to_dict()
        }
        await websocket_manager.broadcast_message(message_data)
    except Exception as e:
        print(f"채팅 메시지 브로드캐스트 실패: {e}")


@router.post("/messages", response_model=ChatMessageResponse)
async def send_chat_message(
    message_data: ChatMessageCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    채팅 메시지 전송
    
    Args:
        message_data: 채팅 메시지 데이터
        background_tasks: 백그라운드 작업
        current_user: 현재 인증된 사용자
        db: 데이터베이스 세션
    
    Returns:
        ChatMessageResponse: 전송된 메시지 정보
    """
    try:
        # 새 채팅 메시지 생성
        new_message = ChatMessage.create_user_message(
            user_id=current_user.id,
            message=message_data.message
        )
        
        db.add(new_message)
        db.commit()
        db.refresh(new_message)
        
        # 사용자 정보와 함께 응답 생성
        message_response = ChatMessageResponse(
            id=new_message.id,
            message=new_message.message,
            type=new_message.message_type.value,
            created_at=new_message.created_at,
            timestamp=new_message.created_at,
            user_id=new_message.user_id,
            username=current_user.nickname,
            metadata=new_message.get_metadata()
        )
        
        # 백그라운드에서 WebSocket 브로드캐스트
        background_tasks.add_task(broadcast_chat_message, new_message)
        
        return message_response
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="메시지 전송 중 오류가 발생했습니다"
        )


@router.get("/messages", response_model=ChatMessageListResponse)
async def get_chat_messages(
    pagination: PaginationParams = Depends(get_pagination_params),
    message_type: Optional[str] = None,
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    채팅 메시지 목록 조회
    
    Args:
        pagination: 페이지네이션 파라미터
        message_type: 메시지 유형 필터 (선택적)
        current_user: 현재 사용자 (선택적)
        db: 데이터베이스 세션
    
    Returns:
        ChatMessageListResponse: 채팅 메시지 목록
    """
    try:
        # 기본 쿼리 (최신순)
        query = db.query(ChatMessage).order_by(desc(ChatMessage.created_at))
        
        # 메시지 유형 필터
        if message_type:
            try:
                msg_type = MessageType(message_type)
                query = query.filter(ChatMessage.message_type == msg_type)
            except ValueError:
                pass  # 잘못된 메시지 유형은 무시
        
        # 전체 개수
        total = query.count()
        
        # 페이지네이션 적용
        messages = query.offset(pagination.offset).limit(pagination.limit).all()
        
        # 응답 생성 (사용자 정보 포함)
        message_responses = []
        for message in messages:
            message_responses.append(ChatMessageResponse.from_orm(message))
        
        return ChatMessageListResponse(
            messages=message_responses,
            total=total,
            page=pagination.page,
            per_page=pagination.per_page
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="메시지 목록 조회 중 오류가 발생했습니다"
        )


@router.get("/messages/recent", response_model=List[ChatMessageResponse])
async def get_recent_chat_messages(
    limit: int = 50,
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    최근 채팅 메시지 조회 (WebSocket 연결 시 초기 로드용)
    
    Args:
        limit: 조회할 메시지 수 (기본 50개)
        current_user: 현재 사용자 (선택적)
        db: 데이터베이스 세션
    
    Returns:
        List[ChatMessageResponse]: 최근 메시지 목록
    """
    try:
        # 제한 설정 (최대 100개)
        limit = min(max(1, limit), 100)
        
        # 최근 메시지 조회
        messages = db.query(ChatMessage)\
                    .order_by(desc(ChatMessage.created_at))\
                    .limit(limit)\
                    .all()
        
        # 시간순으로 다시 정렬 (오래된 것부터)
        messages.reverse()
        
        return [ChatMessageResponse.from_orm(message) for message in messages]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="최근 메시지 조회 중 오류가 발생했습니다"
        )


@router.post("/messages/system", response_model=ChatMessageResponse)
async def send_system_message(
    message_data: SystemMessageCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    시스템 메시지 전송 (관리자용)
    
    Args:
        message_data: 시스템 메시지 데이터
        background_tasks: 백그라운드 작업
        current_user: 현재 인증된 사용자
        db: 데이터베이스 세션
    
    Returns:
        ChatMessageResponse: 전송된 시스템 메시지
    """
    try:
        # 시스템 메시지 생성
        system_message = ChatMessage.create_system_message(
            message=message_data.message,
            metadata=message_data.metadata
        )
        
        db.add(system_message)
        db.commit()
        db.refresh(system_message)
        
        # 응답 생성
        message_response = ChatMessageResponse.from_orm(system_message)
        
        # 백그라운드에서 WebSocket 브로드캐스트
        background_tasks.add_task(broadcast_chat_message, system_message)
        
        return message_response
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="시스템 메시지 전송 중 오류가 발생했습니다"
        )


@router.get("/messages/{message_id}", response_model=ChatMessageResponse)
async def get_chat_message_detail(
    message_id: str,
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    특정 채팅 메시지 상세 조회
    
    Args:
        message_id: 메시지 ID
        current_user: 현재 사용자 (선택적)
        db: 데이터베이스 세션
    
    Returns:
        ChatMessageResponse: 메시지 상세 정보
    """
    try:
        message = db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="메시지를 찾을 수 없습니다"
            )
        
        return ChatMessageResponse.from_orm(message)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="메시지 조회 중 오류가 발생했습니다"
        )


@router.delete("/messages/{message_id}", response_model=SuccessResponse)
async def delete_chat_message(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    채팅 메시지 삭제 (작성자만 가능)
    
    Args:
        message_id: 메시지 ID
        current_user: 현재 인증된 사용자
        db: 데이터베이스 세션
    
    Returns:
        SuccessResponse: 삭제 성공 응답
    """
    try:
        message = db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="메시지를 찾을 수 없습니다"
            )
        
        # 작성자 또는 시스템 메시지만 삭제 가능
        if message.user_id and message.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="본인이 작성한 메시지만 삭제할 수 있습니다"
            )
        
        db.delete(message)
        db.commit()
        
        return SuccessResponse(
            success=True,
            message="메시지가 성공적으로 삭제되었습니다"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="메시지 삭제 중 오류가 발생했습니다"
        )


@router.get("/stats", response_model=ChatStatsResponse)
async def get_chat_stats(
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    채팅 통계 조회
    
    Args:
        current_user: 현재 사용자 (선택적)
        db: 데이터베이스 세션
    
    Returns:
        ChatStatsResponse: 채팅 통계 정보
    """
    try:
        from datetime import datetime, timedelta
        
        # 전체 메시지 수
        total_messages = db.query(ChatMessage).count()
        
        # 활성 사용자 수 (최근 24시간 내 메시지 작성자)
        yesterday = datetime.utcnow() - timedelta(days=1)
        active_users = db.query(ChatMessage.user_id)\
                        .filter(ChatMessage.created_at >= yesterday)\
                        .filter(ChatMessage.user_id.isnot(None))\
                        .distinct().count()
        
        # 오늘 메시지 수
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        messages_today = db.query(ChatMessage)\
                          .filter(ChatMessage.created_at >= today)\
                          .count()
        
        # 가장 활발한 사용자 찾기
        most_active_user = None
        user_message_count = db.query(
            ChatMessage.user_id,
            func.count(ChatMessage.id).label('message_count')
        ).filter(ChatMessage.user_id.isnot(None))\
         .group_by(ChatMessage.user_id)\
         .order_by(desc('message_count'))\
         .first()
        
        if user_message_count:
            user = db.query(User).filter(User.id == user_message_count.user_id).first()
            if user:
                most_active_user = {
                    "user_id": user.id,
                    "nickname": user.nickname,
                    "message_count": user_message_count.message_count
                }
        
        # 메시지 유형별 개수
        message_types_count = {}
        for message_type in MessageType:
            count = db.query(ChatMessage)\
                     .filter(ChatMessage.message_type == message_type)\
                     .count()
            message_types_count[message_type.value] = count
        
        return ChatStatsResponse(
            total_messages=total_messages,
            active_users=active_users,
            messages_today=messages_today,
            most_active_user=most_active_user,
            message_types_count=message_types_count
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="채팅 통계 조회 중 오류가 발생했습니다"
        )


@router.post("/history", response_model=ChatMessageListResponse)
async def get_chat_history(
    history_request: ChatHistoryRequest,
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    채팅 기록 조회 (고급 필터링)
    
    Args:
        history_request: 채팅 기록 조회 요청
        current_user: 현재 사용자 (선택적)
        db: 데이터베이스 세션
    
    Returns:
        ChatMessageListResponse: 필터링된 채팅 기록
    """
    try:
        query = db.query(ChatMessage)
        
        # before_id 필터 (특정 메시지 이전)
        if history_request.before_id:
            before_message = db.query(ChatMessage)\
                              .filter(ChatMessage.id == history_request.before_id)\
                              .first()
            if before_message:
                query = query.filter(ChatMessage.created_at < before_message.created_at)
        
        # 메시지 유형 필터
        if history_request.message_types:
            valid_types = []
            for msg_type in history_request.message_types:
                try:
                    valid_types.append(MessageType(msg_type))
                except ValueError:
                    pass
            
            if valid_types:
                query = query.filter(ChatMessage.message_type.in_(valid_types))
        
        # 최신순 정렬
        query = query.order_by(desc(ChatMessage.created_at))
        
        # 전체 개수
        total = query.count()
        
        # 제한 적용
        messages = query.limit(history_request.limit).all()
        
        return ChatMessageListResponse(
            messages=[ChatMessageResponse.from_orm(msg) for msg in messages],
            total=total,
            page=1,
            per_page=history_request.limit
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="채팅 기록 조회 중 오류가 발생했습니다"
        )
