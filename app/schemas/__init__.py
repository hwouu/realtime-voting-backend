# app/schemas/__init__.py
"""
실시간 투표 플랫폼 스키마 패키지
모든 Pydantic 스키마를 중앙에서 관리
"""

# 사용자 스키마
from .user import (
    UserCreateRequest,
    UserLoginRequest,
    UserResponse,
    UserBasicInfo,
    UserUpdateRequest,
    UserStatusUpdate,
    UserLoginResponse,
    UserListResponse,
    UserProfileResponse,
    SuccessResponse,
    ErrorResponse
)

# 투표 스키마
from .poll import (
    PollOptionCreate,
    PollOptionResponse,
    PollCreateRequest,
    PollResponse,
    PollBasicInfo,
    PollListResponse,
    VoteRequest,
    VoteResponse,
    PollUpdateRequest,
    PollResultsResponse,
    PollStatsResponse,
    VoteUpdateEvent,
    PollCreatedEvent,
    PollClosedEvent
)

# 채팅 스키마
from .chat import (
    ChatMessageCreateRequest,
    ChatMessageResponse,
    ChatMessageListResponse,
    SystemMessageCreate,
    ChatMessageEvent,
    UserJoinEvent,
    UserLeaveEvent,
    OnlineUsersEvent,
    ChatHistoryRequest,
    ChatStatsResponse
)

# 메모 스키마
from .memo import (
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

# 모든 스키마 export
__all__ = [
    # 사용자 스키마
    "UserCreateRequest",
    "UserLoginRequest",
    "UserResponse",
    "UserBasicInfo",
    "UserUpdateRequest",
    "UserStatusUpdate",
    "UserLoginResponse",
    "UserListResponse",
    "UserProfileResponse",
    "SuccessResponse",
    "ErrorResponse",
    
    # 투표 스키마
    "PollOptionCreate",
    "PollOptionResponse",
    "PollCreateRequest",
    "PollResponse",
    "PollBasicInfo",
    "PollListResponse",
    "VoteRequest",
    "VoteResponse",
    "PollUpdateRequest",
    "PollResultsResponse",
    "PollStatsResponse",
    "VoteUpdateEvent",
    "PollCreatedEvent",
    "PollClosedEvent",
    
    # 채팅 스키마
    "ChatMessageCreateRequest",
    "ChatMessageResponse",
    "ChatMessageListResponse",
    "SystemMessageCreate",
    "ChatMessageEvent",
    "UserJoinEvent",
    "UserLeaveEvent",
    "OnlineUsersEvent",
    "ChatHistoryRequest",
    "ChatStatsResponse",
    
    # 메모 스키마
    "MemoCreateRequest",
    "MemoUpdateRequest",
    "MemoResponse",
    "MemoDetailResponse",
    "MemoListResponse",
    "MemoQueryRequest",
    "MemoStatsResponse",
    "MemoSearchRequest",
    "MemoSearchResponse",
    "MemoCreateResponse",
    "MemoUpdateResponse",
    "MemoDeleteResponse"
]
