# app/models/message.py
"""
실시간 투표 플랫폼 채팅 메시지 모델
실시간 채팅, 시스템 메시지, 투표 알림 관리
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from ..database.base import Base


class MessageType(enum.Enum):
    """메시지 유형 열거형"""
    MESSAGE = "message"        # 일반 채팅 메시지
    SYSTEM = "system"          # 시스템 알림
    VOTE_UPDATE = "vote_update"  # 투표 업데이트 알림
    USER_JOIN = "user_join"    # 사용자 입장 알림
    USER_LEAVE = "user_leave"  # 사용자 퇴장 알림
    POLL_CREATED = "poll_created"  # 새 투표 생성 알림


class ChatMessage(Base):
    """채팅 메시지 모델"""
    
    __tablename__ = "chat_messages"
    
    # 기본 정보
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    message = Column(Text, nullable=False)
    message_type = Column(Enum(MessageType), default=MessageType.MESSAGE, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 사용자 정보
    user_id = Column(String, ForeignKey("users.id"), nullable=True)  # 시스템 메시지는 null 가능
    
    # 추가 메타데이터 (JSON 형태의 추가 정보)
    message_metadata = Column(Text, nullable=True)  # JSON 문자열로 저장
    
    # 관계 설정
    user = relationship("User", back_populates="chat_messages")
    
    def __repr__(self):
        return f"<ChatMessage(id={self.id}, type={self.message_type.value}, user_id={self.user_id})>"
    
    def to_dict(self, include_user=True):
        """딕셔너리 변환 (JSON 직렬화용)"""
        data = {
            "id": self.id,
            "message": self.message,
            "type": self.message_type.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "timestamp": self.created_at.isoformat() if self.created_at else None,
            "user_id": self.user_id
        }
        
        if include_user and self.user:
            data["username"] = self.user.nickname
        elif self.message_type == MessageType.SYSTEM:
            data["username"] = "System"
        else:
            data["username"] = "Unknown"
        
        # 메타데이터 파싱 (JSON)
        if self.message_metadata:
            import json
            try:
                data["metadata"] = json.loads(self.message_metadata)
            except json.JSONDecodeError:
                data["metadata"] = None
        
        return data
    
    @classmethod
    def create_user_message(cls, user_id: str, message: str):
        """사용자 메시지 생성"""
        return cls(
            user_id=user_id,
            message=message,
            message_type=MessageType.MESSAGE,
            created_at=datetime.utcnow()
        )
    
    @classmethod
    def create_system_message(cls, message: str, metadata: dict = None):
        """시스템 메시지 생성"""
        import json
        return cls(
            user_id=None,
            message=message,
            message_type=MessageType.SYSTEM,
            message_metadata=json.dumps(metadata) if metadata else None,
            created_at=datetime.utcnow()
        )
    
    @classmethod
    def create_vote_update_message(cls, poll_title: str, user_nickname: str, option_text: str):
        """투표 업데이트 메시지 생성"""
        import json
        message = f"{user_nickname}님이 '{poll_title}' 투표에서 '{option_text}'에 투표했습니다."
        metadata = {
            "poll_title": poll_title,
            "user_nickname": user_nickname,
            "option_text": option_text
        }
        
        return cls(
            user_id=None,
            message=message,
            message_type=MessageType.VOTE_UPDATE,
            message_metadata=json.dumps(metadata),
            created_at=datetime.utcnow()
        )
    
    @classmethod
    def create_user_join_message(cls, user_nickname: str):
        """사용자 입장 메시지 생성"""
        import json
        message = f"{user_nickname}님이 입장했습니다."
        metadata = {"user_nickname": user_nickname}
        
        return cls(
            user_id=None,
            message=message,
            message_type=MessageType.USER_JOIN,
            message_metadata=json.dumps(metadata),
            created_at=datetime.utcnow()
        )
    
    @classmethod
    def create_user_leave_message(cls, user_nickname: str):
        """사용자 퇴장 메시지 생성"""
        import json
        message = f"{user_nickname}님이 퇴장했습니다."
        metadata = {"user_nickname": user_nickname}
        
        return cls(
            user_id=None,
            message=message,
            message_type=MessageType.USER_LEAVE,
            message_metadata=json.dumps(metadata),
            created_at=datetime.utcnow()
        )
    
    @classmethod
    def create_poll_created_message(cls, poll_title: str, creator_nickname: str):
        """새 투표 생성 메시지"""
        import json
        message = f"{creator_nickname}님이 새로운 투표 '{poll_title}'를 생성했습니다."
        metadata = {
            "poll_title": poll_title,
            "creator_nickname": creator_nickname
        }
        
        return cls(
            user_id=None,
            message=message,
            message_type=MessageType.POLL_CREATED,
            message_metadata=json.dumps(metadata),
            created_at=datetime.utcnow()
        )
    
    def is_user_message(self) -> bool:
        """사용자 메시지 여부"""
        return self.message_type == MessageType.MESSAGE and self.user_id is not None
    
    def is_system_message(self) -> bool:
        """시스템 메시지 여부"""
        return self.message_type != MessageType.MESSAGE
    
    def get_formatted_time(self) -> str:
        """포맷된 시간 반환"""
        if not self.created_at:
            return ""
        return self.created_at.strftime("%H:%M")
    
    def get_metadata(self) -> dict:
        """메타데이터 파싱 반환"""
        if not self.message_metadata:
            return {}
        
        import json
        try:
            return json.loads(self.message_metadata)
        except json.JSONDecodeError:
            return {}
