#!/usr/bin/env python3
"""
스마트 서버 시작 스크립트
포트 충돌 시 자동으로 다른 포트 찾아서 실행
"""

import socket
import subprocess
import sys
import os

def find_free_port(start_port=8000, max_port=8010):
    """사용 가능한 포트 찾기"""
    for port in range(start_port, max_port + 1):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    return None

def kill_process_on_port(port):
    """특정 포트를 사용하는 프로세스 종료"""
    try:
        # macOS/Linux
        result = subprocess.run(['lsof', '-ti', f':{port}'], 
                              capture_output=True, text=True)
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                try:
                    subprocess.run(['kill', '-9', pid], check=True)
                    print(f"🔄 포트 {port}를 사용하던 프로세스 {pid} 종료됨")
                    return True
                except subprocess.CalledProcessError:
                    pass
    except FileNotFoundError:
        pass
    return False

def start_server(port=8000):
    """서버 시작"""
    try:
        print(f"🚀 포트 {port}에서 서버를 시작합니다...")
        
        # 환경 변수 설정
        env = os.environ.copy()
        env['PORT'] = str(port)
        
        # 서버 실행
        subprocess.run([
            sys.executable, '-m', 'uvicorn', 
            'main:app', 
            '--host', '0.0.0.0', 
            '--port', str(port), 
            '--reload'
        ], env=env, check=True)
        
    except KeyboardInterrupt:
        print(f"\n✅ 서버가 정상적으로 종료되었습니다.")
    except subprocess.CalledProcessError as e:
        print(f"❌ 서버 실행 실패: {e}")

def main():
    print("🗳️ 실시간 투표 플랫폼 백엔드")
    print("=" * 40)
    
    preferred_port = 8000
    
    # 1. 기본 포트(8000) 확인
    if find_free_port(preferred_port, preferred_port) == preferred_port:
        print(f"✅ 포트 {preferred_port} 사용 가능")
        start_server(preferred_port)
        return
    
    # 2. 기존 프로세스 종료 시도
    print(f"⚠️ 포트 {preferred_port}이 사용 중입니다.")
    choice = input("기존 프로세스를 종료하시겠습니까? (y/n): ").lower()
    
    if choice == 'y':
        if kill_process_on_port(preferred_port):
            print(f"✅ 포트 {preferred_port} 정리 완료")
            start_server(preferred_port)
            return
    
    # 3. 다른 포트 찾기
    print("🔍 사용 가능한 다른 포트를 찾는 중...")
    free_port = find_free_port(8001, 8010)
    
    if free_port:
        print(f"✅ 포트 {free_port}을 사용합니다.")
        start_server(free_port)
    else:
        print("❌ 사용 가능한 포트를 찾을 수 없습니다.")
        print("포트 8000-8010이 모두 사용 중입니다.")

if __name__ == "__main__":
    main()
