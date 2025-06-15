# app/services/chat_service.py
"""
실시간 투표 플랫폼 채팅 서비스
채팅 메시지 관련 비즈니스 로직 처리
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime, timedelta

from ..models.message import ChatMessage, MessageType
from ..models.user import User


class ChatService:
    """채팅 서비스 클래스"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_user_message(self, user_id: str, message: str) -> ChatMessage:
        """
        사용자 채팅 메시지 생성
        
        Args:
            user_id: 사용자 ID
            message: 메시지 내용
        
        Returns:
            ChatMessage: 생성된 메시지 객체
        """
        new_message = ChatMessage.create_user_message(user_id, message)
        self.db.add(new_message)
        self.db.commit()
        self.db.refresh(new_message)
        return new_message
    
    def create_system_message(self, message: str, metadata: Dict[str, Any] = None) -> ChatMessage:
        """
        시스템 메시지 생성
        
        Args:
            message: 메시지 내용
            metadata: 추가 메타데이터
        
        Returns:
            ChatMessage: 생성된 시스템 메시지 객체
        """
        system_message = ChatMessage.create_system_message(message, metadata)
        self.db.add(system_message)
        self.db.commit()
        self.db.refresh(system_message)
        return system_message
    
    def get_messages_list(
        self, 
        page: int = 1, 
        per_page: int = 50,
        message_type: Optional[MessageType] = None
    ) -> Dict[str, Any]:
        """
        채팅 메시지 목록 조회
        
        Args:
            page: 페이지 번호
            per_page: 페이지당 항목 수
            message_type: 메시지 유형 필터
        
        Returns:
            Dict[str, Any]: 메시지 목록 및 통계
        """
        offset = (page - 1) * per_page
        
        query = self.db.query(ChatMessage).order_by(desc(ChatMessage.created_at))
        
        if message_type:
            query = query.filter(ChatMessage.message_type == message_type)
        
        total = query.count()
        messages = query.offset(offset).limit(per_page).all()
        
        return {
            "messages": messages,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        }
    
    def get_recent_messages(self, limit: int = 50) -> List[ChatMessage]:
        """
        최근 채팅 메시지 조회
        
        Args:
            limit: 조회할 메시지 수
        
        Returns:
            List[ChatMessage]: 최근 메시지 목록
        """
        return self.db.query(ChatMessage)\
                     .order_by(desc(ChatMessage.created_at))\
                     .limit(limit)\
                     .all()
    
    def get_message_by_id(self, message_id: str) -> Optional[ChatMessage]:
        """메시지 ID로 조회"""
        return self.db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
    
    def delete_message(self, message: ChatMessage):
        """메시지 삭제"""
        self.db.delete(message)
        self.db.commit()
    
    def get_chat_stats(self) -> Dict[str, Any]:
        """
        채팅 통계 조회
        
        Returns:
            Dict[str, Any]: 채팅 통계 정보
        """
        # 전체 메시지 수
        total_messages = self.db.query(ChatMessage).count()
        
        # 최근 24시간 내 활성 사용자
        yesterday = datetime.utcnow() - timedelta(days=1)
        active_users = self.db.query(ChatMessage.user_id)\
                             .filter(ChatMessage.created_at >= yesterday)\
                             .filter(ChatMessage.user_id.isnot(None))\
                             .distinct().count()
        
        # 오늘 메시지 수
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        messages_today = self.db.query(ChatMessage)\
                               .filter(ChatMessage.created_at >= today)\
                               .count()
        
        # 가장 활발한 사용자
        most_active_user = None
        user_message_count = self.db.query(
            ChatMessage.user_id,
            func.count(ChatMessage.id).label('message_count')
        ).filter(ChatMessage.user_id.isnot(None))\
         .group_by(ChatMessage.user_id)\
         .order_by(desc('message_count'))\
         .first()
        
        if user_message_count:
            user = self.db.query(User).filter(User.id == user_message_count.user_id).first()
            if user:
                most_active_user = {
                    "user_id": user.id,
                    "nickname": user.nickname,
                    "message_count": user_message_count.message_count
                }
        
        # 메시지 유형별 개수
        message_types_count = {}
        for message_type in MessageType:
            count = self.db.query(ChatMessage)\
                          .filter(ChatMessage.message_type == message_type)\
                          .count()
            message_types_count[message_type.value] = count
        
        return {
            "total_messages": total_messages,
            "active_users": active_users,
            "messages_today": messages_today,
            "most_active_user": most_active_user,
            "message_types_count": message_types_count
        }
    
    def get_user_messages(self, user_id: str, limit: int = 100) -> List[ChatMessage]:
        """
        특정 사용자의 메시지 조회
        
        Args:
            user_id: 사용자 ID
            limit: 조회할 메시지 수
        
        Returns:
            List[ChatMessage]: 사용자 메시지 목록
        """
        return self.db.query(ChatMessage)\
                     .filter(ChatMessage.user_id == user_id)\
                     .order_by(desc(ChatMessage.created_at))\
                     .limit(limit)\
                     .all()
    
    def search_messages(self, query: str, limit: int = 50) -> List[ChatMessage]:
        """
        메시지 검색
        
        Args:
            query: 검색 쿼리
            limit: 결과 제한
        
        Returns:
            List[ChatMessage]: 검색된 메시지 목록
        """
        return self.db.query(ChatMessage)\
                     .filter(ChatMessage.message.contains(query))\
                     .order_by(desc(ChatMessage.created_at))\
                     .limit(limit)\
                     .all()
    
    def get_message_history(
        self, 
        before_id: Optional[str] = None,
        message_types: Optional[List[MessageType]] = None,
        limit: int = 50
    ) -> List[ChatMessage]:
        """
        채팅 기록 조회 (고급 필터링)
        
        Args:
            before_id: 이 메시지 ID 이전의 메시지들
            message_types: 메시지 유형 필터
            limit: 결과 제한
        
        Returns:
            List[ChatMessage]: 필터링된 메시지 목록
        """
        query = self.db.query(ChatMessage)
        
        # before_id 필터
        if before_id:
            before_message = self.get_message_by_id(before_id)
            if before_message:
                query = query.filter(ChatMessage.created_at < before_message.created_at)
        
        # 메시지 유형 필터
        if message_types:
            query = query.filter(ChatMessage.message_type.in_(message_types))
        
        return query.order_by(desc(ChatMessage.created_at))\
                   .limit(limit)\
                   .all()
    
    def create_vote_update_message(self, poll_title: str, user_nickname: str, option_text: str) -> ChatMessage:
        """투표 업데이트 시스템 메시지 생성"""
        message = ChatMessage.create_vote_update_message(poll_title, user_nickname, option_text)
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message
    
    def create_user_join_message(self, user_nickname: str) -> ChatMessage:
        """사용자 입장 시스템 메시지 생성"""
        message = ChatMessage.create_user_join_message(user_nickname)
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message
    
    def create_user_leave_message(self, user_nickname: str) -> ChatMessage:
        """사용자 퇴장 시스템 메시지 생성"""
        message = ChatMessage.create_user_leave_message(user_nickname)
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message
    
    def create_poll_created_message(self, poll_title: str, creator_nickname: str) -> ChatMessage:
        """새 투표 생성 시스템 메시지 생성"""
        message = ChatMessage.create_poll_created_message(poll_title, creator_nickname)
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message
    
    def get_daily_message_stats(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        일별 메시지 통계 조회
        
        Args:
            days: 조회할 일 수
        
        Returns:
            List[Dict[str, Any]]: 일별 통계
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        daily_stats = self.db.query(
            func.date(ChatMessage.created_at).label('date'),
            func.count(ChatMessage.id).label('message_count'),
            func.count(func.distinct(ChatMessage.user_id)).label('active_users')
        ).filter(ChatMessage.created_at >= start_date)\
         .group_by(func.date(ChatMessage.created_at))\
         .order_by('date')\
         .all()
        
        return [
            {
                "date": stat.date.strftime('%Y-%m-%d'),
                "message_count": stat.message_count,
                "active_users": stat.active_users
            }
            for stat in daily_stats
        ]
