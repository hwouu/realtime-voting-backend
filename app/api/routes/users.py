# app/api/routes/users.py
"""
실시간 투표 플랫폼 사용자 API 라우터
사용자 인증, 등록, 프로필 관리 엔드포인트
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from ...database.session import get_db
from ...api.deps import get_current_user, get_optional_current_user, get_pagination_params, PaginationParams
from ...core.security import create_user_token, sanitize_nickname, validate_nickname
from ...models.user import User
from ...models.poll import Poll
from ...models.vote import Vote
from ...models.message import ChatMessage
from ...models.memo import UserMemo
from ...schemas.user import (
    UserCreateRequest,
    UserLoginRequest,
    UserResponse,
    UserBasicInfo,
    UserUpdateRequest,
    UserLoginResponse,
    UserListResponse,
    UserProfileResponse,
    SuccessResponse,
    ErrorResponse
)

router = APIRouter()


@router.post("/register", response_model=UserLoginResponse)
async def register_user(
    user_data: UserCreateRequest,
    db: Session = Depends(get_db)
):
    """
    새 사용자 등록
    
    Args:
        user_data: 사용자 생성 요청 데이터
        db: 데이터베이스 세션
    
    Returns:
        UserLoginResponse: 등록된 사용자 정보 및 액세스 토큰
    """
    try:
        # 닉네임 유효성 검증
        nickname = sanitize_nickname(user_data.nickname)
        if not validate_nickname(nickname):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="유효하지 않은 닉네임입니다"
            )
        
        # 중복 닉네임 확인
        existing_user = db.query(User).filter(User.nickname == nickname).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 사용 중인 닉네임입니다"
            )
        
        # 새 사용자 생성
        new_user = User.create_user(nickname=nickname)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # 액세스 토큰 생성
        token_info = create_user_token(new_user.id, new_user.nickname)
        
        return UserLoginResponse(
            success=True,
            user=UserResponse.from_orm(new_user),
            access_token=token_info["access_token"],
            token_type=token_info["token_type"],
            expires_in=token_info["expires_in"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 등록 중 오류가 발생했습니다"
        )


@router.post("/login", response_model=UserLoginResponse)
async def login_user(
    login_data: UserLoginRequest,
    db: Session = Depends(get_db)
):
    """
    사용자 로그인 (닉네임으로 로그인)
    
    Args:
        login_data: 로그인 요청 데이터
        db: 데이터베이스 세션
    
    Returns:
        UserLoginResponse: 사용자 정보 및 액세스 토큰
    """
    try:
        # 닉네임으로 사용자 조회
        nickname = sanitize_nickname(login_data.nickname)
        user = db.query(User).filter(User.nickname == nickname).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다"
            )
        
        # 온라인 상태 업데이트
        user.set_online_status(True)
        db.commit()
        
        # 액세스 토큰 생성
        token_info = create_user_token(user.id, user.nickname)
        
        return UserLoginResponse(
            success=True,
            user=UserResponse.from_orm(user),
            access_token=token_info["access_token"],
            token_type=token_info["token_type"],
            expires_in=token_info["expires_in"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="로그인 중 오류가 발생했습니다"
        )


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    현재 사용자 프로필 조회
    
    Args:
        current_user: 현재 인증된 사용자
        db: 데이터베이스 세션
    
    Returns:
        UserProfileResponse: 사용자 프로필 정보
    """
    try:
        # 사용자 통계 정보 조회
        stats = {
            "total_polls_created": db.query(Poll).filter(Poll.created_by == current_user.id).count(),
            "total_votes_cast": db.query(Vote).filter(Vote.user_id == current_user.id).count(),
            "total_messages_sent": db.query(ChatMessage).filter(ChatMessage.user_id == current_user.id).count(),
            "total_memos_written": db.query(UserMemo).filter(UserMemo.user_id == current_user.id).count()
        }
        
        # 프로필 응답 생성
        profile = UserProfileResponse(
            id=current_user.id,
            nickname=current_user.nickname,
            is_online=current_user.is_online,
            joined_at=current_user.joined_at,
            last_seen=current_user.last_seen,
            avatar_url=current_user.avatar_url,
            bio=current_user.bio,
            **stats
        )
        
        return profile
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="프로필 조회 중 오류가 발생했습니다"
        )


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    update_data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    현재 사용자 프로필 수정
    
    Args:
        update_data: 수정할 사용자 정보
        current_user: 현재 인증된 사용자
        db: 데이터베이스 세션
    
    Returns:
        UserResponse: 수정된 사용자 정보
    """
    try:
        # 닉네임 수정
        if update_data.nickname is not None:
            new_nickname = sanitize_nickname(update_data.nickname)
            
            # 유효성 검증
            if not validate_nickname(new_nickname):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="유효하지 않은 닉네임입니다"
                )
            
            # 중복 확인 (자신 제외)
            existing_user = db.query(User).filter(
                User.nickname == new_nickname,
                User.id != current_user.id
            ).first()
            
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="이미 사용 중인 닉네임입니다"
                )
            
            current_user.nickname = new_nickname
        
        # 기타 정보 수정
        if update_data.bio is not None:
            current_user.bio = update_data.bio
        
        if update_data.avatar_url is not None:
            current_user.avatar_url = update_data.avatar_url
        
        # 변경사항 저장
        db.commit()
        db.refresh(current_user)
        
        return UserResponse.from_orm(current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="프로필 수정 중 오류가 발생했습니다"
        )


@router.get("/list", response_model=UserListResponse)
async def get_users_list(
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    사용자 목록 조회
    
    Args:
        pagination: 페이지네이션 파라미터
        current_user: 현재 사용자 (선택적)
        db: 데이터베이스 세션
    
    Returns:
        UserListResponse: 사용자 목록
    """
    try:
        # 전체 사용자 수 조회
        total = db.query(User).count()
        
        # 온라인 사용자 수 조회
        online_count = db.query(User).filter(User.is_online == True).count()
        
        # 사용자 목록 조회 (최근 접속 순)
        users_query = db.query(User).order_by(User.last_seen.desc())
        users = users_query.offset(pagination.offset).limit(pagination.limit).all()
        
        # 응답 생성
        user_list = [UserBasicInfo.from_orm(user) for user in users]
        
        return UserListResponse(
            users=user_list,
            total=total,
            online_count=online_count
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 목록 조회 중 오류가 발생했습니다"
        )


