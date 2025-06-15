# app/utils/constants.py
"""
실시간 투표 플랫폼 상수 정의
애플리케이션 전체에서 사용되는 상수들을 정의
"""

# 투표 관련 상수
MAX_POLL_OPTIONS = 8
MIN_POLL_OPTIONS = 2
MAX_POLL_TITLE_LENGTH = 100
MAX_POLL_DESCRIPTION_LENGTH = 500

# 사용자 관련 상수
MAX_NICKNAME_LENGTH = 20
MIN_NICKNAME_LENGTH = 1
MAX_BIO_LENGTH = 200

# 메시지 관련 상수
MAX_MESSAGE_LENGTH = 500
MIN_MESSAGE_LENGTH = 1

# 메모 관련 상수
MAX_MEMO_LENGTH = 1000
MIN_MEMO_LENGTH = 1

# 페이지네이션 상수
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
MIN_PAGE_SIZE = 1

# WebSocket 관련 상수
WS_MAX_CONNECTIONS = 1000
WS_HEARTBEAT_INTERVAL = 30  # 초
WS_CLEANUP_INTERVAL = 300   # 초 (5분)
WS_INACTIVE_TIMEOUT = 1800  # 초 (30분)

# 파일 업로드 관련 상수
MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_AVATAR_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}

# 시간 관련 상수
MAX_POLL_DURATION_DAYS = 30
DEFAULT_TOKEN_EXPIRE_MINUTES = 30

# 응답 메시지 상수
class ResponseMessages:
    """응답 메시지 상수 클래스"""
    
    # 성공 메시지
    SUCCESS_CREATED = "성공적으로 생성되었습니다"
    SUCCESS_UPDATED = "성공적으로 수정되었습니다"
    SUCCESS_DELETED = "성공적으로 삭제되었습니다"
    SUCCESS_LOGIN = "로그인 성공"
    SUCCESS_LOGOUT = "로그아웃 성공"
    SUCCESS_REGISTER = "회원가입 성공"
    
    # 에러 메시지
    ERROR_NOT_FOUND = "요청한 리소스를 찾을 수 없습니다"
    ERROR_UNAUTHORIZED = "인증이 필요합니다"
    ERROR_FORBIDDEN = "권한이 없습니다"
    ERROR_VALIDATION = "입력 데이터가 유효하지 않습니다"
    ERROR_DUPLICATE = "이미 존재하는 데이터입니다"
    ERROR_SERVER = "서버 내부 오류가 발생했습니다"
    
    # 투표 관련 메시지
    POLL_CREATED = "투표가 성공적으로 생성되었습니다"
    POLL_UPDATED = "투표가 성공적으로 수정되었습니다"
    POLL_DELETED = "투표가 성공적으로 삭제되었습니다"
    POLL_CLOSED = "투표가 종료되었습니다"
    VOTE_CAST = "투표가 완료되었습니다"
    VOTE_UPDATED = "투표가 변경되었습니다"
    POLL_NOT_ACTIVE = "종료된 투표에는 참여할 수 없습니다"
    POLL_NOT_OWNER = "투표 작성자만 수정할 수 있습니다"
    
    # 사용자 관련 메시지
    USER_CREATED = "사용자가 성공적으로 생성되었습니다"
    USER_UPDATED = "사용자 정보가 성공적으로 수정되었습니다"
    NICKNAME_TAKEN = "이미 사용 중인 닉네임입니다"
    INVALID_NICKNAME = "유효하지 않은 닉네임입니다"
    USER_NOT_FOUND = "사용자를 찾을 수 없습니다"
    
    # 채팅 관련 메시지
    MESSAGE_SENT = "메시지가 전송되었습니다"
    MESSAGE_DELETED = "메시지가 삭제되었습니다"
    MESSAGE_TOO_LONG = f"메시지는 {MAX_MESSAGE_LENGTH}자를 초과할 수 없습니다"
    MESSAGE_EMPTY = "메시지 내용이 비어있습니다"
    
    # 메모 관련 메시지
    MEMO_CREATED = "메모가 성공적으로 생성되었습니다"
    MEMO_UPDATED = "메모가 성공적으로 수정되었습니다"
    MEMO_DELETED = "메모가 성공적으로 삭제되었습니다"
    MEMO_TOO_LONG = f"메모는 {MAX_MEMO_LENGTH}자를 초과할 수 없습니다"
    MEMO_EMPTY = "메모 내용이 비어있습니다"
    MEMO_NOT_FOUND = "메모를 찾을 수 없습니다"


