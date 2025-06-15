# app/services/user_service.py
"""
실시간 투표 플랫폼 사용자 서비스
사용자 관련 비즈니스 로직 처리
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from ..models.user import User
from ..models.poll import Poll
from ..models.vote import Vote
from ..models.message import ChatMessage
from ..models.memo import UserMemo
from ..core.security import create_user_token, validate_nickname, sanitize_nickname


class UserService:
    """사용자 서비스 클래스"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(self, nickname: str, **kwargs) -> User:
        """
        새 사용자 생성
        
        Args:
            nickname: 사용자 닉네임
            **kwargs: 추가 사용자 정보
        
        Returns:
            User: 생성된 사용자 객체
        
        Raises:
            ValueError: 닉네임 검증 실패
            Exception: 닉네임 중복
        """
        # 닉네임 정제 및 검증
        clean_nickname = sanitize_nickname(nickname)
        if not validate_nickname(clean_nickname):
            raise ValueError("유효하지 않은 닉네임입니다")
        
        # 중복 확인
        if self.is_nickname_taken(clean_nickname):
            raise Exception("이미 사용 중인 닉네임입니다")
        
        # 사용자 생성
        user = User.create_user(nickname=clean_nickname, **kwargs)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def authenticate_user(self, nickname: str) -> Optional[User]:
        """
        사용자 인증 (닉네임 기반)
        
        Args:
            nickname: 사용자 닉네임
        
        Returns:
            Optional[User]: 인증된 사용자 또는 None
        """
        clean_nickname = sanitize_nickname(nickname)
        user = self.db.query(User).filter(User.nickname == clean_nickname).first()
        
        if user:
            # 온라인 상태 업데이트
            user.set_online_status(True)
            self.db.commit()
        
        return user
    
    def is_nickname_taken(self, nickname: str, exclude_user_id: str = None) -> bool:
        """
        닉네임 중복 확인
        
        Args:
            nickname: 확인할 닉네임
            exclude_user_id: 제외할 사용자 ID (수정시 자신 제외)
        
        Returns:
            bool: 중복 여부
        """
        query = self.db.query(User).filter(User.nickname == nickname)
        
        if exclude_user_id:
            query = query.filter(User.id != exclude_user_id)
        
        return query.first() is not None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """사용자 ID로 조회"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_nickname(self, nickname: str) -> Optional[User]:
        """닉네임으로 사용자 조회"""
        return self.db.query(User).filter(User.nickname == nickname).first()
    
    def update_user(self, user: User, **update_data) -> User:
        """
        사용자 정보 업데이트
        
        Args:
            user: 업데이트할 사용자 객체
            **update_data: 업데이트할 데이터
        
        Returns:
            User: 업데이트된 사용자 객체
        """
        for field, value in update_data.items():
            if hasattr(user, field) and value is not None:
                # 닉네임 업데이트시 검증
                if field == "nickname":
                    clean_nickname = sanitize_nickname(value)
                    if not validate_nickname(clean_nickname):
                        raise ValueError("유효하지 않은 닉네임입니다")
                    
                    if self.is_nickname_taken(clean_nickname, user.id):
                        raise Exception("이미 사용 중인 닉네임입니다")
                    
                    value = clean_nickname
                
                setattr(user, field, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_user_stats(self, user: User) -> Dict[str, Any]:
        """
        사용자 통계 정보 조회
        
        Args:
            user: 사용자 객체
        
        Returns:
            Dict[str, Any]: 사용자 통계
        """
        stats = {
            "total_polls_created": self.db.query(Poll).filter(Poll.created_by == user.id).count(),
            "total_votes_cast": self.db.query(Vote).filter(Vote.user_id == user.id).count(),
            "total_messages_sent": self.db.query(ChatMessage).filter(ChatMessage.user_id == user.id).count(),
            "total_memos_written": self.db.query(UserMemo).filter(UserMemo.user_id == user.id).count()
        }
        
        return stats
    
    def get_online_users(self) -> List[User]:
        """온라인 사용자 목록 조회"""
        return self.db.query(User).filter(User.is_online == True).all()
    
    def get_users_list(self, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """
        사용자 목록 조회 (페이지네이션)
        
        Args:
            page: 페이지 번호
            per_page: 페이지당 항목 수
        
        Returns:
            Dict[str, Any]: 사용자 목록 및 통계
        """
        offset = (page - 1) * per_page
        
        total = self.db.query(User).count()
        online_count = self.db.query(User).filter(User.is_online == True).count()
        
        users = self.db.query(User)\
                     .order_by(desc(User.last_seen))\
                     .offset(offset)\
                     .limit(per_page)\
                     .all()
        
        return {
            "users": users,
            "total": total,
            "online_count": online_count,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        }
    
    def set_user_offline(self, user: User):
        """사용자 오프라인 상태로 변경"""
        user.set_online_status(False)
        self.db.commit()
    
    def set_user_online(self, user: User):
        """사용자 온라인 상태로 변경"""
        user.set_online_status(True)
        self.db.commit()
    
    def get_user_activity_summary(self, user: User) -> Dict[str, Any]:
        """
        사용자 활동 요약 조회
        
        Args:
            user: 사용자 객체
        
        Returns:
            Dict[str, Any]: 활동 요약
        """
        from datetime import datetime, timedelta
        
        # 최근 7일간 활동
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        recent_polls = self.db.query(Poll)\
                            .filter(Poll.created_by == user.id)\
                            .filter(Poll.created_at >= week_ago)\
                            .count()
        
        recent_votes = self.db.query(Vote)\
                            .filter(Vote.user_id == user.id)\
                            .filter(Vote.created_at >= week_ago)\
                            .count()
        
        recent_messages = self.db.query(ChatMessage)\
                               .filter(ChatMessage.user_id == user.id)\
                               .filter(ChatMessage.created_at >= week_ago)\
                               .count()
        
        recent_memos = self.db.query(UserMemo)\
                            .filter(UserMemo.user_id == user.id)\
                            .filter(UserMemo.created_at >= week_ago)\
                            .count()
        
        return {
            "recent_polls": recent_polls,
            "recent_votes": recent_votes,
            "recent_messages": recent_messages,
            "recent_memos": recent_memos,
            "is_active": user.is_active,
            "last_seen": user.last_seen
        }
    
    def create_user_token(self, user: User) -> Dict[str, Any]:
        """
        사용자 JWT 토큰 생성
        
        Args:
            user: 사용자 객체
        
        Returns:
            Dict[str, Any]: 토큰 정보
        """
        return create_user_token(user.id, user.nickname)
    
    def search_users(self, query: str, limit: int = 10) -> List[User]:
        """
        사용자 검색
        
        Args:
            query: 검색 쿼리
            limit: 결과 제한
        
        Returns:
            List[User]: 검색된 사용자 목록
        """
        return self.db.query(User)\
                     .filter(User.nickname.contains(query))\
                     .order_by(func.length(User.nickname))\
                     .limit(limit)\
                     .all()
