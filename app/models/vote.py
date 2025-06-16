# app/models/vote.py
"""
실시간 투표 플랫폼 투표 기록 모델
사용자 투표 기록 관리
"""

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from ..database.base import Base


class Vote(Base):
    """투표 기록 모델"""
    
    __tablename__ = "votes"
    
    # 기본 정보
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    poll_id = Column(String, ForeignKey("polls.id"), nullable=False)
    option_id = Column(String, ForeignKey("poll_options.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 관계 설정
    poll = relationship("Poll", back_populates="votes")
    option = relationship("PollOption", back_populates="votes")
    user = relationship("User", back_populates="votes")
    
    # 유니크 제약 조건 (한 사용자는 한 투표에 한 번만 참여)
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )
    
    def __repr__(self):
        return f"<Vote(user_id={self.user_id}, poll_id={self.poll_id}, option_id={self.option_id})>"
    
    def to_dict(self):
        """딕셔너리 변환"""
        return {
            "id": self.id,
            "poll_id": self.poll_id,
            "option_id": self.option_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def create_vote(cls, poll_id: str, option_id: str, user_id: str):
        """새 투표 생성 클래스 메서드"""
        return cls(
            poll_id=poll_id,
            option_id=option_id,
            user_id=user_id,
            created_at=datetime.utcnow()
        )
