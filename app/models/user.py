# app/models/user.py
"""
실시간 투표 플랫폼 사용자 모델
사용자 정보, 인증, 세션 관리
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from ..database.base import Base


class User(Base):
    """사용자 모델"""
    
    __tablename__ = "users"
    
    # 기본 정보
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    nickname = Column(String(20), nullable=False, index=True)
    
    # 상태 정보
    is_online = Column(Boolean, default=True, nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 추가 정보 (선택적)
    avatar_url = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    
    # 관계 설정
    created_polls = relationship("Poll", back_populates="creator", cascade="all, delete-orphan")
    votes = relationship("Vote", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")
    memos = relationship("UserMemo", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, nickname={self.nickname}, online={self.is_online})>"
    
    def to_dict(self):
        """딕셔너리 변환 (JSON 직렬화용)"""
        return {
            "id": self.id,
            "nickname": self.nickname,
            "is_online": self.is_online,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "avatar_url": self.avatar_url,
            "bio": self.bio
        }
    
    def update_last_seen(self):
        """마지막 접속 시간 업데이트"""
        self.last_seen = datetime.utcnow()
    
    def set_online_status(self, is_online: bool):
        """온라인 상태 변경"""
        self.is_online = is_online
        if is_online:
            self.update_last_seen()
    
    @property
    def is_active(self) -> bool:
        """활성 사용자 여부"""
        if not self.last_seen:
            return False
        
        # 30분 이내 활동이 있으면 활성 사용자로 간주
        time_diff = datetime.utcnow() - self.last_seen
        return time_diff.total_seconds() < 1800  # 30분 = 1800초
    
    @classmethod
    def create_user(cls, nickname: str, **kwargs):
        """새 사용자 생성 클래스 메서드"""
        return cls(
            nickname=nickname,
            joined_at=datetime.utcnow(),
            last_seen=datetime.utcnow(),
            is_online=True,
            **kwargs
        )
