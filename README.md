# Second Brain

AI와 대화하며 지식 그래프를 생성하는 개인 지식 관리 시스템

## 기능

- 3D 지식 그래프 시각화
- Claude AI 기반 대화 인터페이스
- 실시간 WebSocket 통신
- 시스템 트레이 지원
- Windows 데스크탑 앱 (Tauri)

## 기술 스택

### Frontend
- React 19 + TypeScript
- Tailwind CSS 4
- Three.js (react-force-graph-3d)
- Zustand (상태 관리)
- Vite

### Backend
- Python 3.11+
- FastAPI + Uvicorn
- Anthropic Claude API
- WebSocket

### Desktop App
- Tauri 2
- Rust

## 설치

### 요구 사항
- Node.js 18+
- Python 3.11+
- Rust (rustc 1.70+)

### 환경 설정

1. **Python 의존성 설치**
```bash
pip install -r requirements.txt
```

2. **환경 변수 설정**
```bash
cp .env.example .env
# .env 파일에 ANTHROPIC_API_KEY 설정
```

3. **Frontend 의존성 설치**
```bash
cd interfaces/frontend
npm install
```

## 실행

### 개발 모드

**Backend + Frontend 분리 실행:**
```bash
# 터미널 1: Backend
python run_web.py

# 터미널 2: Frontend
cd interfaces/frontend
npm run dev
```

**Tauri 개발 모드:**
```bash
cd interfaces/frontend
cargo tauri dev
```

### 프로덕션 빌드

**Python Backend exe 빌드:**
```bash
pyinstaller backend.spec --noconfirm
# 결과: dist/python-backend-x86_64-pc-windows-msvc.exe
```

**Tauri 앱 빌드:**
```bash
cd interfaces/frontend
cargo tauri build
# 결과: src-tauri/target/release/second-brain.exe
```

## 프로젝트 구조

```
second-brain/
├── config/              # 설정
├── core/                # 핵심 모듈
├── interfaces/
│   ├── frontend/        # React 프론트엔드
│   │   └── src-tauri/   # Tauri 설정
│   └── web/             # FastAPI 백엔드
├── tools/               # 도구 모듈
├── backend_main.py      # PyInstaller 엔트리포인트
├── backend.spec         # PyInstaller 설정
├── run_web.py           # 개발용 서버 실행
└── requirements.txt
```

## API

- `GET /health` - 서버 상태 확인
- `POST /api/chat` - 채팅 메시지 전송
- `GET /api/graph` - 그래프 데이터 조회
- `WS /ws/{session_id}` - WebSocket 연결

## 라이선스

MIT