# HTTP 상태 코드 상수
class HTTPStatus:
    """HTTP 상태 코드 상수 클래스"""
    
    # 성공 응답
    OK = 200
    CREATED = 201
    NO_CONTENT = 204
    
    # 클라이언트 에러
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    TOO_MANY_REQUESTS = 429
    
    # 서버 에러
    INTERNAL_SERVER_ERROR = 500
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503


# WebSocket 메시지 타입 상수
class WSMessageType:
    """WebSocket 메시지 타입 상수 클래스"""
    
    # 클라이언트 → 서버
    PING = "ping"
    CHAT_MESSAGE = "chat_message"
    VOTE_CAST = "vote_cast"
    POLL_SUBSCRIBE = "poll_subscribe"
    USER_TYPING = "user_typing"
    
    # 서버 → 클라이언트
    PONG = "pong"
    CHAT_MESSAGE_RECEIVED = "chat_message_received"
    VOTE_RESULT = "vote_result"
    POLL_CREATED = "poll_created"
    POLL_UPDATED = "poll_updated"
    POLL_CLOSED = "poll_closed"
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    USERS_ONLINE = "users_online"
    ERROR = "error"
    SYSTEM_NOTIFICATION = "system_notification"
    PERSONAL_NOTIFICATION = "personal_notification"


# 데이터베이스 관련 상수
class DatabaseConfig:
    """데이터베이스 설정 상수 클래스"""
    
    # 연결 풀 설정
    POOL_SIZE = 10
    MAX_OVERFLOW = 20
    POOL_TIMEOUT = 30
    POOL_RECYCLE = 3600
    
    # 쿼리 제한
    MAX_QUERY_LIMIT = 1000
    DEFAULT_QUERY_LIMIT = 100


# 로깅 관련 상수
class LogLevel:
    """로깅 레벨 상수 클래스"""
    
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# 캐싱 관련 상수
class CacheKeys:
    """캐시 키 상수 클래스"""
    
    ONLINE_USERS = "online_users"
    POLL_RESULTS = "poll_results:{poll_id}"
    USER_STATS = "user_stats:{user_id}"
    TRENDING_POLLS = "trending_polls"
    CHAT_STATS = "chat_stats"


# 정규표현식 패턴 상수
class RegexPatterns:
    """정규표현식 패턴 상수 클래스"""
    
    # 닉네임 패턴 (한글, 영문, 숫자, 언더스코어, 공백)
    NICKNAME = r'^[a-zA-Z0-9가-힣_\s]+$'
    
    # 이메일 패턴 (기본적인 이메일 형식)
    EMAIL = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    # URL 패턴 (http/https)
    URL = r'^https?://[^\s/$.?#].[^\s]*$'
    
    # UUID 패턴
    UUID = r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'


# 환경 변수 기본값
class DefaultValues:
    """환경 변수 기본값 상수 클래스"""
    
    # 서버 설정
    HOST = "0.0.0.0"
    PORT = 8000
    DEBUG = False
    
    # 데이터베이스
    DATABASE_URL = "sqlite:///./voting_app.db"
    DATABASE_ECHO = False
    
    # JWT 설정
    JWT_ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    # WebSocket 설정
    WS_MAX_CONNECTIONS = 1000
    WS_HEARTBEAT_INTERVAL = 30
    
    # 로깅 설정
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(levelname)s:     %(message)s"


# API 버전 관련 상수
class APIVersion:
    """API 버전 상수 클래스"""
    
    V1 = "v1"
    CURRENT = V1
    PREFIX = f"/api/{CURRENT}"


# 미디어 타입 상수
class MediaType:
    """미디어 타입 상수 클래스"""
    
    JSON = "application/json"
    HTML = "text/html"
    PLAIN_TEXT = "text/plain"
    FORM_DATA = "application/x-www-form-urlencoded"
    MULTIPART = "multipart/form-data"


# 헤더 상수
class Headers:
    """HTTP 헤더 상수 클래스"""
    
    AUTHORIZATION = "Authorization"
    CONTENT_TYPE = "Content-Type"
    USER_AGENT = "User-Agent"
    X_USER_ID = "X-User-ID"
    X_REQUEST_ID = "X-Request-ID"
    X_FORWARDED_FOR = "X-Forwarded-For"
