# FaceMaskDetection

**C++/Qt5 上位机客户端 + Python 推理服务** 的口罩佩戴检测桌面系统。

客户端负责交互、渲染与任务调度，服务端只负责推理与数据 —— 两侧以 HTTP/JSON 通信，进程隔离。

![检测页](docs/screenshots/01-detect.png)

---

## 功能

| 能力 | 说明 |
|---|---|
| **单图检测** | 拖拽或打开图片，检测 `with_mask` / `without_mask` / `mask_weared_incorrect` 三类目标 |
| **批量检测** | 多选或整个文件夹入队，客户端按并发数排队调度，服务端串行推理；支持进度、取消、逐张结果预览 |
| **历史记录** | 每次检测自动入库，支持按文件名/时间/ID 搜索、只看违规、查看标注结果、删除 |
| **模型管理** | 扫描权重目录，展示体积与修改时间，可设为默认模型 |
| **AI 分析** | 调用大模型对检测结果做合规性分析，**SSE 流式**逐字返回 |
| **国际化** | 中英双语（Qt Linguist），191 条字符串，中文无需翻译文件 |

## 界面

| 单图检测 | 批量检测 |
|---|---|
| ![检测](docs/screenshots/01-detect.png) | ![批量](docs/screenshots/02-batch.png) |

| 历史记录 | 模型管理 | 设置 |
|---|---|---|
| ![历史](docs/screenshots/03-history.png) | ![模型](docs/screenshots/04-models.png) | ![设置](docs/screenshots/05-settings.png) |

---

## 架构

```
┌──────────────────────────────────┐          ┌──────────────────────────────────┐
│   C++17 / Qt 5.15 客户端          │          │   Python 推理服务                 │
│                                  │   HTTP   │   （仅标准库，零第三方依赖）        │
│  ├─ QProcess        进程守护      │ <──────> │                                  │
│  │                   崩溃自动重启  │  JSON    │  ├─ http.server   线程化 HTTP     │
│  ├─ QNetworkAccessManager 异步网络│  SSE     │  ├─ ultralytics   YOLOv12n 推理   │
│  ├─ QThreadPool     解码/任务调度 │          │  ├─ sqlite3       历史库          │
│  ├─ QGraphicsView   检测框自绘    │          │  └─ SiliconFlow   大模型分析      │
│  ├─ QAbstractTableModel 历史表格  │          │                                  │
│  └─ ChildProcessJob 作业对象守护  │          │                                  │
└──────────────────────────────────┘          └──────────────────────────────────┘
            约 4700 行 C++                            约 800 行 Python
```

**分工原则**：服务端刻意保持"薄"—— 一个职责，把图片变成结构化检测结果。所有交互、渲染、并发调度都在客户端，因此界面永远不阻塞。

## 技术栈

**客户端（本项目的重点）**

| 技术点 | 用在哪 |
|---|---|
| C++17 / Qt 5.15 Widgets | 全部界面 |
| **QProcess + Windows 作业对象** | 拉起并守护推理服务；客户端被强杀时后端不会变成孤儿进程 |
| **QNetworkAccessManager** | 全异步 HTTP，请求超时、错误分类、大图上传 |
| **SSE 增量解析** | 大模型流式输出，处理 TCP 半帧/粘包（`SseParser`，有独立单元测试） |
| **QThreadPool / QRunnable** | 图片解码放后台线程；批量任务队列 |
| **两级背压调度** | 预读上限 + 在途请求上限，避免一次性压爆服务端 |
| **QAbstractTableModel + QSortFilterProxyModel** | 历史记录表格，筛选逻辑与数据解耦 |
| **QGraphicsView + 自定义 QGraphicsItem** | 检测框自绘：矢量、可缩放、悬停显示置信度 |
| Qt Linguist | 中英双语 |
| CMake + MSBuild | 构建（为什么不用 Ninja 见下） |

**服务端**：Python 3.12 · ultralytics 8.3 · PyTorch 2.7 (CUDA) · SQLite · http.server

> **运行期数据**：历史库与上传原图都在 `data/`（已 gitignore）。原图默认保留 30 天、
> 总量上限 2 GB，服务启动时按策略清理（可用 `FMD_UPLOAD_RETENTION_DAYS` /
> `FMD_UPLOAD_MAX_MB` 覆盖）。只清原图，不删检测记录 —— 统计数据不受影响。

**模型**：YOLOv12n，3 类，约 5.2 MB

