@echo off
rem FaceMaskDetection Qt5 客户端构建脚本（M0 已验证可用）
setlocal

set "QT_DIR=D:\Qt\5.15.2\msvc2019_64"
set "VCVARS=C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"

if not exist "%QT_DIR%\bin\qmake.exe" (
  echo [ERROR] Qt5 not found at %QT_DIR%
  exit /b 1
)

call "%VCVARS%" >nul 2>&1
if errorlevel 1 ( echo [ERROR] vcvars64 failed & exit /b 1 )

cd /d "%~dp0"

cmake -S . -B build -G Ninja ^
  -DCMAKE_BUILD_TYPE=Release ^
  -DCMAKE_PREFIX_PATH="%QT_DIR%" || exit /b 1

cmake --build build || exit /b 1

echo.
echo [BUILD OK] build\fmd_client.exe
endlocal
