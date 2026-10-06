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

## 6.5 国际化

| 检查项 | 结果 |
| --- | --- |
| 抽取字符串 | 14 个 context / 191 条 |
| 英文翻译完成度 | 191 / 191 |
| check-i18n en_US | 6 / 6 关键字符串命中，退出码 0 |
| check-i18n zh_CN | 0 / 6 命中（源语言，全部回退到源字符串），退出码 0 |
| fmd_en.qm | 21337 bytes |
| fmd_zh_CN.qm | 26 bytes（空。中文靠 Qt 回退机制，不依赖翻译文件） |

中文是源码语言，因此**中文界面永远可用**，不会因为翻译文件缺失或损坏而变成空白。

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

---

## 后端性能优化（阶段 2 附带）

### 优化前的认知与实测

最初以为"降 imgsz 能提速"。实测否决了这个想法：

| imgsz | 单张耗时 |
| --- | --- |
| 320 | 21.1 ms |
| 416 | 23.0 ms |
| 640 | 20.9 ms |

**三者几乎无差别** —— 说明瓶颈不在 GPU 算力（yolov12n 只有 5.9 GFLOPs），
而在 ultralytics `predict()` 的固定开销：构建 source 加载器、letterbox、
NMS、构造 Results 对象。所以好的做法是**摊薄它**，不是缩小它。

### 批量 predict 的规模曲线

| 批大小 | 总耗时 | 每张 | 相对单张 |
| --- | --- | --- | --- |
| 1 | 20 ~ 26 ms | 20 ~ 26 ms | 1.0x |
| 2 | 24.19 ms | 12.10 ms | 2.2x |
| 4 | 31.27 ms | 7.82 ms | 3.4x |
| 8 | 46.19 ms | 5.77 ms | 4.6x |
| 16 | 88.18 ms | 5.51 ms | 4.8x |

### 服务端微批处理的实际效果

把并发推理请求聚成一批（`server/batching.py`），用一次 predict 处理。
**同一轮内的 A/B 对照**（12 张图，save=1）：

| 配置 | 批处理关闭 | 批处理开启 | 提升 |
| --- | --- | --- | --- |
| conc=1 | 10.7 张/秒 | 17.4 张/秒 | 1.6x |
| conc=4 | 11.5 张/秒 | 34.1 张/秒 | 3.0x |

⚠️ **注意**：关闭批处理时并发**完全不扩展**（10.7 → 11.5）。
开启后并发才正常发挥作用。

### ⚠️ 测量噪声的警告（重要）

同一配置在不同轮次之间的实测值能差 **2 倍**（例如"save=1 并发4"先后测到
36.7 / 44.7 / 23.9 / 25.3 张/秒）。这台机器上同时跑着许多进程，
加上 Windows Defender 的实时扫描，绝对数值非常不可靠。

**只有同一轮内的对照才有意义。** 上面所有"提升 x 倍"的结论都来自同一轮的 A/B。
这也是为什么代码里保留了 `FMD_BATCH=0/1`、`FMD_ASYNC_WRITE=0/1`、
`FMD_BATCH_WAIT_MS` 这些开关 —— 没有开关就只能"改代码前测一次、改完再测一次"，
而那种对比在噪声面前说明不了任何问题。

### 被数据否决的两个想法

**1. 模型 fuse（Conv+BN 融合）** —— 对 predict 没有影响（20.6 ms vs 20.0 ms，噪声内）。
ultralytics 内部已经处理了。

**2. 合批等待窗口** —— 曾默认 12 ms，用来"等更多请求凑成一批"。实测是净损失：

| 等待窗口 | conc=1 | conc=4 | 平均批大小 |
| --- | --- | --- | --- |
| 12 ms | 15.3 张/秒 | 49.9 张/秒 | 4.00 |
| **0 ms** | **19.2 张/秒** | **53.2 张/秒** | 2.00 |

