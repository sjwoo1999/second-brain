# Second Brain - Python Backend 빌드 스크립트
# PyInstaller를 사용하여 Python 백엔드를 EXE로 패키징

param(
    [switch]$Clean = $false
)

$ErrorActionPreference = "Stop"

# 프로젝트 루트 디렉토리
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not $ProjectRoot) {
    $ProjectRoot = (Get-Location).Path -replace "\\scripts$", ""
}

Write-Host "=== Second Brain Backend 빌드 시작 ===" -ForegroundColor Cyan
Write-Host "프로젝트 루트: $ProjectRoot" -ForegroundColor Gray

# 가상환경 확인 및 활성화
$VenvPath = "$ProjectRoot\.venv"
if (Test-Path "$VenvPath\Scripts\Activate.ps1") {
    Write-Host "가상환경 활성화 중..." -ForegroundColor Yellow
    & "$VenvPath\Scripts\Activate.ps1"
}

# PyInstaller 설치 확인
Write-Host "PyInstaller 확인 중..." -ForegroundColor Yellow
$pyinstaller = pip show pyinstaller 2>$null
if (-not $pyinstaller) {
    Write-Host "PyInstaller 설치 중..." -ForegroundColor Yellow
    pip install pyinstaller
}

# 빌드 디렉토리 설정
$BuildDir = "$ProjectRoot\build"
$DistDir = "$ProjectRoot\dist"
$TargetDir = "$ProjectRoot\interfaces\frontend\src-tauri\binaries"

# 기존 빌드 정리
if ($Clean) {
    Write-Host "기존 빌드 정리 중..." -ForegroundColor Yellow
    if (Test-Path $BuildDir) { Remove-Item -Recurse -Force $BuildDir }
    if (Test-Path $DistDir) { Remove-Item -Recurse -Force $DistDir }
}

# PyInstaller 빌드 실행
Write-Host "PyInstaller 빌드 실행 중..." -ForegroundColor Yellow

$PyInstallerArgs = @(
    "--onefile"
    "--name=python-backend-x86_64-pc-windows-msvc"
    "--distpath=$DistDir"
    "--workpath=$BuildDir"
    "--specpath=$BuildDir"
    "--clean"
    # 필요한 데이터 파일 포함
    "--add-data=config;config"
    "--add-data=core;core"
    "--add-data=interfaces;interfaces"
    "--add-data=knowledge;knowledge"
    "--add-data=tools;tools"
    # Hidden imports
    "--hidden-import=uvicorn"
    "--hidden-import=uvicorn.logging"
    "--hidden-import=uvicorn.loops"
    "--hidden-import=uvicorn.loops.auto"
    "--hidden-import=uvicorn.protocols"
    "--hidden-import=uvicorn.protocols.http"
    "--hidden-import=uvicorn.protocols.http.auto"
    "--hidden-import=uvicorn.protocols.websockets"
    "--hidden-import=uvicorn.protocols.websockets.auto"
    "--hidden-import=uvicorn.lifespan"
    "--hidden-import=uvicorn.lifespan.on"
    "--hidden-import=fastapi"
    "--hidden-import=starlette"
    "--hidden-import=pydantic"
    "--hidden-import=anthropic"
    # 콘솔 숨김 (릴리즈용)
    "--noconsole"
    # 엔트리 포인트
    "$ProjectRoot\run_web.py"
)

Push-Location $ProjectRoot
try {
    pyinstaller @PyInstallerArgs

    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller 빌드 실패"
    }

    # 빌드된 EXE를 Tauri binaries 폴더로 복사
    Write-Host "바이너리를 Tauri 폴더로 복사 중..." -ForegroundColor Yellow

    if (-not (Test-Path $TargetDir)) {
        New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
    }

    $SourceExe = "$DistDir\python-backend-x86_64-pc-windows-msvc.exe"
    $TargetExe = "$TargetDir\python-backend-x86_64-pc-windows-msvc.exe"

    if (Test-Path $SourceExe) {
        Copy-Item -Path $SourceExe -Destination $TargetExe -Force
        Write-Host "빌드 완료!" -ForegroundColor Green
        Write-Host "출력 파일: $TargetExe" -ForegroundColor Gray

        $FileSize = (Get-Item $TargetExe).Length / 1MB
        Write-Host "파일 크기: $([math]::Round($FileSize, 2)) MB" -ForegroundColor Gray
    } else {
        throw "빌드된 EXE 파일을 찾을 수 없습니다: $SourceExe"
    }
}
finally {
    Pop-Location
}

Write-Host "`n=== 빌드 완료 ===" -ForegroundColor Cyan
Write-Host "다음 단계: npm run tauri:build" -ForegroundColor Yellow
