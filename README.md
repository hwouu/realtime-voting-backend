# 🗳️ 실시간 투표 플랫폼 백엔드

WebSocket 기반 실시간 투표 및 채팅 플랫폼의 백엔드 API 서버

## 📊 프로젝트 개요

컴퓨터 네트워크 9팀 프로젝트로, 다양한 네트워크 프로토콜 트래픽을 생성하여 Wireshark로 패킷 분석하는 것이 주 목적입니다.

### 🎯 주요 기능

- **실시간 투표 시스템**: 투표 생성, 참여, 결과 집계
- **WebSocket 실시간 통신**: 투표 결과 및 채팅 메시지 실시간 업데이트  
- **사용자 인증**: JWT 토큰 기반 인증
- **개인 메모 기능**: 사용자별 메모 저장 및 조회
- **다양한 HTTP 메서드**: GET, POST, PUT, DELETE, PATCH 활용
- **다중 포트 서비스**: 패킷 분석을 위한 다양한 포트 사용

## 🛠️ 기술 스택

- **Framework**: FastAPI 0.115.6
- **Database**: SQLite (SQLAlchemy ORM)
- **Real-time**: WebSocket, Socket.IO
- **Authentication**: JWT, Passlib
- **Validation**: Pydantic
- **Development**: Uvicorn, Python-dotenv

## 🚀 빠른 시작

### 1. 가상환경 설정
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정
```bash
# .env 파일을 확인하고 필요시 수정
cp .env.example .env
```

### 4. 데이터베이스 초기화
```bash
# Alembic 마이그레이션 실행 (추후 구현)
alembic upgrade head
```

### 5. 서버 실행
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 📡 API 엔드포인트

### 인증 API
- `POST /api/auth/login` - 사용자 로그인
- `GET /api/auth/me` - 현재 사용자 정보

### 투표 API  
- `GET /api/polls` - 투표 목록 조회
- `POST /api/polls` - 새 투표 생성
- `GET /api/polls/{poll_id}` - 특정 투표 조회
- `POST /api/polls/{poll_id}/vote` - 투표 참여
- `PUT /api/polls/{poll_id}` - 투표 수정
- `DELETE /api/polls/{poll_id}` - 투표 삭제

### 채팅 API
- `GET /api/chat/messages` - 채팅 메시지 조회
- `POST /api/chat/messages` - 채팅 메시지 전송

### 메모 API
- `GET /api/memos` - 메모 조회
- `POST /api/memos` - 메모 저장
- `PUT /api/memos/{memo_id}` - 메모 수정
- `DELETE /api/memos/{memo_id}` - 메모 삭제

## 🔄 WebSocket 이벤트

### 클라이언트 → 서버
- `user:join` - 사용자 접속
- `chat:message` - 채팅 메시지 전송
- `vote:cast` - 투표 참여

### 서버 → 클라이언트  
- `user:joined` - 사용자 접속 알림
- `user:left` - 사용자 퇴장 알림
- `vote:result` - 투표 결과 업데이트
- `chat:message_received` - 채팅 메시지 수신
- `poll:created` - 새 투표 생성 알림

## 🌐 네트워크 패킷 분석

### 포트 사용
- **8000**: 메인 API 서버 (HTTP/HTTPS)
- **8001**: WebSocket 서버 (WS/WSS)
- **8080**: 파일 서버 (선택적)
- **3001**: 헬스체크 서비스 (선택적)

### 프로토콜 분석 포인트
- **Layer 2**: Ethernet Frame
- **Layer 3**: IP 패킷 (IPv4/IPv6) 
- **Layer 4**: TCP/UDP 세그먼트
- **Layer 7**: HTTP/WebSocket 애플리케이션 데이터

## 📁 프로젝트 구조

```
app/
├── main.py              # FastAPI 애플리케이션 진입점
├── api/                 # API 라우터
│   ├── __init__.py
│   ├── deps.py          # 의존성 주입
│   └── routes/          # API 경로별 라우터
│       ├── auth.py      # 인증 API
│       ├── polls.py     # 투표 API
│       ├── chat.py      # 채팅 API
│       └── memos.py     # 메모 API
├── core/                # 핵심 설정
│   ├── config.py        # 환경 설정
│   ├── security.py      # 보안 설정
│   └── websocket.py     # WebSocket 관리
├── database/            # 데이터베이스
│   ├── base.py          # 기본 설정
│   └── session.py       # 세션 관리
├── models/              # SQLAlchemy 모델
│   ├── user.py          # 사용자 모델
│   ├── poll.py          # 투표 모델
│   ├── vote.py          # 투표 기록 모델
│   ├── message.py       # 채팅 메시지 모델
│   └── memo.py          # 메모 모델
├── schemas/             # Pydantic 스키마
│   ├── user.py          # 사용자 스키마
│   ├── poll.py          # 투표 스키마
│   ├── chat.py          # 채팅 스키마
│   └── memo.py          # 메모 스키마
└── services/            # 비즈니스 로직
    ├── auth_service.py  # 인증 서비스
    ├── poll_service.py  # 투표 서비스
    ├── chat_service.py  # 채팅 서비스
    └── memo_service.py  # 메모 서비스
```

## 🧪 개발 및 테스트

### 개발 서버 실행
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### API 문서 확인
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 패킷 캡처 테스트
```bash
# Wireshark 필터 예시
host 127.0.0.1 or host localhost
tcp.port in {3000,8000,8001,8080}
```

## 👥 팀원

- **노현우** (2020121070) - 프론트엔드 개발
- **김민수** (2020125008) - 백엔드 개발  
- **이수현** (2021121141) - 네트워크 분석
- **김지홍** (2021125017) - 시스템 통합

## 📅 개발 일정

- **1주차**: 프로젝트 설계 및 환경 구축 ✅
- **2주차**: 기본 API 구현 🔄
- **3주차**: WebSocket 실시간 통신 구현
- **4주차**: 패킷 분석 및 보안 검증
- **5주차**: 통합 테스트 및 최적화
- **6주차**: 최종 보고서 및 발표 준비

---

**컴퓨터 네트워크 프로젝트 · 9팀**
