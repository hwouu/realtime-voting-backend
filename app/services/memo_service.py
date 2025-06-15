# app/services/memo_service.py
"""
실시간 투표 플랫폼 메모 서비스
메모 관련 비즈니스 로직 처리
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, or_
from datetime import datetime, timedelta

from ..models.memo import UserMemo
from ..models.poll import Poll
from ..models.user import User


class MemoService:
    """메모 서비스 클래스"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_memo(
        self, 
        user_id: str, 
        content: str, 
        poll_id: Optional[str] = None
    ) -> UserMemo:
        """
        새 메모 생성
        
        Args:
            user_id: 사용자 ID
            content: 메모 내용
            poll_id: 관련 투표 ID (선택적)
        
        Returns:
            UserMemo: 생성된 메모 객체
        """
        # 투표 ID가 있으면 투표 존재 확인
        if poll_id:
            poll = self.db.query(Poll).filter(Poll.id == poll_id).first()
            if not poll:
                raise Exception("해당 투표를 찾을 수 없습니다")
        
        new_memo = UserMemo.create_memo(
            user_id=user_id,
            content=content,
            poll_id=poll_id
        )
        
        self.db.add(new_memo)
        self.db.commit()
        self.db.refresh(new_memo)
        
        return new_memo
    
    def get_memo_by_id(self, memo_id: str, user_id: str) -> Optional[UserMemo]:
        """
        메모 ID로 조회 (사용자 소유권 확인)
        
        Args:
            memo_id: 메모 ID
            user_id: 사용자 ID
        
        Returns:
            Optional[UserMemo]: 메모 객체 또는 None
        """
        return self.db.query(UserMemo).filter(
            UserMemo.id == memo_id,
            UserMemo.user_id == user_id
        ).first()
    
    def get_user_memos(
        self, 
        user_id: str,
        page: int = 1,
        per_page: int = 20,
        poll_id: Optional[str] = None,
        sort_by: str = "updated_at",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """
        사용자 메모 목록 조회
        
        Args:
            user_id: 사용자 ID
            page: 페이지 번호
            per_page: 페이지당 항목 수
            poll_id: 특정 투표 필터 (선택적)
            sort_by: 정렬 기준
            sort_order: 정렬 순서
        
        Returns:
            Dict[str, Any]: 메모 목록 및 통계
        """
        offset = (page - 1) * per_page
        
        query = self.db.query(UserMemo).filter(UserMemo.user_id == user_id)
        
        if poll_id:
            query = query.filter(UserMemo.poll_id == poll_id)
        
        # 전체 개수
        total = query.count()
        
        # 투표 관련/일반 메모 개수
        poll_related_count = self.db.query(UserMemo)\
                                  .filter(UserMemo.user_id == user_id)\
                                  .filter(UserMemo.poll_id.isnot(None))\
                                  .count()
        general_count = total - poll_related_count
        
        # 정렬 적용
        if hasattr(UserMemo, sort_by):
            if sort_order.lower() == "asc":
                query = query.order_by(getattr(UserMemo, sort_by))
            else:
                query = query.order_by(desc(getattr(UserMemo, sort_by)))
        else:
            query = query.order_by(desc(UserMemo.updated_at))
        
        # 페이지네이션
        memos = query.offset(offset).limit(per_page).all()
        
        return {
            "memos": memos,
            "total": total,
            "poll_related_count": poll_related_count,
            "general_count": general_count,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        }
    
    def update_memo(self, memo: UserMemo, content: str) -> UserMemo:
        """
        메모 내용 수정
        
        Args:
            memo: 수정할 메모 객체
            content: 새 내용
        
        Returns:
            UserMemo: 수정된 메모 객체
        """
        memo.update_content(content)
        self.db.commit()
        self.db.refresh(memo)
        return memo
    
    def delete_memo(self, memo: UserMemo):
        """메모 삭제"""
        self.db.delete(memo)
        self.db.commit()
    
    def search_memos(
        self, 
        user_id: str,
        query: str,
        page: int = 1,
        per_page: int = 20,
        poll_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        메모 검색
        
        Args:
            user_id: 사용자 ID
            query: 검색 쿼리
            page: 페이지 번호
            per_page: 페이지당 항목 수
            poll_id: 특정 투표 필터 (선택적)
        
        Returns:
            Dict[str, Any]: 검색 결과
        """
        offset = (page - 1) * per_page
        
        db_query = self.db.query(UserMemo)\
                         .filter(UserMemo.user_id == user_id)\
                         .filter(UserMemo.content.contains(query))
        
        if poll_id:
            db_query = db_query.filter(UserMemo.poll_id == poll_id)
        
        total = db_query.count()
        memos = db_query.order_by(desc(UserMemo.updated_at))\
                       .offset(offset)\
                       .limit(per_page)\
                       .all()
        
        return {
            "results": memos,
            "total": total,
            "query": query,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        }
    
    def get_memo_stats(self, user_id: str) -> Dict[str, Any]:
        """
        메모 통계 조회
        
        Args:
            user_id: 사용자 ID
        
        Returns:
            Dict[str, Any]: 메모 통계
        """
        # 전체 메모 수
        total_memos = self.db.query(UserMemo)\
                           .filter(UserMemo.user_id == user_id)\
                           .count()
        
        # 투표 관련 메모 수
        poll_related_memos = self.db.query(UserMemo)\
                                  .filter(UserMemo.user_id == user_id)\
                                  .filter(UserMemo.poll_id.isnot(None))\
                                  .count()
        
        # 일반 메모 수
        general_memos = total_memos - poll_related_memos
        
        # 총 단어/글자 수
        memos = self.db.query(UserMemo)\
                     .filter(UserMemo.user_id == user_id)\
                     .all()
        
        total_words = sum(memo.word_count for memo in memos)
        total_characters = sum(memo.character_count for memo in memos)
        
        # 가장 활발한 날 (최근 30일)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        daily_counts = self.db.query(
            func.date(UserMemo.created_at).label('date'),
            func.count(UserMemo.id).label('count')
        ).filter(
            UserMemo.user_id == user_id,
            UserMemo.created_at >= thirty_days_ago
        ).group_by(func.date(UserMemo.created_at))\
         .order_by(desc('count'))\
         .first()
        
        most_active_day = daily_counts.date.strftime('%Y-%m-%d') if daily_counts else None
        
        # 최근 24시간 메모 수
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_memos_count = self.db.query(UserMemo)\
                                  .filter(UserMemo.user_id == user_id)\
                                  .filter(UserMemo.created_at >= yesterday)\
                                  .count()
        
        return {
            "total_memos": total_memos,
            "poll_related_memos": poll_related_memos,
            "general_memos": general_memos,
            "total_words": total_words,
            "total_characters": total_characters,
            "most_active_day": most_active_day,
            "recent_memos_count": recent_memos_count
        }
    
    def get_poll_memos(self, user_id: str, poll_id: str) -> List[UserMemo]:
        """
        특정 투표의 사용자 메모 조회
        
        Args:
            user_id: 사용자 ID
            poll_id: 투표 ID
        
        Returns:
            List[UserMemo]: 투표 관련 메모 목록
        """
        return self.db.query(UserMemo)\
                     .filter(UserMemo.user_id == user_id)\
                     .filter(UserMemo.poll_id == poll_id)\
                     .order_by(desc(UserMemo.updated_at))\
                     .all()
    
    def get_recent_memos(self, user_id: str, limit: int = 10) -> List[UserMemo]:
        """
        최근 메모 목록 조회
        
        Args:
            user_id: 사용자 ID
            limit: 조회할 메모 수
        
        Returns:
            List[UserMemo]: 최근 메모 목록
        """
        return self.db.query(UserMemo)\
                     .filter(UserMemo.user_id == user_id)\
                     .order_by(desc(UserMemo.updated_at))\
                     .limit(limit)\
                     .all()
    
    def get_memo_activity_summary(self, user_id: str, days: int = 7) -> List[Dict[str, Any]]:
        """
        메모 활동 요약 (일별)
        
        Args:
            user_id: 사용자 ID
            days: 조회할 일 수
        
        Returns:
            List[Dict[str, Any]]: 일별 메모 활동
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        daily_stats = self.db.query(
            func.date(UserMemo.created_at).label('date'),
            func.count(UserMemo.id).label('memo_count'),
            func.sum(func.length(UserMemo.content)).label('total_characters')
        ).filter(
            UserMemo.user_id == user_id,
            UserMemo.created_at >= start_date
        ).group_by(func.date(UserMemo.created_at))\
         .order_by('date')\
         .all()
        
        return [
            {
                "date": stat.date.strftime('%Y-%m-%d'),
                "memo_count": stat.memo_count,
                "total_characters": stat.total_characters or 0
            }
            for stat in daily_stats
        ]
    
    def get_memo_with_relations(self, memo_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        관련 정보가 포함된 메모 조회
        
        Args:
            memo_id: 메모 ID
            user_id: 사용자 ID
        
        Returns:
            Optional[Dict[str, Any]]: 메모 및 관련 정보
        """
        memo = self.get_memo_by_id(memo_id, user_id)
        if not memo:
            return None
        
        # 사용자 정보
        user = self.db.query(User).filter(User.id == user_id).first()
        user_info = {
            "id": user.id,
            "nickname": user.nickname
        } if user else None
        
        # 투표 정보
        poll_info = None
        if memo.poll_id:
            poll = self.db.query(Poll).filter(Poll.id == memo.poll_id).first()
            if poll:
                poll_info = {
                    "id": poll.id,
                    "title": poll.title
                }
        
        return {
            "memo": memo,
            "user": user_info,
            "poll": poll_info
        }
    
    def bulk_delete_memos(self, user_id: str, memo_ids: List[str]) -> int:
        """
        메모 일괄 삭제
        
        Args:
            user_id: 사용자 ID
            memo_ids: 삭제할 메모 ID 목록
        
        Returns:
            int: 삭제된 메모 수
        """
        deleted_count = self.db.query(UserMemo)\
                             .filter(
                                 UserMemo.user_id == user_id,
                                 UserMemo.id.in_(memo_ids)
                             ).delete(synchronize_session=False)
        
        self.db.commit()
        return deleted_count
    
    def export_user_memos(self, user_id: str) -> List[Dict[str, Any]]:
        """
        사용자 메모 내보내기 (전체)
        
        Args:
            user_id: 사용자 ID
        
        Returns:
            List[Dict[str, Any]]: 모든 메모 데이터
        """
        memos = self.db.query(UserMemo)\
                     .filter(UserMemo.user_id == user_id)\
                     .order_by(UserMemo.created_at)\
                     .all()
        
        export_data = []
        for memo in memos:
            poll_title = None
            if memo.poll_id and memo.poll:
                poll_title = memo.poll.title
            
            export_data.append({
                "id": memo.id,
                "content": memo.content,
                "poll_id": memo.poll_id,
                "poll_title": poll_title,
                "created_at": memo.created_at.isoformat(),
                "updated_at": memo.updated_at.isoformat(),
                "word_count": memo.word_count,
                "character_count": memo.character_count
            })
        
        return export_data
