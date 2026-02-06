#!/usr/bin/env python3
"""웹 서버 실행 스크립트."""

import uvicorn
from config.settings import settings


def main():
    """웹 서버 시작."""
    print(f"""
╔══════════════════════════════════════════════════╗
║           🧠 Second Brain Web Server             ║
╠══════════════════════════════════════════════════╣
║  Backend:  http://{settings.web_host}:{settings.web_port}                  ║
║  API Docs: http://{settings.web_host}:{settings.web_port}/docs             ║
║  Frontend: http://localhost:5173 (별도 실행 필요)  ║
╚══════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "interfaces.web.app:app",
        host=settings.web_host,
        port=settings.web_port,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()
