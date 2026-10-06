@echo off
rem ===========================================================================
rem FaceMaskDetection Qt5 客户端构建脚本
rem
rem 用法: build.bat [clean]
rem
rem 为什么用 Visual Studio 生成器（MSBuild）而不是 Ninja：
rem
rem   Ninja 依赖 build.ninja 里的 msvc_deps_prefix 来识别编译器的头文件输出，
rem   从而生成头文件依赖。CMake 会把该前缀写成 "注意: 包含文件:" 的 UTF-8 形式，
rem   而中文区域的 cl.exe 实际输出的是 GBK 字节 —— 两边对不上，Ninja 就把所有
rem   include 行全部丢弃。
rem
rem   后果：**改任何头文件都不会触发对应的 .cpp 重编**，不同编译单元对同一个
rem   类/结构体的内存布局理解不一致，表现为：
rem     * 程序一启动就崩（0xC0000374 堆损坏 / 0xC0000005 访问违例），且常常没有任何输出
rem     * 链接期 LNK2019 找不到刚加的函数
rem   本项目排查期间因此类问题往返了四次，最后定位到这个前缀编码问题。
rem
rem   MSBuild 由编译器自己解析 /showIncludes，不受编码影响，依赖追踪是正确的。
rem ===========================================================================
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

if /i "%~1"=="clean" (
  echo [0/3] 清理构建目录...
  if exist build rmdir /s /q build
)

cmake -S . -B build -G "Visual Studio 17 2022" -A x64 ^
  -DCMAKE_PREFIX_PATH="%QT_DIR%" || exit /b 1

cmake --build build --config Release || exit /b 1

echo.
echo [BUILD OK] build\bin\fmd_client.exe
endlocal
