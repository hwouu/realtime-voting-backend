#!/usr/bin/env python3
"""
빠른 패키지 설치 및 테스트 스크립트
"""

import subprocess
import sys
import os

def install_missing_package():
    """누락된 pydantic-settings 패키지 설치"""
    try:
        print("📦 pydantic-settings 패키지를 설치합니다...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", "pydantic-settings==2.7.0"
        ], check=True)
        print("✅ pydantic-settings 설치 완료")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 패키지 설치 실패: {e}")
        return False

def test_imports():
    """프로젝트 모듈 import 테스트"""
    try:
        print("\n🧪 프로젝트 모듈 import 재테스트:")
        
        from app.core.config import settings
        print("✅ app.core.config - OK")
        
        from app.models.user import User
        print("✅ app.models.user - OK")
        
        from app.database.session import get_db
        print("✅ app.database.session - OK")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import 오류: {e}")
        return False

def init_database():
    """데이터베이스 초기화"""
    try:
        print("\n🗄️ 데이터베이스 초기화 재시도...")
        import asyncio
        from app.database.session import init_db
        
        async def main():
            await init_db()
            print("✅ 데이터베이스 초기화 완료")
        
        asyncio.run(main())
        return True
        
    except Exception as e:
        print(f"❌ 데이터베이스 초기화 실패: {e}")
        return False

def main():
    print("🔧 누락된 패키지 수정 스크립트")
    print("=" * 40)
    
    # 1. 패키지 설치
    if not install_missing_package():
        return
    
    # 2. Import 테스트
    if not test_imports():
        return
    
    # 3. 데이터베이스 초기화
    if not init_database():
        return
    
    print("\n🎉 모든 문제가 해결되었습니다!")
    print("🚀 이제 다음 명령어로 서버를 시작할 수 있습니다:")
    print("   python main.py")
    print("   또는")
    print("   python start_server.py")

if __name__ == "__main__":
    # 프로젝트 루트 디렉토리로 이동
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Python 경로에 현재 디렉토리 추가
    sys.path.insert(0, os.getcwd())
    
    main()
