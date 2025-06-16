#!/usr/bin/env python3
"""
데이터베이스 재생성 스크립트
metadata 컬럼명 충돌 문제 해결용
"""

import os
import sys
import asyncio

def remove_old_database():
    """기존 데이터베이스 파일 삭제"""
    db_files = ["voting_app.db", "voting_app.db-journal", "voting_app.db-wal"]
    
    for db_file in db_files:
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"🗑️ 기존 데이터베이스 파일 삭제: {db_file}")
    
    print("✅ 기존 데이터베이스 정리 완료")

async def create_new_database():
    """새 데이터베이스 생성"""
    try:
        # Python 경로에 현재 디렉토리 추가
        sys.path.insert(0, os.getcwd())
        
        from app.database.session import init_db
        
        print("🗄️ 새 데이터베이스를 생성합니다...")
        await init_db()
        print("✅ 데이터베이스 생성 완료")
        return True
        
    except Exception as e:
        print(f"❌ 데이터베이스 생성 실패: {e}")
        return False

def test_server_start():
    """서버 시작 테스트"""
    try:
        print("🧪 서버 시작 테스트...")
        
        # 설정 로드 테스트
        from app.core.config import settings
        print(f"✅ 설정 로드 성공: {settings.app_name}")
        
        # 모델 import 테스트
        from app.models.message import ChatMessage
        print("✅ 메시지 모델 로드 성공")
        
        from app.models.user import User
        print("✅ 사용자 모델 로드 성공")
        
        print("🎉 모든 테스트 통과! 서버를 시작할 수 있습니다.")
        return True
        
    except Exception as e:
        print(f"❌ 서버 테스트 실패: {e}")
        return False

def main():
    print("🔧 데이터베이스 재생성 스크립트")
    print("=" * 40)
    
    # 1. 기존 데이터베이스 삭제
    remove_old_database()
    
    # 2. 새 데이터베이스 생성
    success = asyncio.run(create_new_database())
    if not success:
        return
    
    # 3. 서버 시작 테스트
    if test_server_start():
        print("\n🚀 이제 다음 명령어로 서버를 시작하세요:")
        print("   python main.py")
        print("\n📚 서버 주소:")
        print("   - API: http://localhost:8000")
        print("   - 문서: http://localhost:8000/docs")
        print("   - WebSocket: ws://localhost:8000/ws")

if __name__ == "__main__":
    main()
