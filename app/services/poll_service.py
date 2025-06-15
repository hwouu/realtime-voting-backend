# app/services/poll_service.py
"""
실시간 투표 플랫폼 투표 서비스
투표 관련 비즈니스 로직 처리
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime

from ..models.poll import Poll, PollOption, Vote
from ..models.user import User


class PollService:
    """투표 서비스 클래스"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_poll(
        self, 
        title: str, 
        description: str, 
        options: List[str], 
        creator_id: str,
        ends_at: Optional[datetime] = None
    ) -> Poll:
        """
        새 투표 생성
        
        Args:
            title: 투표 제목
            description: 투표 설명
            options: 투표 옵션 목록
            creator_id: 생성자 ID
            ends_at: 종료 시간 (선택적)
        
        Returns:
            Poll: 생성된 투표 객체
        """
        # 투표 생성
        poll = Poll(
            title=title,
            description=description,
            created_by=creator_id,
            ends_at=ends_at,
            is_active=True
        )
        
        self.db.add(poll)
        self.db.commit()
        self.db.refresh(poll)
        
        # 투표 옵션 생성
        for option_text in options:
            option = PollOption(
                poll_id=poll.id,
                text=option_text
            )
            self.db.add(option)
        
        self.db.commit()
        self.db.refresh(poll)
        
        return poll
    
    def get_poll_by_id(self, poll_id: str) -> Optional[Poll]:
        """투표 ID로 조회"""
        return self.db.query(Poll).filter(Poll.id == poll_id).first()
    
    def get_polls_list(
        self, 
        page: int = 1, 
        per_page: int = 20, 
        active_only: bool = False
    ) -> Dict[str, Any]:
        """
        투표 목록 조회
        
        Args:
            page: 페이지 번호
            per_page: 페이지당 항목 수
            active_only: 활성 투표만 조회 여부
        
        Returns:
            Dict[str, Any]: 투표 목록 및 통계
        """
        offset = (page - 1) * per_page
        
        query = self.db.query(Poll)
        
        if active_only:
            query = query.filter(Poll.is_active == True)
        
        total = query.count()
        active_count = self.db.query(Poll).filter(Poll.is_active == True).count()
        
        polls = query.order_by(desc(Poll.created_at))\
                    .offset(offset)\
                    .limit(per_page)\
                    .all()
        
        return {
            "polls": polls,
            "total": total,
            "active_count": active_count,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        }
    
    def vote_on_poll(self, poll_id: str, option_id: str, user_id: str) -> Dict[str, Any]:
        """
        투표 참여
        
        Args:
            poll_id: 투표 ID
            option_id: 선택한 옵션 ID
            user_id: 투표자 ID
        
        Returns:
            Dict[str, Any]: 투표 결과
        """
        # 투표 및 옵션 조회
        poll = self.get_poll_by_id(poll_id)
        if not poll:
            raise Exception("투표를 찾을 수 없습니다")
        
        if not poll.is_active or poll.is_ended:
            raise Exception("종료된 투표에는 참여할 수 없습니다")
        
        option = self.db.query(PollOption).filter(
            PollOption.id == option_id,
            PollOption.poll_id == poll_id
        ).first()
        
        if not option:
            raise Exception("투표 옵션을 찾을 수 없습니다")
        
        # 기존 투표 확인
        existing_vote = self.db.query(Vote).filter(
            Vote.poll_id == poll_id,
            Vote.user_id == user_id
        ).first()
        
        if existing_vote:
            # 기존 투표 변경
            old_option = self.db.query(PollOption).filter(
                PollOption.id == existing_vote.option_id
            ).first()
            
            if old_option:
                old_option.decrement_vote()
            
            existing_vote.option_id = option_id
            option.increment_vote()
            
            message = "투표가 변경되었습니다"
            vote_id = existing_vote.id
        else:
            # 새 투표 생성
            new_vote = Vote.create_vote(
                poll_id=poll_id,
                option_id=option_id,
                user_id=user_id
            )
            
            self.db.add(new_vote)
            option.increment_vote()
            
            message = "투표가 완료되었습니다"
            vote_id = new_vote.id
        
        self.db.commit()
        self.db.refresh(poll)
        
        return {
            "success": True,
            "message": message,
            "vote_id": vote_id,
            "poll_results": poll.get_results()
        }
    
    def update_poll(self, poll: Poll, **update_data) -> Poll:
        """
        투표 정보 업데이트
        
        Args:
            poll: 업데이트할 투표 객체
            **update_data: 업데이트할 데이터
        
        Returns:
            Poll: 업데이트된 투표 객체
        """
        for field, value in update_data.items():
            if hasattr(poll, field) and value is not None:
                setattr(poll, field, value)
        
        self.db.commit()
        self.db.refresh(poll)
        return poll
    
    def delete_poll(self, poll: Poll):
        """투표 삭제"""
        self.db.delete(poll)
        self.db.commit()
    
    def close_poll(self, poll: Poll) -> Poll:
        """투표 종료"""
        poll.close_poll()
        self.db.commit()
        self.db.refresh(poll)
        return poll
    
    def get_poll_stats(self, poll: Poll) -> Dict[str, Any]:
        """
        투표 통계 조회
        
        Args:
            poll: 투표 객체
        
        Returns:
            Dict[str, Any]: 투표 통계
        """
        # 고유 투표자 수
        unique_voters = self.db.query(Vote.user_id)\
                              .filter(Vote.poll_id == poll.id)\
                              .distinct().count()
        
        # 가장 인기 있는 옵션
        most_popular_option = None
        if poll.options:
            most_popular = max(poll.options, key=lambda opt: opt.vote_count)
            if most_popular.vote_count > 0:
                most_popular_option = most_popular.to_dict()
        
        return {
            "poll_id": poll.id,
            "total_votes": poll.total_votes,
            "unique_voters": unique_voters,
            "most_popular_option": most_popular_option,
            "options_count": len(poll.options),
            "is_active": poll.is_active,
            "is_ended": poll.is_ended
        }
    
    def get_user_polls(self, user_id: str, page: int = 1, per_page: int = 20) -> List[Poll]:
        """
        사용자가 생성한 투표 목록 조회
        
        Args:
            user_id: 사용자 ID
            page: 페이지 번호
            per_page: 페이지당 항목 수
        
        Returns:
            List[Poll]: 사용자 투표 목록
        """
        offset = (page - 1) * per_page
        
        return self.db.query(Poll)\
                     .filter(Poll.created_by == user_id)\
                     .order_by(desc(Poll.created_at))\
                     .offset(offset)\
                     .limit(per_page)\
                     .all()
    
    def get_user_votes(self, user_id: str) -> List[Vote]:
        """사용자가 참여한 투표 목록 조회"""
        return self.db.query(Vote)\
                     .filter(Vote.user_id == user_id)\
                     .order_by(desc(Vote.created_at))\
                     .all()
    
    def check_user_voted(self, poll_id: str, user_id: str) -> Optional[Vote]:
        """사용자가 특정 투표에 참여했는지 확인"""
        return self.db.query(Vote).filter(
            Vote.poll_id == poll_id,
            Vote.user_id == user_id
        ).first()
    
    def get_poll_results(self, poll: Poll) -> Dict[str, Any]:
        """
        투표 결과 상세 조회
        
        Args:
            poll: 투표 객체
        
        Returns:
            Dict[str, Any]: 투표 결과
        """
        return {
            "poll_id": poll.id,
            "poll_title": poll.title,
            "total_votes": poll.total_votes,
            "results": poll.get_results(),
            "is_active": poll.is_active,
            "created_at": poll.created_at,
            "ends_at": poll.ends_at
        }
    
    def search_polls(self, query: str, limit: int = 10) -> List[Poll]:
        """
        투표 검색
        
        Args:
            query: 검색 쿼리
            limit: 결과 제한
        
        Returns:
            List[Poll]: 검색된 투표 목록
        """
        return self.db.query(Poll)\
                     .filter(
                         Poll.title.contains(query) | 
                         Poll.description.contains(query)
                     )\
                     .order_by(desc(Poll.created_at))\
                     .limit(limit)\
                     .all()
    
    def get_trending_polls(self, limit: int = 5) -> List[Poll]:
        """
        인기 투표 목록 조회 (최근 투표 수 기준)
        
        Args:
            limit: 결과 제한
        
        Returns:
            List[Poll]: 인기 투표 목록
        """
        from datetime import timedelta
        
        # 최근 24시간 내 투표가 많은 순으로 정렬
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        poll_vote_counts = self.db.query(
            Poll.id,
            func.count(Vote.id).label('recent_votes')
        ).join(Vote)\
         .filter(Vote.created_at >= yesterday)\
         .group_by(Poll.id)\
         .order_by(desc('recent_votes'))\
         .limit(limit)\
         .all()
        
        # 투표 객체들 조회
        poll_ids = [poll_id for poll_id, _ in poll_vote_counts]
        polls = self.db.query(Poll).filter(Poll.id.in_(poll_ids)).all()
        
        # 원래 순서대로 정렬
        polls_dict = {poll.id: poll for poll in polls}
        return [polls_dict[poll_id] for poll_id in poll_ids if poll_id in polls_dict]
