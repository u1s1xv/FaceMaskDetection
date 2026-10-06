@echo off
rem FaceMaskDetection 客户端打包脚本
rem
rem 关键点：必须把 D:\Qt 的 bin 放在 PATH 最前面。
rem 本机 PATH 上的 qmake/Qt5*.dll 是 Anaconda 自带的另一套 Qt，
rem windeployqt 按 PATH 找依赖，会误抓 Anaconda 的 DLL 导致打包失败或运行崩溃。
setlocal

set "QT_DIR=D:\Qt\5.15.2\msvc2019_64"
set "VCVARS=C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"

if not exist "%QT_DIR%\bin\windeployqt.exe" ( echo [ERROR] Qt not found at %QT_DIR% & exit /b 1 )
set "PATH=%QT_DIR%\bin;%PATH%"

call "%VCVARS%" >nul 2>&1 || ( echo [ERROR] vcvars64 failed & exit /b 1 )
cd /d "%~dp0"

echo [1/3] 构建 release...
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH="%QT_DIR%" || exit /b 1
cmake --build build || exit /b 1

echo [2/3] 收集运行时依赖...
if exist dist rmdir /s /q dist
mkdir dist
copy /y build\fmd_client.exe dist\ >nul || exit /b 1
windeployqt --release --no-translations --no-compiler-runtime --no-opengl-sw dist\fmd_client.exe || exit /b 1

echo [3/3] 校验依赖来源（必须全部来自 %QT_DIR%）...
rem VersionInfo.FileName 返回的是 Qt 官方二进制的原始构建机路径，不能判断来源，必须比哈希
powershell -NoProfile -Command "$bad=0; Get-ChildItem dist -Filter Qt5*.dll | ForEach-Object { $src=Join-Path '%QT_DIR%\bin' $_.Name; if (-not (Test-Path $src) -or (Get-FileHash $_.FullName).Hash -ne (Get-FileHash $src).Hash) { Write-Host ('[FAIL] ' + $_.Name); $bad++ } }; if ($bad -eq 0) { Write-Host '[OK] Qt DLL 全部来自 %QT_DIR%' } else { exit 1 }"

echo.
echo [DONE] 产物在 dist\，可直接拷到其它机器运行
endlocal
