#!/usr/bin/env python3
"""
실시간 투표 플랫폼 백엔드 서버 시작 스크립트
가상환경 및 의존성 문제 해결을 위한 스크립트
"""

import sys
import os
import subprocess
from pathlib import Path

# 프로젝트 루트 디렉토리 설정
PROJECT_ROOT = Path(__file__).parent
os.chdir(PROJECT_ROOT)

# Python 경로에 프로젝트 루트 추가
sys.path.insert(0, str(PROJECT_ROOT))

def check_virtual_environment():
    """가상환경 활성화 확인"""
    venv_path = PROJECT_ROOT / "venv"
    
    if not venv_path.exists():
        print("❌ 가상환경이 없습니다. 가상환경을 생성해주세요:")
        print("python -m venv venv")
        return False
    
    # 가상환경 활성화 확인
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ 가상환경이 활성화되었습니다.")
        return True
    else:
        print("⚠️ 가상환경이 활성화되지 않았습니다.")
        print("다음 명령어로 가상환경을 활성화해주세요:")
        print("source venv/bin/activate  # macOS/Linux")
        print("venv\\Scripts\\activate  # Windows")
        return False

def install_dependencies():
    """의존성 패키지 설치"""
    try:
        print("📦 의존성 패키지 설치 중...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ 의존성 패키지 설치 완료")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 의존성 설치 실패: {e}")
        return False

def check_packages():
    """필수 패키지 확인"""
    required_packages = [
        "fastapi",
        "sqlalchemy", 
        "pydantic",
        "uvicorn",
        "alembic",
        "python_jose",
        "passlib"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)
    
    return len(missing_packages) == 0

def create_env_file():
    """환경 변수 파일 확인 및 생성"""
    env_file = PROJECT_ROOT / ".env"
    
    if env_file.exists():
        print("✅ .env 파일이 존재합니다.")
        return True
    
    print("⚠️ .env 파일이 없습니다. 기본 .env 파일을 생성합니다...")
    
    env_content = """# 실시간 투표 플랫폼 백엔드 환경 변수

# 애플리케이션 설정
APP_NAME="실시간 투표 플랫폼"
APP_VERSION="1.0.0"
DEBUG=true
SECRET_KEY="your-secret-key-here-change-in-production"

# 서버 설정
HOST=0.0.0.0
PORT=8000
SOCKET_PORT=8001

# 데이터베이스 설정
DATABASE_URL="sqlite:///./voting_app.db"
DATABASE_ECHO=true

# JWT 토큰 설정
JWT_SECRET_KEY="your-jwt-secret-key-here"
JWT_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 로깅 설정
LOG_LEVEL="INFO"

# 개발 환경 설정
RELOAD=true
"""
    
    try:
        env_file.write_text(env_content)
        print("✅ .env 파일 생성 완료")
        return True
    except Exception as e:
        print(f"❌ .env 파일 생성 실패: {e}")
        return False

def run_server():
    """서버 실행"""
    try:
        print("🚀 서버를 시작합니다...")
        print("서버 주소: http://localhost:8000")
        print("API 문서: http://localhost:8000/docs")
        print("종료하려면 Ctrl+C를 누르세요.")
        print("-" * 50)
        
        # uvicorn으로 서버 실행
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ], check=True)
        
    except KeyboardInterrupt:
        print("\n✅ 서버가 정상적으로 종료되었습니다.")
    except subprocess.CalledProcessError as e:
        print(f"❌ 서버 실행 실패: {e}")

def main():
    """메인 함수"""
    print("🗳️ 실시간 투표 플랫폼 백엔드 서버")
    print("=" * 50)
    
    # 1. 가상환경 확인
    if not check_virtual_environment():
        return
    
    # 2. 환경 변수 파일 확인
    if not create_env_file():
        return
    
    # 3. 패키지 확인
    print("\n📦 패키지 확인:")
    if not check_packages():
        print("\n❌ 일부 패키지가 누락되었습니다.")
        install = input("패키지를 설치하시겠습니까? (y/n): ")
        if install.lower() == 'y':
            if not install_dependencies():
                return
        else:
            return
    
    # 4. 서버 실행
    print("\n🚀 모든 준비가 완료되었습니다!")
    run_server()

if __name__ == "__main__":
    main()
