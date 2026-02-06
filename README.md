# Second Brain

AI 기반 개인 지식 관리 시스템 — 대화하며 자동으로 지식을 축적하고, 그래프로 시각화하며, 맥락에 맞게 기억을 활용합니다.

## 주요 기능

### AI 대화
- Claude API (Opus / Sonnet / Haiku) 멀티 모델 지원
- 질문 복잡도에 따른 자동 모델 라우팅으로 비용 최적화
- 프롬프트 캐싱 및 대화 요약을 통한 토큰 절약

### 지식 그래프
- 대화 중 핵심 개념을 자동 노드로 추출
- React Force Graph 3D 기반 실시간 시각화
- 노드 간 관계를 통한 지식 탐색

### 개인 메모리
- 대화에서 사용자 선호·사실·결정 등을 자동 추출 (Haiku 기반)
- SQLite FTS5 전문 검색으로 빠른 메모리 조회
- 새 대화 시 관련 메모리를 시스템 프롬프트에 자동 주입

## 기술 스택

| 레이어 | 기술 |
|--------|------|
| **Backend** | Python 3.10+, FastAPI, WebSocket, Anthropic SDK |
| **Frontend** | React 19, TypeScript, Zustand, Tailwind CSS 4 |
| **시각화** | react-force-graph-3d, Three.js |
| **데이터** | SQLite (FTS5), 파일 기반 지식 저장 |
| **Desktop** | Tauri 2 (Rust) |

## 프로젝트 구조

```
second-brain/
├── config/                 # 설정 (settings.py)
├── core/                   # 핵심 로직
│   ├── orchestrator.py     #   대화 오케스트레이터
│   └── memory_service.py   #   메모리 CRUD·검색 서비스
├── interfaces/
│   ├── frontend/           # React 프론트엔드
│   │   ├── src/
│   │   │   ├── components/ #   UI 컴포넌트
│   │   │   ├── stores/     #   Zustand 상태 관리
│   │   │   └── hooks/      #   커스텀 훅 (WebSocket 등)
│   │   └── src-tauri/      #   Tauri 데스크톱 설정
│   └── web/                # FastAPI 웹 서버
│       ├── app.py          #   앱 진입점
│       ├── routes/         #   REST API 라우트
│       ├── services/       #   비즈니스 서비스
│       ├── models/         #   Pydantic 모델
│       └── websocket/      #   WebSocket 핸들러
├── knowledge/              # 지식 데이터 저장소
├── data/                   # SQLite DB 등 런타임 데이터
├── scripts/                # 빌드·유틸 스크립트
├── run_web.py              # 웹 서버 실행 스크립트
└── requirements.txt        # Python 의존성
```

## 시작하기

### 1. 환경 변수 설정

```bash
cp .env.example .env
```

`.env` 파일에 API 키를 입력합니다:

```env
ANTHROPIC_API_KEY=sk-ant-...    # 필수
DISCORD_BOT_TOKEN=              # 선택
GITHUB_TOKEN=ghp_...            # 선택
```

### 2. 백엔드 설치 및 실행

```bash
pip install -r requirements.txt
python run_web.py
```

백엔드가 `http://127.0.0.1:8000`에서 시작됩니다.

### 3. 프론트엔드 설치 및 실행

```bash
cd interfaces/frontend
npm install
npm run dev
```

브라우저에서 `http://localhost:5173`으로 접속합니다.

## 아키텍처

```
┌────────────────┐         WebSocket          ┌──────────────────┐
│                │  ◄────────────────────────► │                  │
│   React App    │     /ws/{session_id}        │   FastAPI Server │
│                │  ◄────────────────────────► │                  │
│  - ChatPanel   │         REST API            │  - Orchestrator  │
│  - GraphView   │     /api/chat, graph,       │  - MemoryService │
│  - MemoryPanel │     cost, memory            │  - CostTracker   │
│                │                             │                  │
└────────────────┘                             └────────┬─────────┘
                                                        │
                                               ┌────────▼─────────┐
                                               │   Claude API     │
                                               │  (Opus/Sonnet/   │
                                               │   Haiku)         │
                                               └────────┬─────────┘
                                                        │
                                               ┌────────▼─────────┐
                                               │   SQLite + FTS5  │
                                               │   (memory.db)    │
                                               └──────────────────┘
```

**동작 흐름:**
1. 사용자가 메시지를 입력하면 WebSocket으로 백엔드에 전송
2. Orchestrator가 질문 복잡도를 분석하여 적절한 모델 선택
3. 관련 메모리를 검색해 시스템 프롬프트에 주입
4. Claude API 호출 후 응답을 WebSocket으로 실시간 전송
5. 백그라운드에서 대화 내용으로부터 메모리를 자동 추출·저장

## API 엔드포인트

### REST API

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `GET` | `/health` | 서버 상태 확인 |
| `POST` | `/api/chat` | 채팅 메시지 전송 |
| `GET` | `/api/graph` | 지식 그래프 데이터 조회 |
| `GET` | `/api/cost` | 비용 통계 조회 |
| `GET` | `/api/memory` | 메모리 목록 조회 |
| `POST` | `/api/memory` | 메모리 생성 |
| `GET` | `/api/memory/search?q=` | 메모리 검색 (FTS5) |
| `GET` | `/api/memory/stats` | 메모리 통계 |

### WebSocket

`ws://127.0.0.1:8000/ws/{session_id}`

| 방향 | 타입 | 설명 |
|------|------|------|
| `→` | `chat` | 사용자 메시지 전송 |
| `→` | `get_graph` | 그래프 데이터 요청 |
| `→` | `get_cost` | 비용 정보 요청 |
| `→` | `clear_history` | 대화 기록 초기화 |
| `←` | `response` | AI 응답 |
| `←` | `processing` | 처리 상태 (started/completed) |
| `←` | `graph_update` | 그래프 데이터 갱신 |
| `←` | `node_added` | 새 노드 추가 알림 |
| `←` | `cost_update` | 비용 정보 갱신 |
| `←` | `memory_added` | 새 메모리 추출 알림 |
| `←` | `memory_stats` | 메모리 통계 갱신 |

API 문서(Swagger UI)는 서버 실행 후 `http://127.0.0.1:8000/docs`에서 확인할 수 있습니다.

## 빌드

데스크톱 앱 빌드(Tauri) 및 상세 빌드 가이드는 [BUILD.md](BUILD.md)를 참고하세요.

## 라이선스

MIT
