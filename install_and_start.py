#!/usr/bin/env python3
"""
빠른 패키지 설치 및 서버 시작 스크립트
greenlet 패키지 설치 포함
"""

import subprocess
import sys

def install_greenlet():
    """greenlet 패키지 설치"""
    try:
        print("📦 greenlet 패키지를 설치합니다...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", "greenlet==3.0.3"
        ], check=True)
        print("✅ greenlet 패키지 설치 완료")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ greenlet 설치 실패: {e}")
        return False

def start_server():
    """서버 시작"""
    try:
        print("🚀 서버를 시작합니다...")
        subprocess.run([sys.executable, "main.py"], check=True)
    except KeyboardInterrupt:
        print("\n✅ 서버가 정상적으로 종료되었습니다.")
    except subprocess.CalledProcessError as e:
        print(f"❌ 서버 실행 실패: {e}")

def main():
    print("🔧 greenlet 설치 및 서버 시작")
    print("=" * 40)
    
    # greenlet 설치
    if install_greenlet():
        # 서버 시작
        start_server()
    else:
        print("❌ 설치 실패로 서버를 시작할 수 없습니다.")

if __name__ == "__main__":
    main()
