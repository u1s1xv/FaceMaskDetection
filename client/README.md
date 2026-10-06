# FaceMaskDetection 客户端（C++/Qt5）

智能口罩检测系统的上位机客户端。与 Python 推理服务以 HTTP 通信，双进程架构。

> 架构设计与决策依据见 [../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)
> 性能实测数据见 [../docs/BENCHMARK.md](../docs/BENCHMARK.md)

## 环境要求

| 组件 | 版本 | 说明 |
|---|---|---|
| Qt | 5.15.2 msvc2019_64 | 本机路径 `D:\Qt\5.15.2\msvc2019_64` |
| 编译器 | MSVC 2022 (14.4x) | 与 msvc2019_64 套件二进制兼容 |
| CMake | ≥ 3.16 | VS2022 自带，或 `D:\Qt\Tools\CMake_64` |
| Ninja | 任意 | VS2022 自带，或 `D:\Qt\Tools\Ninja` |
| Python | conda env `med-yolo` | 3.12 + torch 2.7.1+cu126 + ultralytics 8.3.158 |

> ⚠️ **PATH 上的 qmake 是 Anaconda 自带的另一套 Qt**。
> 构建脚本已用 `CMAKE_PREFIX_PATH` 显式指向 `D:\Qt`，不要绕过它直接跑 qmake，
> 否则会链到 Anaconda 的 DLL，导致运行崩溃或打包失败。

## 构建

```bat
build.bat
```

脚本会依次执行 `vcvars64` → `cmake 配置` → `ninja 构建` → **windeployqt 部署 Qt 运行时**，
产物在 `build\fmd_client.exe`，**可以直接双击运行**（Qt DLL 已拷到旁边）。

> 部署这一步不是可选的：本机 PATH 上有另一套（MinGW 版）Qt，
> 如果 exe 旁边没有自己的 Qt DLL，运行时会加载到不兼容的那套而报错。详见「故障排查」。

## 运行

```bat
build\fmd_client.exe
```

客户端会自动用 `QProcess` 拉起 `../server/app.py`，轮询 `/health` 直到就绪。
服务崩溃会自动重启（最多 5 次，带退避）。

Python 解释器与服务脚本路径可以在「设置」页修改，持久化到 QSettings。

## 打包发布

```bat
deploy.bat
```

产物在 `dist\`（约 30 MB），可直接拷贝到其它机器运行。脚本末尾会**按哈希校验**
每个 Qt DLL 确实来自 `D:\Qt`，防止混入 Anaconda 的版本。

## 单元测试

```bat
cd tests
run_tests.bat
```

目前覆盖 `SseParser` 的 9 个用例，重点钉死 SSE **半帧**问题。

## 无界面验证入口

全部功能都可以在没有人、没有显示器的情况下验证，便于 CI 或远程调试：

| 命令 | 验证内容 |
|---|---|
| `--selftest <图片>` | 端到端：拉起服务 → 健康检查 → 列模型 → 推理 |
| `--smoke-ui <图片>` | 界面链路：主窗口 → 线程池解码 → 推理 → 结果回填 |
| `--smoke-batch <目录> <N>` | 批量调度：队列 / 背压 / 进度 / 取消 |
| `--smoke-history` | 历史三级链路：列表 → 详情 → 原图 |
| `--smoke-settings <端口>` | 配置链路：QSettings → 进程 → 客户端 |
| `--smoke-llm` | 流式分析：SSE 增量解析 |
| `--benchmark <图片> <N>` | 性能基准，输出 Markdown 表格 |
| `--check-i18n --lang <语言>` | 国际化：验证翻译文件加载与关键字符串命中 |
| `--list-langs` | 列出可用界面语言 |
| `--screenshot <png> [页号] [等待ms]` | 用 Qt 自己渲染窗口存图，用于界面评审 |
| `--dump-layout` | 打印屏幕信息与整棵控件树的几何数据，排查布局问题 |

全部通过时退出码为 0。

## 故障排查

### 弹窗「无法定位程序输入点 ?viewportSizeHint@QTableView@@...」

**原因**：exe 链接的是 `D:\Qt\5.15.2\msvc2019_64`（MSVC 版），运行时却加载到了
PATH 上另一套 Qt —— 本机 PATH 里有 `D:\Qt\5.15.2\mingw81_64\bin`（**MinGW 版**），
两者 ABI 不兼容，符号对不上。

**为什么现在不该再出现**：`build.bat` 构建后会自动跑 windeployqt，把 Qt DLL 与插件拷到
`build\` 目录。Windows 的 DLL 搜索顺序是「exe 目录 > 系统目录 > PATH」，exe 旁边有正确的 Qt
就不会被 PATH 抢走。

**若仍然出现**，检查三件事：

```bat
REM 1) build 目录里是否有 Qt5Core/Gui/Widgets/Network.dll 与 platforms\qwindows.dll
dir build\Qt5*.dll
dir build\platforms

REM 2) 这些 DLL 是否来自 D:\Qt（而不是别处）
powershell -Command "Get-ChildItem build\Qt5*.dll | %% { $_.Name + ' ' + (Get-FileHash $_.FullName).Hash.Substring(0,8) }"

REM 3) 重新执行完整构建（含部署步骤）
build.bat
```

> 另一个独立问题：**改过公共头文件后如果出现莫名崩溃（堆损坏 0xC0000374）**，
> 先执行 `rmdir /s /q build` 再重新构建。增量构建有时不会重编所有依赖方，
> 导致不同编译单元对同一结构体的内存布局理解不一致。

### 界面某个面板看起来"不见了"

先别下结论 —— **用 `CopyFromScreen` 截的图不可信**：截图进程若是 DPI-unaware 的，
在高缩放屏幕上会拿到被虚拟化处理的画面。正确做法：

```bat
build\fmd_client.exe --dump-layout          REM 看控件几何数据（权威）
build\fmd_client.exe --screenshot ui.png 0  REM 用 Qt 自己渲染存图
```

## 国际化

```bat
build\fmd_client.exe --check-i18n --lang en_US
build\fmd_client.exe --lang en_US        REM 以英文界面启动
```

- 源码语言是中文，所以中文界面**不依赖翻译文件**（Qt 回退到源字符串）
- 英文翻译在 `resources/i18n/fmd_en.ts`，构建时由 lupdate/lrelease 自动处理
- 修改带 `tr()` 的文本后重新构建即可，lupdate 会自动更新 .ts
- 切换语言在「设置」页，保存后点「立即重启应用」生效

## 目录结构

```
src/
├── main.cpp                 入口 + 各验证模式
├── MainWindow.*             导航、页面栈、后端生命周期
├── core/                    与界面无关的基础设施
│   ├── Protocol.*           数据契约（JSON 解析集中于此）
│   ├── BackendClient.*      网络层（全异步）
│   ├── BackendProcess.*     QProcess 守护 + 崩溃重启
│   └── SseParser.*          SSE 增量解析（可独立单测）
├── models/                  Model/View
│   ├── HistoryModel.*       QAbstractTableModel
│   └── HistoryProxy.*       QSortFilterProxyModel
├── workers/
│   ├── ImageLoaderTask.*    QRunnable 文件解码
│   └── BatchController.*    批量调度 + 两级背压
└── views/                   页面与自定义图元
resources/                   QSS 主题 + qrc + i18n/*.ts
tests/                       Qt Test 单元测试
```
