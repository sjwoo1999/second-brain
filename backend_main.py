#!/usr/bin/env python3
"""Tauri sidecar용 백엔드 엔트리포인트."""

import sys
import os

# PyInstaller 패키징 시 경로 처리
if getattr(sys, 'frozen', False):
    # exe로 실행 시
    base_path = sys._MEIPASS
    os.chdir(os.path.dirname(sys.executable))
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

# 경로 추가
sys.path.insert(0, base_path)

import uvicorn
from interfaces.web.app import app


def main():
    """백엔드 서버 시작."""
    print("[Second Brain] Backend starting...")
    print("[Second Brain] API: http://127.0.0.1:8000")
    print("[Second Brain] Docs: http://127.0.0.1:8000/docs")

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
        # 프로덕션 설정
        reload=False,
        workers=1
    )


if __name__ == "__main__":
    main()
