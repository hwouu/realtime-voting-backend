#!/usr/bin/env python3
"""
패키지 설치 확인 스크립트
import 오류 진단용
"""

import sys
import os

# 현재 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

print("🔍 Python 환경 및 패키지 확인")
print(f"Python 버전: {sys.version}")
print(f"Python 실행 경로: {sys.executable}")
print(f"현재 작업 디렉토리: {os.getcwd()}")
print(f"Python 경로: {sys.path[:3]}...")

# 필수 패키지 확인
required_packages = [
    "fastapi",
    "sqlalchemy", 
    "pydantic",
    "uvicorn",
    "alembic"
]

print("\n📦 패키지 import 테스트:")
for package in required_packages:
    try:
        __import__(package)
        print(f"✅ {package} - OK")
    except ImportError as e:
        print(f"❌ {package} - FAIL: {e}")

# app 모듈 import 테스트
print("\n🏗️ 프로젝트 모듈 import 테스트:")
try:
    from app.core.config import settings
    print("✅ app.core.config - OK")
except ImportError as e:
    print(f"❌ app.core.config - FAIL: {e}")

try:
    from app.models.user import User
    print("✅ app.models.user - OK")
except ImportError as e:
    print(f"❌ app.models.user - FAIL: {e}")

try:
    from app.database.session import get_db
    print("✅ app.database.session - OK")
except ImportError as e:
    print(f"❌ app.database.session - FAIL: {e}")

print("\n🎯 결론:")
print("모든 패키지가 정상 import되면 Pylance 오류는 IDE 설정 문제입니다.")
print("패키지 import 실패가 있다면 가상환경 활성화 또는 패키지 설치를 확인하세요.")
