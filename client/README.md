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

脚本会依次执行 `vcvars64` → `cmake 配置` → `ninja 构建`，产物在 `build\fmd_client.exe`。

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

全部通过时退出码为 0。

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
resources/                   QSS 主题 + qrc
tests/                       Qt Test 单元测试
```
