# app/websocket/events.py
"""
실시간 투표 플랫폼 WebSocket 이벤트 처리
WebSocket 연결, 이벤트 핸들링, 실시간 통신 관리
"""

import json
import logging
from typing import Dict, Any
from fastapi import WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session

from ..database.session import get_db, get_async_db
from ..models.user import User
from ..models.message import ChatMessage
from ..core.security import extract_user_from_token
from .manager import websocket_manager

logger = logging.getLogger(__name__)


async def authenticate_websocket_user(
    websocket: WebSocket,
    token: str = Query(None),
    user_id: str = Query(None),
    nickname: str = Query(None)
) -> Dict[str, str]:
    """
    WebSocket 사용자 인증
    
    Args:
        websocket: WebSocket 연결
        token: JWT 토큰 (선택적)
        user_id: 사용자 ID (선택적)
        nickname: 사용자 닉네임 (선택적)
    
    Returns:
        Dict[str, str]: 사용자 정보 (user_id, nickname)
    
    Raises:
        Exception: 인증 실패시
    """
    try:
        # JWT 토큰으로 인증 시도
        if token:
            user_data = extract_user_from_token(token)
            if user_data:
                return {
                    "user_id": user_data["user_id"],
                    "nickname": user_data["nickname"]
                }
        
        # 쿼리 파라미터로 인증 시도 (간소화된 인증)
        if user_id and nickname:
            # 실제 운영 환경에서는 추가 검증 필요
            return {
                "user_id": user_id,
                "nickname": nickname
            }
        
        raise Exception("인증 정보가 없습니다")
        
    except Exception as e:
        logger.error(f"WebSocket 인증 실패: {e}")
        raise Exception("WebSocket 인증에 실패했습니다")


async def handle_websocket_message(
    websocket: WebSocket,
    connection_id: str,
    message_data: Dict[str, Any]
):
    """
    WebSocket 메시지 처리
    
    Args:
        websocket: WebSocket 연결
        connection_id: 연결 ID
        message_data: 수신된 메시지 데이터
    """
    try:
        message_type = message_data.get("type")
        data = message_data.get("data", {})
        
        logger.info(f"WebSocket 메시지 수신: {message_type} from {connection_id}")
        
        # 메시지 유형별 처리
        if message_type == "ping":
            await handle_ping(websocket, connection_id)
        
        elif message_type == "chat_message":
            await handle_chat_message(websocket, connection_id, data)
        
        elif message_type == "vote_cast":
            await handle_vote_cast(websocket, connection_id, data)
        
        elif message_type == "poll_subscribe":
            await handle_poll_subscribe(websocket, connection_id, data)
        
        elif message_type == "user_typing":
            await handle_user_typing(websocket, connection_id, data)
        
        else:
            logger.warning(f"알 수 없는 메시지 유형: {message_type}")
            await send_error_message(websocket, "알 수 없는 메시지 유형입니다")
    
    except Exception as e:
        logger.error(f"WebSocket 메시지 처리 오류: {e}")
        await send_error_message(websocket, "메시지 처리 중 오류가 발생했습니다")


async def handle_ping(websocket: WebSocket, connection_id: str):
    """핑 메시지 처리 (하트비트)"""
    try:
        pong_message = {
            "type": "pong",
            "timestamp": "2025-01-16T15:30:00Z"
        }
        await websocket.send_text(json.dumps(pong_message))
        
    except Exception as e:
        logger.error(f"핑 처리 오류: {e}")


async def handle_chat_message(websocket: WebSocket, connection_id: str, data: Dict[str, Any]):
    """채팅 메시지 처리"""
    try:
        message_text = data.get("message", "").strip()
        if not message_text:
            await send_error_message(websocket, "메시지 내용이 비어있습니다")
            return
        
        # 연결에서 사용자 정보 조회
        user_info = websocket_manager.connection_manager.connection_users.get(connection_id)
        if not user_info:
            await send_error_message(websocket, "사용자 정보를 찾을 수 없습니다")
            return
        
        # 데이터베이스에 메시지 저장 (비동기)
        async for db in get_async_db():
            new_message = ChatMessage.create_user_message(
                user_id=user_info["user_id"],
                message=message_text
            )
            db.add(new_message)
            await db.commit()
            await db.refresh(new_message)
            
            # 모든 사용자에게 브로드캐스트
            broadcast_data = {
                "type": "chat_message_received",
                "data": new_message.to_dict()
            }
            await websocket_manager.broadcast_message(broadcast_data)
            break
        
    except Exception as e:
        logger.error(f"채팅 메시지 처리 오류: {e}")
        await send_error_message(websocket, "채팅 메시지 전송에 실패했습니다")


