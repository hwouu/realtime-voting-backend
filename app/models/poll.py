# app/models/poll.py
"""
실시간 투표 플랫폼 투표 모델
투표, 투표 옵션, 투표 기록 관리
"""

from sqlalchemy import Column, String, Text, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from ..database.base import Base


class Poll(Base):
    """투표 모델"""
    
    __tablename__ = "polls"
    
    # 기본 정보
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # 투표 상태
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ends_at = Column(DateTime, nullable=True)  # 종료 시간 (선택적)
    
    # 작성자 정보
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    
    # 관계 설정
    creator = relationship("User", back_populates="created_polls")
    options = relationship("PollOption", back_populates="poll", cascade="all, delete-orphan")
    votes = relationship("Vote", back_populates="poll", cascade="all, delete-orphan")
    memos = relationship("UserMemo", back_populates="poll", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Poll(id={self.id}, title={self.title}, active={self.is_active})>"
    
    def to_dict(self, include_results=True):
        """딕셔너리 변환 (JSON 직렬화용)"""
        data = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "ends_at": self.ends_at.isoformat() if self.ends_at else None,
            "created_by": self.created_by
        }
        
        if include_results:
            data.update({
                "options": [option.to_dict() for option in self.options],
                "total_votes": self.total_votes
            })
        
        return data
    
    @property
    def total_votes(self) -> int:
        """전체 투표 수"""
        try:
            if not self.options:
                return 0
            return sum(option.vote_count for option in self.options)
        except Exception as e:
            print(f"Error calculating total_votes: {e}")
            return 0
    
    @property
    def is_ended(self) -> bool:
        """투표 종료 여부"""
        if not self.is_active:
            return True
        if self.ends_at and datetime.utcnow() > self.ends_at:
            return True
        return False
    
    def get_results(self) -> list:
        """투표 결과 조회"""
        total = self.total_votes
        results = []
        
        for option in self.options:
            percentage = (option.vote_count / total * 100) if total > 0 else 0
            results.append({
                "id": option.id,
                "text": option.text,
                "votes": option.vote_count,
                "percentage": round(percentage, 1)
            })
        
        return results
    
    def add_option(self, text: str) -> "PollOption":
        """투표 옵션 추가"""
        option = PollOption(
            poll_id=self.id,
            text=text
        )
        self.options.append(option)
        return option
    
    def close_poll(self):
        """투표 종료"""
        self.is_active = False
        self.ends_at = datetime.utcnow()


class PollOption(Base):
    """투표 옵션 모델"""
    
    __tablename__ = "poll_options"
    
    # 기본 정보
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    poll_id = Column(String, ForeignKey("polls.id"), nullable=False)
    text = Column(String(100), nullable=False)
    vote_count = Column(Integer, default=0, nullable=False)
    
    # 관계 설정
    poll = relationship("Poll", back_populates="options")
    votes = relationship("Vote", back_populates="option", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<PollOption(id={self.id}, text={self.text}, votes={self.vote_count})>"
    
    def to_dict(self):
        """딕셔너리 변환"""
        total_votes = self.poll.total_votes if self.poll else 0
        percentage = (self.vote_count / total_votes * 100) if total_votes > 0 else 0
        
        return {
            "id": self.id,
            "text": self.text,
            "votes": self.vote_count,
            "percentage": round(percentage, 1)
        }
    
    def increment_vote(self):
        """투표 수 증가"""
        self.vote_count += 1
    
    def decrement_vote(self):
        """투표 수 감소 (투표 변경시)"""
        if self.vote_count > 0:
            self.vote_count -= 1