等待换来的"更整齐的批"抵不过它给每个请求增加的延迟；而不等待时，
批处理器唤醒时队列里本来就有请求，平均批大小照样到 2。
所以默认值改成 0（机会性合批）。

### 另一项优化：原图写盘移出请求路径

`/detect` 默认 `save=1`，每次把原图同步写盘。实测（并发 4）：

| | 吞吐 | 并发扩展 |
| --- | --- | --- |
| save=0（不落盘） | 53.5 张/秒 | 3.46x |
| save=1（同步落盘） | 36.7 张/秒 | 2.08x |

Windows 上一次文件写要十几毫秒（杀毒实时扫描），瓶颈根本不在推理。
改成后台线程写盘（`storage.UploadWriter`）：路径在入队时算好并写进数据库，
文件随后落盘；读取端发现文件还没写完会短暂等待（实测最慢 259 ms），
所以不会出现"有记录却读不到图"。

### 单请求固定成本的构成

并发 1 时单张 65.5 ms，其中：

| 环节 | 耗时 |
| --- | --- |
| 图像解码（1300×956 JPEG） | 3.7 ms |
| 推理 | ~20 ms |
| HTTP / 调度 / 线程交接 | ~42 ms |

**固定开销是大头**，这也是为什么并发的收益远大于任何单点微优化 ——
以及为什么批处理能把吞吐拉起来。

---

## 摄像头与实时链路的性能预算

**这组数据决定了实时检测的整套架构**，所以单列一节。

测试环境：RTX 3060 Laptop / YOLOv12n / 本机 640×480 摄像头。

| 测量项 | 结果 | 对架构的影响 |
| --- | --- | --- |
| 推理 @imgsz=320 | 21.1 ms | **降 imgsz 不提速** |
| 推理 @imgsz=416 | 23.0 ms | 瓶颈在 ultralytics 框架开销（预处理 / NMS / 结果构造），不在 GPU 算力 |
| 推理 @imgsz=640 | 20.9 ms | 所以直接用 640，精度白拿 |
| 采集 DSHOW | 15.0 FPS | **DSHOW 只有 MSMF 的一半**，别迷信"DSHOW 最稳" |
| 采集 MSMF | **31.3 FPS** | 默认用 MSMF |
| 采集 ANY | 29.5 FPS | 自动选择即可 |
| cv2 画框（5 个框） | 0.12 ms | 几乎免费 |
| JPEG 编码 640×480 | 0.57 ms / 25.6 KB | 20fps 只需 0.5 MB/s，本机回环毫无压力 |
| 推理（`annotated=False`） | 19.63 ms | |
| **实时快路径合计** | **20.32 ms → 49.2 FPS** | 单路可跑满采集帧率 |
| 现有标注路径（PNG） | 69.69 ms → 14.4 FPS | **标注一项吃掉 50 ms**，实时路径不能复用它 |

**两条关键结论**：

1. **瓶颈在采集（31 FPS），不在推理（49 FPS）**。单路摄像头可以跑满帧率，不需要跳帧推理。
2. **现有标注路径慢 3.4 倍**，因为它走 PNG 编码。实时视频必须走独立的 JPEG 快路径。

### 测量方法

| 指标 | 方法 |
| --- | --- |
| 摄像头枚举与后端对比 | `cv2.VideoCapture(idx, backend)` 循环计数 2.5 秒 |
| 推理帧率 | `detector.get_detector().run_inference(image_data=frame, annotated=False)` 循环 20 次取平均 |
| 实时快路径 | 推理 + `cv2.rectangle`/`putText` + `cv2.imencode(".jpg", q=80)` |

两个必须注意的前提：

- `image_data` 接受 **numpy 数组**，不是裸字节（`app.py` 中先 `cv2.imdecode`）
- **CUDA 操作是异步的**：计时必须包 `torch.cuda.synchronize()`，
  否则测出来的只是 CPU 侧下发时间（曾因此测出"纯 H2D 拷贝 0.00 ms"这种不可能的值）