@router.get("/online", response_model=List[UserBasicInfo])
async def get_online_users(
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    현재 온라인 사용자 목록 조회
    
    Args:
        current_user: 현재 사용자 (선택적)
        db: 데이터베이스 세션
    
    Returns:
        List[UserBasicInfo]: 온라인 사용자 목록
    """
    try:
        # 온라인 사용자 조회
        online_users = db.query(User).filter(User.is_online == True).all()
        
        return [UserBasicInfo.from_orm(user) for user in online_users]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="온라인 사용자 조회 중 오류가 발생했습니다"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: str,
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    특정 사용자 정보 조회
    
    Args:
        user_id: 조회할 사용자 ID
        current_user: 현재 사용자 (선택적)
        db: 데이터베이스 세션
    
    Returns:
        UserResponse: 사용자 정보
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다"
            )
        
        return UserResponse.from_orm(user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 조회 중 오류가 발생했습니다"
        )


@router.post("/logout", response_model=SuccessResponse)
async def logout_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    사용자 로그아웃
    
    Args:
        current_user: 현재 인증된 사용자
        db: 데이터베이스 세션
    
    Returns:
        SuccessResponse: 로그아웃 성공 응답
    """
    try:
        # 오프라인 상태로 변경
        current_user.set_online_status(False)
        db.commit()
        
        return SuccessResponse(
            success=True,
            message="성공적으로 로그아웃되었습니다"
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="로그아웃 중 오류가 발생했습니다"
        )