async def handle_vote_cast(websocket: WebSocket, connection_id: str, data: Dict[str, Any]):
    """투표 참여 처리"""
    try:
        poll_id = data.get("poll_id")
        option_id = data.get("option_id")
        
        if not poll_id or not option_id:
            await send_error_message(websocket, "투표 정보가 누락되었습니다")
            return
        
        # 연결에서 사용자 정보 조회
        user_info = websocket_manager.connection_manager.connection_users.get(connection_id)
        if not user_info:
            await send_error_message(websocket, "사용자 정보를 찾을 수 없습니다")
            return
        
        # 투표 처리는 API 엔드포인트에서 수행하도록 안내
        response_message = {
            "type": "vote_response",
            "data": {
                "success": False,
                "message": "투표는 API 엔드포인트를 통해 수행해주세요",
                "poll_id": poll_id
            }
        }
        await websocket.send_text(json.dumps(response_message))
        
    except Exception as e:
        logger.error(f"투표 처리 오류: {e}")
        await send_error_message(websocket, "투표 처리에 실패했습니다")


async def handle_poll_subscribe(websocket: WebSocket, connection_id: str, data: Dict[str, Any]):
    """투표 구독 처리 (실시간 결과 업데이트)"""
    try:
        poll_id = data.get("poll_id")
        if not poll_id:
            await send_error_message(websocket, "투표 ID가 필요합니다")
            return
        
        # 투표 구독 확인 메시지 전송
        response_message = {
            "type": "poll_subscribed",
            "data": {
                "poll_id": poll_id,
                "message": f"투표 {poll_id}의 실시간 업데이트를 구독했습니다"
            }
        }
        await websocket.send_text(json.dumps(response_message))
        
    except Exception as e:
        logger.error(f"투표 구독 처리 오류: {e}")
        await send_error_message(websocket, "투표 구독에 실패했습니다")


async def handle_user_typing(websocket: WebSocket, connection_id: str, data: Dict[str, Any]):
    """사용자 타이핑 상태 처리"""
    try:
        is_typing = data.get("is_typing", False)
        
        # 연결에서 사용자 정보 조회
        user_info = websocket_manager.connection_manager.connection_users.get(connection_id)
        if not user_info:
            return
        
        # 다른 사용자들에게 타이핑 상태 브로드캐스트
        typing_message = {
            "type": "user_typing",
            "data": {
                "user_id": user_info["user_id"],
                "nickname": user_info["nickname"],
                "is_typing": is_typing
            }
        }
        await websocket_manager.broadcast_message(
            typing_message, 
            exclude_user_id=user_info["user_id"]
        )
        
    except Exception as e:
        logger.error(f"타이핑 상태 처리 오류: {e}")


async def send_error_message(websocket: WebSocket, error_message: str):
    """에러 메시지 전송"""
    try:
        error_response = {
            "type": "error",
            "data": {
                "message": error_message,
                "timestamp": "2025-01-16T15:30:00Z"
            }
        }
        await websocket.send_text(json.dumps(error_response))
        
    except Exception as e:
        logger.error(f"에러 메시지 전송 실패: {e}")


