@echo off
rem 单元测试构建与运行
setlocal
set "QT_DIR=D:\Qt\5.15.2\msvc2019_64"
set "VCVARS=C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"

call "%VCVARS%" >nul 2>&1 || ( echo [ERROR] vcvars64 failed & exit /b 1 )
cd /d "%~dp0"

cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH="%QT_DIR%" || exit /b 1
cmake --build build || exit /b 1

set "PATH=%QT_DIR%\bin;%PATH%"
set "QT_QPA_PLATFORM=offscreen"
ctest --test-dir build --output-on-failure
endlocal