---

## 快速开始

### 环境要求

| 组件 | 版本 |
|---|---|
| Qt | 5.15.2 `msvc2019_64` |
| 编译器 | MSVC 2022 |
| CMake | ≥ 3.16 |
| Python | 3.12（需 torch + ultralytics，建议独立 conda 环境） |

### 构建并运行

```bat
cd client
build.bat            REM vcvars64 → CMake → MSBuild → windeployqt 部署 Qt 运行时
build\bin\fmd_client.exe
```

客户端启动时会自动拉起 `server/app.py` 并轮询健康检查，服务崩溃会自动重启。Python 解释器与端口可在「设置」页修改。

### 打包发布

```bat
cd client
deploy.bat           REM 产物在 dist\，可直接拷到其它机器运行
```

---

## 性能

同一张 1300×956 图片、同样参数，各跑 4 次取平均：

| 方案 | 端到端耗时 | 响应体积 |
|---|---|---|
| 服务端渲染 PNG + base64 回传 | 608 ms | 1565 KB |
| **客户端自绘（只回结构化 JSON）** | **213 ms** | **约 2 KB** |

**快 2.9 倍，体积小约 800 倍。** 两种模式都保留在界面上（「使用服务端渲染图」开关），可当场对比。

其他实测数据（冷启动 13.7 s 的构成、批量并发、推理尺寸影响）见 **[docs/BENCHMARK.md](docs/BENCHMARK.md)**。

---

## 设计说明

**[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** 记录了每项设计决策的**理由与代价**，包括：

- 为什么拆成两个进程，而不是用 pybind11 把 Python 嵌进 C++
- 为什么检测框由客户端画（有实测数据支撑）
- 批量并发为什么限制的是"在途请求数"而不是线程数
- 服务端为什么必须给推理加锁（一个真实 bug：并发时 6 张图挂 3 张）
- **构建系统为什么放弃 Ninja 改用 MSBuild** —— 中文区域 MSVC 下 `msvc_deps_prefix` 编码错乱，导致头文件依赖追踪整体失效，表现为"改头文件不重编、程序莫名崩溃"
- **原图为什么要设保留策略** —— 每检测一次存一份原图，无上限时几千次就能撑到 GB 级；以及为什么清理必须放后台线程

## 项目结构

```
FaceMaskDetection/
├── client/                 C++/Qt5 上位机客户端
│   ├── src/
│   │   ├── core/           与界面无关的基础设施
│   │   │   ├── Protocol.*        数据契约（JSON 解析集中于此）
│   │   │   ├── BackendClient.*   异步网络层
│   │   │   ├── BackendProcess.*  QProcess 守护
│   │   │   ├── ChildProcessJob.* 作业对象（防孤儿进程）
│   │   │   └── SseParser.*       SSE 增量解析
│   │   ├── models/         QAbstractTableModel + 代理
│   │   ├── workers/        QRunnable 与批量调度器
│   │   ├── views/          五个页面 + 自绘图元
│   │   └── widgets/        PageHeader / StatCard
│   ├── resources/          QSS 主题 + 图标 + i18n
│   └── tests/              Qt Test 单元测试
├── server/                 Python 推理服务（标准库）
├── yoloserver/             模型权重、训练/转换脚本（命令行工具）
└── docs/                   架构说明、性能数据、界面截图
```

---

## 测试

所有功能都有**无界面验证入口**，可在无人环境跑（CI / 远程调试）：

```bat
cd client
build\bin\fmd_client.exe --selftest "<图片>"     REM 端到端：拉起服务→健康检查→推理
build\bin\fmd_client.exe --smoke-batch "<目录>" 6  REM 批量调度
build\bin\fmd_client.exe --smoke-history          REM 历史列表→详情→原图
build\bin\fmd_client.exe --check-i18n --lang en_US REM 国际化
build\bin\fmd_client.exe --benchmark "<图片>" 4    REM 性能基准
```

全部通过时退出码为 0。另有 SseParser 单元测试（`cd client/tests && run_tests.bat`），覆盖 TCP 半帧、CRLF、坏帧、逐字节投喂等边界。

## 关于本项目

检测模型与数据来自早先的一个协作项目（原为 Django Web 应用）。当前版本将 Web 端整体替换为 C++/Qt 桌面客户端，并把推理逻辑从 Django 中解耦为独立服务 —— 原 Web 版本保留在 `pre-qt-migration` 标签中。
