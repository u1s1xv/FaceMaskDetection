# 性能实测数据

> 所有数据都在本机实测得到，可用 ``fmd_client.exe --benchmark`` 复现。
> 面试时直接给面试官看这张表，比任何形容词都有说服力。

---

## 测试环境

| 项 | 值 |
|---|---|
| CPU / GPU | NVIDIA GeForce RTX 3060 Laptop (6 GB)，驱动 617.14 |
| 操作系统 | Windows 10 (10.0.26100) |
| 编译器 | MSVC 14.44 (VS2022 Community) |
| Qt | 5.15.2 (msvc2019_64 套件，release 构建) |
| Python | 3.12.11 (conda env ``med-yolo``) |
| PyTorch | 2.7.1+cu126，CUDA 可用 |
| Ultralytics | 8.3.158 |
| 模型 | ``train3_20250701-105710_yolov12n_best.pt``（5.22 MB，3 类） |
| 测试图片 | 1300×956 JPEG，109 KB |

---

## 1. 渲染方案对比（核心结论）

同一张图片、同样参数，各跑 4 次取平均：

| 方案 | 平均端到端耗时 | 响应体积 | base64 后传输量 |
|---|---|---|---|
| 服务端渲染 PNG + base64 回传 | **608 ms** | 1173.4 KB | 1564.6 KB |
| 客户端自绘（仅结构化 JSON） | **213 ms** | **约 2 KB** | 约 2 KB |

**结论：客户端自绘快 2.9 倍，传输体积小约 800 倍。**

开销差在哪里（服务端渲染多出的四段）：

1. 服务端把 1300×956 的图编码成 PNG（无损，体积大）
2. base64 编码，体积再 **×1.33**
3. 通过 HTTP 传输 1.5 MB
4. 客户端 base64 解码 + PNG 解码

**代价**：客户端要自己实现绘制。收益是矢量框可缩放、可悬停显示置信度，交互质量反而更高。

---

## 2. 推理尺寸对耗时的影响

| 推理尺寸 | 平均端到端耗时 | 相对 320 的增幅 |
|---|---|---|
| imgsz = 320 | 206 ms | — |
| imgsz = 640 | 213 ms | +3.4% |
| imgsz = 1280 | 260 ms | +26% |

**注意**：从 320 到 640 只增加 3.4%，说明**瓶颈不在模型推理本身**，而在固定的服务端开销（图片解码、JSON 序列化、HTTP 往返）。1280 才明显上升。

这条数据说明：调 imgsz 不是免费的，但也不是主要成本项——优化要看全链路。

---

## 3. 冷启动代价

| 阶段 | 耗时 |
|---|---|
| 首次请求（进程启动 + torch 导入 + CUDA 上下文 + 模型加载 + 首次推理） | **13677 ms** |
| 之后模型加载（已 import torch） | 130 ms |
| 稳定后单次端到端 | 约 213 ms |

**结论：冷启动的 13.7 秒几乎全在 ``import torch`` 和 CUDA 初始化上**，模型文件本身只有 5.22 MB、加载仅 130 ms。

这就是为什么客户端必须：

1. 用 ``QProcess`` 把服务**提前拉起**，而不是等用户点"检测"才启动
2. 启动后用 1 秒间隔轮询 ``/health``（最多 90 次），就绪后再放开功能
3. 连上后把轮询降频到 15 秒，避免无谓请求

---

## 4. 批量调度

6 张图片，并发设为 4：

| 指标 | 值 |
|---|---|
| 成功 / 失败 | 6 / 0 |
| 总耗时 | 15.2 s |
| 客户端进程退出码 | 0 |

> **反例记录**：修复前（服务端未串行化推理）同样的测试是 **3 成功 / 3 失败**。
> 原因见 ``docs/ARCHITECTURE.md`` 2.5 节：ultralytics 的模型实例不是线程安全的，
> ``ThreadingHTTPServer`` 下的并发请求会互相踩踏。这不是"调大并发就好了"的问题，
> 而是必须先在服务端串行化。

---

## 5. 大模型流式分析（SSE）

对一条检测记录发起分析：

| 指标 | 值 |
|---|---|
| 收到 content 帧数 | 21 |
| 累计字符数 | 242 |
| start / done 帧 | 均正常收到 |
| 模式 | 模拟模式（未配置 SILICONFLOW_API_KEY） |

**验证意义**：21 个分块分多次到达，说明 ``SseParser`` 的**增量解析**确实在工作——如果它必须等完整响应才能解析，客户端就不会逐块收到内容。

服务端主动把文本切成小块（每块 12 字符、间隔 10 ms）以模拟真实大模型的输出节奏，这样客户端的流式链路在没有 API Key 的环境下也能完整验证。

---

## 6. 单元测试

```
********* Start testing of TestSseParser *********
PASS   : TestSseParser::singleFrame()
PASS   : TestSseParser::multipleFramesInOneChunk()
PASS   : TestSseParser::frameSplitAcrossChunks()
PASS   : TestSseParser::splitAtDelimiterBoundary()
PASS   : TestSseParser::crlfLineEndings()
PASS   : TestSseParser::malformedJsonIsSkipped()
PASS   : TestSseParser::commentLinesIgnored()
PASS   : TestSseParser::resetClearsPendingBuffer()
PASS   : TestSseParser::byteByByteFeed()
Totals: 11 passed, 0 failed, 0 skipped
********* Finished testing of TestSseParser *********
```

其中 ``frameSplitAcrossChunks`` / ``splitAtDelimiterBoundary`` / ``byteByByteFeed`` 三个用例专门钉死**半帧**问题：TCP 是字节流，事件边界与 ``read()`` 返回边界无关，靠手工点击几乎不可能复现。

---

## 7. 复现方式

```bash
cd client

# 单元测试
cd tests && run_tests.bat

# 性能基准
build\fmd_client.exe --benchmark "<图片路径>" 4

# 其余链路验证（详见 docs/ARCHITECTURE.md 第 6 节）
build\fmd_client.exe --selftest     "<图片路径>"
build\fmd_client.exe --smoke-ui     "<图片路径>"
build\fmd_client.exe --smoke-batch  "<图片目录>" 6
build\fmd_client.exe --smoke-history
build\fmd_client.exe --smoke-settings 8899
build\fmd_client.exe --smoke-llm
```
