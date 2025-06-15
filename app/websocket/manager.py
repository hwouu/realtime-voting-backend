# app/websocket/manager.py
"""
실시간 투표 플랫폼 WebSocket 연결 관리
WebSocket 연결, 사용자 세션, 실시간 이벤트 브로드캐스트 관리
"""

import asyncio
import json
import logging
from typing import Dict, List, Set, Optional, Any
from datetime import datetime, timedelta
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.session import get_async_db
from ..models.user import User
from ..models.message import ChatMessage, MessageType
from ..schemas.user import UserBasicInfo
from ..schemas.chat import ChatMessageResponse

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket 연결 관리자"""
    
    def __init__(self):
        # 활성 연결 저장: {connection_id: WebSocket}
        self.active_connections: Dict[str, WebSocket] = {}
        
        # 사용자별 연결 매핑: {user_id: connection_id}
        self.user_connections: Dict[str, str] = {}
        
        # 연결별 사용자 매핑: {connection_id: user_info}
        self.connection_users: Dict[str, dict] = {}
        
        # 연결별 마지막 활동 시간
        self.last_activity: Dict[str, datetime] = {}
        
        # 룸별 연결 관리 (미래 확장용)
        self.rooms: Dict[str, Set[str]] = {}


class WebSocketManager:
    """WebSocket 전역 관리자"""
    
    def __init__(self):
        self.connection_manager = ConnectionManager()
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        
    async def connect(self, websocket: WebSocket, user_id: str, user_nickname: str) -> str:
        """WebSocket 연결 설정"""
        try:
            await websocket.accept()
            
            # 고유 연결 ID 생성
            connection_id = f"{user_id}_{datetime.utcnow().timestamp()}"
            
            # 기존 연결이 있다면 해제
            if user_id in self.connection_manager.user_connections:
                old_connection_id = self.connection_manager.user_connections[user_id]
                await self._disconnect_by_id(old_connection_id, send_message=False)
            
            # 새 연결 등록
            self.connection_manager.active_connections[connection_id] = websocket
            self.connection_manager.user_connections[user_id] = connection_id
            self.connection_manager.connection_users[connection_id] = {
                "user_id": user_id,
                "nickname": user_nickname,
                "connected_at": datetime.utcnow()
            }
            self.connection_manager.last_activity[connection_id] = datetime.utcnow()
            
            logger.info(f"✅ WebSocket 연결됨: {user_nickname} (ID: {user_id})")
            
            # 사용자 온라인 상태 업데이트
            await self._update_user_online_status(user_id, True)
            
            # 다른 사용자들에게 입장 알림
            await self._broadcast_user_joined(user_nickname)
            
            # 현재 온라인 사용자 목록 전송
            await self._send_online_users(connection_id)
            
            # 백그라운드 작업 시작
            if not self.heartbeat_task:
                self.heartbeat_task = asyncio.create_task(self._heartbeat_worker())
            if not self.cleanup_task:
                self.cleanup_task = asyncio.create_task(self._cleanup_worker())
            
            return connection_id
            
        except Exception as e:
            logger.error(f"❌ WebSocket 연결 실패: {e}")
            raise
    
    async def disconnect(self, connection_id: str):
        """WebSocket 연결 해제"""
        await self._disconnect_by_id(connection_id, send_message=True)
    
    async def _disconnect_by_id(self, connection_id: str, send_message: bool = True):
        """연결 ID로 연결 해제"""
        try:
            # 연결 정보 조회
            user_info = self.connection_manager.connection_users.get(connection_id)
            
            if connection_id in self.connection_manager.active_connections:
                # WebSocket 연결 해제
                try:
                    websocket = self.connection_manager.active_connections[connection_id]
                    await websocket.close()
                except:
                    pass  # 이미 닫힌 연결일 수 있음
                
                # 연결 정보 삭제
                del self.connection_manager.active_connections[connection_id]
                
                if user_info:
                    user_id = user_info["user_id"]
                    user_nickname = user_info["nickname"]
                    
                    # 사용자 매핑 삭제
                    if user_id in self.connection_manager.user_connections:
                        del self.connection_manager.user_connections[user_id]
                    
                    # 사용자 오프라인 상태 업데이트
                    await self._update_user_online_status(user_id, False)
                    
                    # 다른 사용자들에게 퇴장 알림
                    if send_message:
                        await self._broadcast_user_left(user_nickname)
                    
                    logger.info(f"🔌 WebSocket 연결 해제됨: {user_nickname} (ID: {user_id})")
                
                # 기타 정보 삭제
                if connection_id in self.connection_manager.connection_users:
                    del self.connection_manager.connection_users[connection_id]
                if connection_id in self.connection_manager.last_activity:
                    del self.connection_manager.last_activity[connection_id]
                    
        except Exception as e:
            logger.error(f"❌ WebSocket 연결 해제 오류: {e}")
    
    async def send_personal_message(self, message: dict, user_id: str):
        """특정 사용자에게 개인 메시지 전송"""
        try:
            connection_id = self.connection_manager.user_connections.get(user_id)
            if connection_id and connection_id in self.connection_manager.active_connections:
                websocket = self.connection_manager.active_connections[connection_id]
                await websocket.send_text(json.dumps(message, ensure_ascii=False))
                
                # 활동 시간 업데이트
                self.connection_manager.last_activity[connection_id] = datetime.utcnow()
                
        except WebSocketDisconnect:
            await self._disconnect_by_id(connection_id)
        except Exception as e:
            logger.error(f"❌ 개인 메시지 전송 실패 (user_id: {user_id}): {e}")
    
    async def broadcast_message(self, message: dict, exclude_user_id: Optional[str] = None):
        """모든 연결된 사용자에게 메시지 브로드캐스트"""
        if not self.connection_manager.active_connections:
            return
        
        disconnected_connections = []
        
        for connection_id, websocket in self.connection_manager.active_connections.items():
            try:
                # 제외할 사용자 확인
                user_info = self.connection_manager.connection_users.get(connection_id)
                if user_info and exclude_user_id and user_info["user_id"] == exclude_user_id:
                    continue
                
                await websocket.send_text(json.dumps(message, ensure_ascii=False))
                
                # 활동 시간 업데이트
                self.connection_manager.last_activity[connection_id] = datetime.utcnow()
                
            except WebSocketDisconnect:
                disconnected_connections.append(connection_id)
            except Exception as e:
                logger.error(f"❌ 브로드캐스트 실패 (connection_id: {connection_id}): {e}")
                disconnected_connections.append(connection_id)
        
        # 연결이 끊어진 사용자들 정리
        for connection_id in disconnected_connections:
            await self._disconnect_by_id(connection_id, send_message=False)
    
    async def get_online_users(self) -> List[UserBasicInfo]:
        """현재 온라인 사용자 목록 조회"""
        online_users = []
        
        for connection_id, user_info in self.connection_manager.connection_users.items():
            if connection_id in self.connection_manager.active_connections:
                online_users.append(UserBasicInfo(
                    id=user_info["user_id"],
                    nickname=user_info["nickname"],
                    is_online=True
                ))
        
        return online_users
    
    async def get_connection_count(self) -> int:
        """현재 연결 수 반환"""
        return len(self.connection_manager.active_connections)
    
    async def _update_user_online_status(self, user_id: str, is_online: bool):
        """사용자 온라인 상태 데이터베이스 업데이트"""
        try:
            async for db in get_async_db():
                # SQLAlchemy 2.0 스타일로 사용자 조회 및 업데이트
                from sqlalchemy import select, update
                
                # 사용자 상태 업데이트
                stmt = (
                    update(User)
                    .where(User.id == user_id)
                    .values(
                        is_online=is_online,
                        last_seen=datetime.utcnow()
                    )
                )
                await db.execute(stmt)
                await db.commit()
                break
                
        except Exception as e:
            logger.error(f"❌ 사용자 온라인 상태 업데이트 실패: {e}")
    
    async def _broadcast_user_joined(self, user_nickname: str):
        """사용자 입장 알림 브로드캐스트"""
        try:
            # 채팅 메시지 저장
            async for db in get_async_db():
                join_message = ChatMessage.create_user_join_message(user_nickname)
                db.add(join_message)
                await db.commit()
                await db.refresh(join_message)
                
                # 브로드캐스트 메시지 생성
                message = {
                    "type": "user_joined",
                    "data": join_message.to_dict()
                }
                
                await self.broadcast_message(message)
                break
                
        except Exception as e:
            logger.error(f"❌ 사용자 입장 알림 실패: {e}")
    
    async def _broadcast_user_left(self, user_nickname: str):
        """사용자 퇴장 알림 브로드캐스트"""
        try:
            # 채팅 메시지 저장
            async for db in get_async_db():
                leave_message = ChatMessage.create_user_leave_message(user_nickname)
                db.add(leave_message)
                await db.commit()
                await db.refresh(leave_message)
                
                # 브로드캐스트 메시지 생성
                message = {
                    "type": "user_left",
                    "data": leave_message.to_dict()
                }
                
                await self.broadcast_message(message)
                break
                
        except Exception as e:
            logger.error(f"❌ 사용자 퇴장 알림 실패: {e}")
    
    async def _send_online_users(self, connection_id: str):
        """온라인 사용자 목록 전송"""
        try:
            online_users = await self.get_online_users()
            
            message = {
                "type": "users_online",
                "data": {
                    "users": [user.dict() for user in online_users],
                    "count": len(online_users)
                }
            }
            
            if connection_id in self.connection_manager.active_connections:
                websocket = self.connection_manager.active_connections[connection_id]
                await websocket.send_text(json.dumps(message, ensure_ascii=False))
                
        except Exception as e:
            logger.error(f"❌ 온라인 사용자 목록 전송 실패: {e}")
    
    async def _heartbeat_worker(self):
        """하트비트 워커 (주기적으로 연결 상태 확인)"""
        while True:
            try:
                await asyncio.sleep(30)  # 30초마다 실행
                
                # 모든 연결에 핑 메시지 전송
                ping_message = {
                    "type": "ping",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await self.broadcast_message(ping_message)
                
            except Exception as e:
                logger.error(f"❌ 하트비트 워커 오류: {e}")
                await asyncio.sleep(10)
    
    async def _cleanup_worker(self):
        """정리 워커 (비활성 연결 정리)"""
        while True:
            try:
                await asyncio.sleep(300)  # 5분마다 실행
                
                current_time = datetime.utcnow()
                inactive_connections = []
                
                # 30분 이상 비활성 연결 찾기
                for connection_id, last_activity in self.connection_manager.last_activity.items():
                    if current_time - last_activity > timedelta(minutes=30):
                        inactive_connections.append(connection_id)
                
                # 비활성 연결 정리
                for connection_id in inactive_connections:
                    logger.info(f"🧹 비활성 연결 정리: {connection_id}")
                    await self._disconnect_by_id(connection_id, send_message=True)
                
                logger.info(f"🧹 연결 정리 완료: {len(inactive_connections)}개 연결 정리됨")
                
            except Exception as e:
                logger.error(f"❌ 정리 워커 오류: {e}")
                await asyncio.sleep(60)
    
    async def cleanup(self):
        """리소스 정리"""
        try:
            # 백그라운드 작업 취소
            if self.heartbeat_task and not self.heartbeat_task.done():
                self.heartbeat_task.cancel()
                
            if self.cleanup_task and not self.cleanup_task.done():
                self.cleanup_task.cancel()
            
            # 모든 연결 해제
            connection_ids = list(self.connection_manager.active_connections.keys())
            for connection_id in connection_ids:
                await self._disconnect_by_id(connection_id, send_message=False)
            
            logger.info("🧹 WebSocket 매니저 정리 완료")
            
        except Exception as e:
            logger.error(f"❌ WebSocket 매니저 정리 실패: {e}")
    
    def get_stats(self) -> dict:
        """WebSocket 통계 정보 반환"""
        return {
            "total_connections": len(self.connection_manager.active_connections),
            "active_users": len(self.connection_manager.user_connections),
            "rooms": len(self.connection_manager.rooms),
            "heartbeat_running": self.heartbeat_task and not self.heartbeat_task.done(),
            "cleanup_running": self.cleanup_task and not self.cleanup_task.done()
        }


# 전역 WebSocket 매니저 인스턴스
websocket_manager = WebSocketManager()
