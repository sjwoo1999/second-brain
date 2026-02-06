# 세컨드 브레인 - 빌드 가이드

## 요구사항

### 1. Rust 설치
```powershell
# rustup 설치 (https://rustup.rs/)
winget install Rustlang.Rustup

# 또는 직접 다운로드
# https://www.rust-lang.org/tools/install
```

설치 후 터미널을 재시작하고 확인:
```powershell
rustc --version
cargo --version
```

### 2. Node.js (이미 설치됨)
```powershell
node --version  # v18+ 권장
npm --version
```

### 3. Python (백엔드 빌드용)
```powershell
python --version  # 3.10+
pip install pyinstaller
```

---

## 빌드 단계

### Step 1: Python 백엔드 EXE 빌드
```powershell
cd D:\workspace\second-brain
.\scripts\build-backend.ps1
```

이 스크립트가 `interfaces/frontend/src-tauri/binaries/` 폴더에
`python-backend-x86_64-pc-windows-msvc.exe`를 생성합니다.

### Step 2: Tauri 앱 빌드
```powershell
cd D:\workspace\second-brain\interfaces\frontend
npm run tauri:build
```

빌드 결과물:
- `src-tauri/target/release/세컨드 브레인.exe` (실행 파일)
- `src-tauri/target/release/bundle/nsis/세컨드 브레인_0.1.0_x64-setup.exe` (설치 파일)

---

## 개발 모드 실행

### 방법 1: 분리 실행 (권장)
터미널 1 - Python 백엔드:
```powershell
cd D:\workspace\second-brain
python run_web.py
```

터미널 2 - Tauri 개발 모드:
```powershell
cd D:\workspace\second-brain\interfaces\frontend
npm run tauri:dev
```

### 방법 2: 웹 브라우저로 개발
```powershell
# 백엔드
python run_web.py

# 프론트엔드 (별도 터미널)
cd interfaces/frontend
npm run dev
```

---

## 아이콘 설정

`src-tauri/icons/` 폴더에 다음 아이콘 파일이 필요합니다:
- `32x32.png`
- `128x128.png`
- `128x128@2x.png` (256x256)
- `icon.ico` (Windows)
- `icon.icns` (macOS)
- `icon.png` (트레이용)

Tauri 아이콘 생성기 사용:
```powershell
npm run tauri icon path/to/your-icon.png
```

---

## 문제 해결

### Rust 빌드 오류
```powershell
# Visual C++ Build Tools 설치 필요
winget install Microsoft.VisualStudio.2022.BuildTools
```

### WebSocket 연결 실패
백엔드가 실행 중인지 확인:
```powershell
curl http://localhost:8000/health
```

### Sidecar 실행 오류
1. `python-backend-x86_64-pc-windows-msvc.exe` 파일이 존재하는지 확인
2. 파일명이 정확히 일치하는지 확인 (아키텍처 suffix 포함)
