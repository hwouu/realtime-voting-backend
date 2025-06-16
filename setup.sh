#!/bin/bash

# 실시간 투표 플랫폼 백엔드 설정 스크립트
# 모든 의존성 문제를 해결하는 원스톱 스크립트

echo "🗳️ 실시간 투표 플랫폼 백엔드 설정을 시작합니다..."

# 1. 현재 디렉토리 확인
if [ ! -f "main.py" ]; then
    echo "❌ 프로젝트 루트 디렉토리에서 실행해주세요."
    exit 1
fi

echo "✅ 프로젝트 루트 디렉토리 확인됨"

# 2. Python 버전 확인
python_version=$(python3 --version 2>&1)
echo "📍 Python 버전: $python_version"

# 3. 가상환경 생성 (없는 경우)
if [ ! -d "venv" ]; then
    echo "📦 가상환경을 생성합니다..."
    python3 -m venv venv
    echo "✅ 가상환경 생성 완료"
fi

# 4. 가상환경 활성화
echo "🔄 가상환경을 활성화합니다..."
source venv/bin/activate

# 5. pip 업그레이드
echo "⬆️ pip를 업그레이드합니다..."
pip install --upgrade pip

# 6. 의존성 설치
echo "📦 의존성 패키지를 설치합니다..."
pip install -r requirements.txt

# 7. 환경 변수 파일 확인
if [ ! -f ".env" ]; then
    echo "⚙️ .env 파일을 생성합니다..."
    cp .env.example .env 2>/dev/null || echo "DEBUG=true
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
DATABASE_URL=sqlite:///./voting_app.db" > .env
    echo "✅ .env 파일 생성 완료"
fi

# 8. 데이터베이스 초기화
echo "🗄️ 데이터베이스를 초기화합니다..."
python -c "
import asyncio
import sys
sys.path.append('.')
from app.database.session import init_db

async def main():
    await init_db()
    print('✅ 데이터베이스 초기화 완료')

if __name__ == '__main__':
    asyncio.run(main())
"

# 9. 패키지 import 테스트
echo "🧪 패키지 import를 테스트합니다..."
python test_imports.py

echo ""
echo "🎉 설정이 완료되었습니다!"
echo ""
echo "🚀 서버를 시작하려면 다음 명령어를 실행하세요:"
echo "   source venv/bin/activate"
echo "   python main.py"
echo ""
echo "또는 시작 스크립트를 사용하세요:"
echo "   python start_server.py"
echo ""
echo "📚 API 문서: http://localhost:8000/docs"
echo "🔌 WebSocket: ws://localhost:8000/ws"
