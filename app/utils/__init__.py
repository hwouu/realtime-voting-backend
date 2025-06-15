# app/utils/__init__.py
"""
실시간 투표 플랫폼 유틸리티 패키지
공통 유틸리티 함수들을 관리
"""

from .helpers import (
    generate_unique_id,
    validate_email,
    validate_url,
    sanitize_html,
    format_datetime,
    calculate_percentage,
    paginate_query,
    create_response
)

from .validators import (
    validate_poll_data,
    validate_user_data,
    validate_memo_data,
    validate_chat_message
)

from .constants import (
    MAX_POLL_OPTIONS,
    MAX_POLL_TITLE_LENGTH,
    MAX_MESSAGE_LENGTH,
    MAX_MEMO_LENGTH,
    MAX_NICKNAME_LENGTH,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE
)

__all__ = [
    # 헬퍼 함수들
    "generate_unique_id",
    "validate_email",
    "validate_url", 
    "sanitize_html",
    "format_datetime",
    "calculate_percentage",
    "paginate_query",
    "create_response",
    
    # 검증 함수들
    "validate_poll_data",
    "validate_user_data",
    "validate_memo_data",
    "validate_chat_message",
    
    # 상수들
    "MAX_POLL_OPTIONS",
    "MAX_POLL_TITLE_LENGTH",
    "MAX_MESSAGE_LENGTH",
    "MAX_MEMO_LENGTH",
    "MAX_NICKNAME_LENGTH",
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE"
]