def setup_websocket_events(app):
    """
    FastAPI 앱에 WebSocket 이벤트 설정
    
    Args:
        app: FastAPI 애플리케이션 인스턴스
    """
    
    @app.websocket("/ws")
    async def websocket_endpoint(
        websocket: WebSocket,
        token: str = Query(None),
        user_id: str = Query(None),
        nickname: str = Query(None)
    ):
        """
        메인 WebSocket 엔드포인트
        
        Args:
            websocket: WebSocket 연결
            token: JWT 토큰 (선택적)
            user_id: 사용자 ID (선택적)
            nickname: 사용자 닉네임 (선택적)
        """
        connection_id = None
        
        try:
            # 사용자 인증
            user_data = await authenticate_websocket_user(
                websocket, token, user_id, nickname
            )
            
            # WebSocket 연결 설정
            connection_id = await websocket_manager.connect(
                websocket,
                user_data["user_id"],
                user_data["nickname"]
            )
            
            logger.info(f"✅ WebSocket 연결 성공: {user_data['nickname']} ({connection_id})")
            
            # 메시지 수신 루프
            while True:
                try:
                    # 메시지 수신 (텍스트 또는 JSON)
                    message = await websocket.receive_text()
                    
                    try:
                        message_data = json.loads(message)
                    except json.JSONDecodeError:
                        # 일반 텍스트 메시지로 처리
                        message_data = {
                            "type": "chat_message",
                            "data": {"message": message}
                        }
                    
                    # 메시지 처리
                    await handle_websocket_message(websocket, connection_id, message_data)
                    
                except WebSocketDisconnect:
                    logger.info(f"🔌 WebSocket 연결 종료: {user_data['nickname']}")
                    break
                    
                except json.JSONDecodeError as e:
                    logger.error(f"JSON 파싱 오류: {e}")
                    await send_error_message(websocket, "잘못된 메시지 형식입니다")
                    
                except Exception as e:
                    logger.error(f"메시지 처리 중 오류: {e}")
                    await send_error_message(websocket, "메시지 처리 중 오류가 발생했습니다")
        
        except Exception as e:
            logger.error(f"WebSocket 연결 오류: {e}")
            try:
                await websocket.close(code=1008, reason="인증 실패")
            except:
                pass
        
        finally:
            # 연결 정리
            if connection_id:
                await websocket_manager.disconnect(connection_id)
    
    @app.websocket("/ws/health")
    async def websocket_health_check(websocket: WebSocket):
        """
        WebSocket 헬스 체크 엔드포인트
        
        Args:
            websocket: WebSocket 연결
        """
        try:
            await websocket.accept()
            
            # 상태 정보 전송
            stats = websocket_manager.get_stats()
            health_data = {
                "type": "health_check",
                "data": {
                    "status": "healthy",
                    "timestamp": "2025-01-16T15:30:00Z",
                    "connections": stats
                }
            }
            
            await websocket.send_text(json.dumps(health_data))
            await websocket.close()
            
        except Exception as e:
            logger.error(f"WebSocket 헬스 체크 오류: {e}")
            try:
                await websocket.close(code=1011, reason="서버 오류")
            except:
                pass
    
    @app.get("/ws/stats")
    async def get_websocket_stats():
        """
        WebSocket 통계 정보 조회 (HTTP 엔드포인트)
        
        Returns:
            dict: WebSocket 연결 통계
        """
        try:
            stats = websocket_manager.get_stats()
            online_users = await websocket_manager.get_online_users()
            
            return {
                "success": True,
                "data": {
                    "websocket_stats": stats,
                    "online_users": [user.dict() for user in online_users],
                    "timestamp": "2025-01-16T15:30:00Z"
                }
            }
            
        except Exception as e:
            logger.error(f"WebSocket 통계 조회 오류: {e}")
            return {
                "success": False,
                "error": "통계 조회 중 오류가 발생했습니다"
            }


# WebSocket 이벤트 핸들러 래퍼 함수들 (추후 확장용)
async def broadcast_poll_update(poll_id: str, poll_data: Dict[str, Any]):
    """투표 업데이트 브로드캐스트"""
    try:
        message = {
            "type": "poll_updated",
            "data": {
                "poll_id": poll_id,
                "poll": poll_data
            }
        }
        await websocket_manager.broadcast_message(message)
        
    except Exception as e:
        logger.error(f"투표 업데이트 브로드캐스트 오류: {e}")


async def broadcast_system_notification(message: str, notification_type: str = "info"):
    """시스템 알림 브로드캐스트"""
    try:
        notification = {
            "type": "system_notification",
            "data": {
                "message": message,
                "notification_type": notification_type,
                "timestamp": "2025-01-16T15:30:00Z"
            }
        }
        await websocket_manager.broadcast_message(notification)
        
    except Exception as e:
        logger.error(f"시스템 알림 브로드캐스트 오류: {e}")


async def send_personal_notification(user_id: str, message: str, notification_type: str = "info"):
    """개인 알림 전송"""
    try:
        notification = {
            "type": "personal_notification",
            "data": {
                "message": message,
                "notification_type": notification_type,
                "timestamp": "2025-01-16T15:30:00Z"
            }
        }
        await websocket_manager.send_personal_message(notification, user_id)
        
    except Exception as e:
        logger.error(f"개인 알림 전송 오류: {e}")
