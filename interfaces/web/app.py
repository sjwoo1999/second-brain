"""FastAPI 웹 앱."""

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from .routes import chat_router, graph_router, cost_router
from .websocket.handler import ws_handler


def create_app() -> FastAPI:
    """FastAPI 앱 생성."""

    app = FastAPI(
        title="Second Brain",
        description="뇌 시각화 웹 앱 - AI와 대화하며 지식 그래프 생성",
        version="0.1.0"
    )

    # CORS 설정 (프론트엔드 개발 서버 허용)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",  # Vite 개발 서버
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API 라우터 등록
    app.include_router(chat_router)
    app.include_router(graph_router)
    app.include_router(cost_router)

    # WebSocket 엔드포인트
    @app.websocket("/ws/{session_id}")
    async def websocket_endpoint(websocket: WebSocket, session_id: str):
        """WebSocket 연결 처리."""
        await ws_handler.handle_connection(websocket, session_id)

    # 헬스체크
    @app.get("/health")
    async def health_check():
        """서버 상태 확인."""
        return {"status": "healthy"}

    # 프론트엔드 정적 파일 서빙 (빌드 후)
    frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
    if frontend_dist.exists():
        app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")

        @app.get("/")
        async def serve_frontend():
            """프론트엔드 메인 페이지."""
            return FileResponse(frontend_dist / "index.html")

    return app


# 앱 인스턴스
app = create_app()
