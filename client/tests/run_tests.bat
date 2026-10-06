@echo off
rem 单元测试构建与运行（用 Visual Studio 生成器，原因见 ..\build.bat 顶部说明）
setlocal
set "QT_DIR=D:\Qt\5.15.2\msvc2019_64"
set "VCVARS=C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"

call "%VCVARS%" >nul 2>&1 || ( echo [ERROR] vcvars64 failed & exit /b 1 )
cd /d "%~dp0"

cmake -S . -B build -G "Visual Studio 17 2022" -A x64 -DCMAKE_PREFIX_PATH="%QT_DIR%" || exit /b 1
cmake --build build --config Release || exit /b 1

set "PATH=%QT_DIR%\bin;%PATH%"
set "QT_QPA_PLATFORM=offscreen"
ctest --test-dir build -C Release --output-on-failure
endlocal
