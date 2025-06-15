# app/models/memo.py
"""
실시간 투표 플랫폼 메모 모델
사용자별 개인 메모 관리
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from ..database.base import Base


class UserMemo(Base):
    """사용자 메모 모델"""
    
    __tablename__ = "user_memos"
    
    # 기본 정보
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    content = Column(Text, nullable=False)
    
    # 관련 정보
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    poll_id = Column(String, ForeignKey("polls.id"), nullable=True)  # 투표별 메모 (선택적)
    
    # 시간 정보
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 관계 설정
    user = relationship("User", back_populates="memos")
    poll = relationship("Poll", back_populates="memos")
    
    def __repr__(self):
        return f"<UserMemo(id={self.id}, user_id={self.user_id}, poll_id={self.poll_id})>"
    
    def to_dict(self, include_user=False, include_poll=False):
        """딕셔너리 변환 (JSON 직렬화용)"""
        data = {
            "id": self.id,
            "content": self.content,
            "user_id": self.user_id,
            "poll_id": self.poll_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_user and self.user:
            data["user"] = {
                "id": self.user.id,
                "nickname": self.user.nickname
            }
        
        if include_poll and self.poll:
            data["poll"] = {
                "id": self.poll.id,
                "title": self.poll.title
            }
        
        return data
    
    def update_content(self, new_content: str):
        """메모 내용 업데이트"""
        self.content = new_content
        self.updated_at = datetime.utcnow()
    
    @property
    def content_preview(self) -> str:
        """메모 내용 미리보기 (첫 50자)"""
        if len(self.content) <= 50:
            return self.content
        return self.content[:47] + "..."
    
    @property
    def word_count(self) -> int:
        """단어 수 계산"""
        return len(self.content.split())
    
    @property
    def character_count(self) -> int:
        """글자 수 계산"""
        return len(self.content)
    
    @property
    def is_recent(self) -> bool:
        """최근 메모 여부 (1시간 이내)"""
        if not self.updated_at:
            return False
        
        time_diff = datetime.utcnow() - self.updated_at
        return time_diff.total_seconds() < 3600  # 1시간 = 3600초
    
    @classmethod
    def create_memo(cls, user_id: str, content: str, poll_id: str = None):
        """새 메모 생성 클래스 메서드"""
        return cls(
            user_id=user_id,
            content=content,
            poll_id=poll_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    @classmethod
    def create_poll_memo(cls, user_id: str, poll_id: str, content: str):
        """투표별 메모 생성"""
        return cls.create_memo(user_id=user_id, content=content, poll_id=poll_id)
    
    @classmethod
    def create_general_memo(cls, user_id: str, content: str):
        """일반 메모 생성"""
        return cls.create_memo(user_id=user_id, content=content, poll_id=None)
    
    def is_poll_memo(self) -> bool:
        """투표 관련 메모 여부"""
        return self.poll_id is not None
    
    def is_general_memo(self) -> bool:
        """일반 메모 여부"""
        return self.poll_id is None
    
    def get_formatted_created_time(self) -> str:
        """포맷된 생성 시간"""
        if not self.created_at:
            return ""
        return self.created_at.strftime("%Y-%m-%d %H:%M")
    
    def get_formatted_updated_time(self) -> str:
        """포맷된 수정 시간"""
        if not self.updated_at:
            return ""
        return self.updated_at.strftime("%Y-%m-%d %H:%M")
    
    def get_time_since_update(self) -> str:
        """수정된 지 얼마나 지났는지"""
        if not self.updated_at:
            return "알 수 없음"
        
        time_diff = datetime.utcnow() - self.updated_at
        seconds = int(time_diff.total_seconds())
        
        if seconds < 60:
            return "방금 전"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes}분 전"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"{hours}시간 전"
        else:
            days = seconds // 86400
            return f"{days}일 전"
