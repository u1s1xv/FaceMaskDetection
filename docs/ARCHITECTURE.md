# FaceMaskDetection 客户端架构说明

> 本文档面向技术面试：说明**为什么这么设计**，以及每个决策付出的代价。

---

## 1. 项目定位

一个 **C++/Qt5 上位机客户端 + Python 推理服务**的双进程桌面系统，用于口罩佩戴检测。

```
┌──────────────────────────────┐         ┌──────────────────────────────┐
│   C++17 / Qt5.15 客户端       │  HTTP   │   Python 推理服务             │
│   ├─ QProcess 进程守护        │ <─────> │   ├─ 标准库 http.server       │
│   ├─ QNetworkAccessManager    │  JSON   │   ├─ ultralytics (YOLO)      │
│   ├─ QThreadPool 解码/任务调度 │         │   ├─ SQLite 历史库            │
│   ├─ QGraphicsView 自绘检测框  │         │   └─ SiliconFlow 大模型分析    │
│   └─ QAbstractTableModel 历史  │         │                              │
└──────────────────────────────┘         └──────────────────────────────┘
       约 7000 行 C++                          约 900 行 Python
```

**分工原则**：客户端负责交互、渲染、调度；服务端只负责推理与数据。服务端刻意保持"薄"——它只有一个职责，就是把图片变成结构化检测结果。

---

## 2. 关键设计决策

### 2.1 为什么拆成两个进程，而不是用 pybind11 把 Python 嵌进 C++？

| 考量 | 双进程 | pybind11 嵌入 |
|---|---|---|
| 崩溃隔离 | ✅ Python/ CUDA 段错误不会拖垮 UI | ❌ 一崩全崩 |
| GIL | 无影响 | 需要处理 GIL 与 Qt 线程的关系 |
| 部署 | 两侧独立升级 | 必须一起编译，PyTorch 体积拖进客户端 |
| 模型热更新 | 重启服务即可，UI 不断 | 需重新加载整个进程 |
| 调试 | 两侧可独立调试 | 混合调用栈很难看 |

**代价**：多了一次进程间通信。实测一次推理端到端 213 ms，其中纯推理约 80 ms，可见 IPC + 图片编解码的开销是存在的但可接受。

### 2.2 为什么 POST 的 body 直接是图像原始字节，不用 multipart？

服务端只需要一张图，没有其它字段。用裸字节后：

- Qt 侧直接 ``QNetworkAccessManager::post(request, QByteArray)``，**省掉 QHttpMultiPart 的构造与边界处理**
- 服务端不用解析 multipart，``cv2.imdecode(np.frombuffer(raw))`` 一行搞定
- 参数走 query string，仍然是标准 HTTP

**代价**：接口不够"通用"，一个请求只能传一张图。对本项目的使用场景是划算的。

### 2.3 为什么检测框由客户端画，而不是服务端烧进图片？（有实测数据支撑）

两种方案都实现了，实测对比（1300×956 图片，各 4 次取平均）：

| 方案 | 端到端耗时 | 响应体积 |
|---|---|---|
| 服务端渲染 PNG + base64 回传 | **608 ms** | **1565 KB** |
| 客户端自绘（只回结构化 JSON） | **213 ms** | **约 2 KB** |

**快 2.9 倍，体积小约 800 倍。** 差距来自服务端 PNG 编码、base64 编码（+33%）、传输、客户端解码四段开销。

**代价**：客户端要自己实现绘制逻辑。但换来的是矢量框——缩放不糊、可悬停显示置信度，交互质量反而更高。

> 这个开关保留在界面上（"使用服务端渲染图"），用于对比测试。

### 2.4 批量并发：限制的是"在途请求数"，不是线程数

推理在服务端是**串行**的（单张 GPU 一次只能跑一个模型）。客户端如果同时打 20 个请求过去，只会让服务端排队、内存上涨，进度反馈也失真。

所以 ``BatchController`` 采用两级背压：

1. **预读上限**：最多 ``maxConcurrent × 2`` 个文件同时在读，不把整批图片读进内存
2. **在途上限**：最多 ``maxConcurrent`` 个请求挂在网络上，完成一个补一个

派发后立刻释放图片字节，峰值内存 ≈ 并发数 × 单图大小。

界面上的"并发"下拉框可以直接改这个值，用于做并发调优对比。

### 2.5 服务端为什么要给推理加锁？（一个真实的 bug）

最初客户端并发 4 个请求时，**6 张图有 3 张失败**。原因是：

- HTTP 层用的是 ``ThreadingHTTPServer``，请求天然并发
- 但 ``ultralytics`` 的 YOLO 实例**不是线程安全的**，多个线程同时调 ``model.predict()`` 会互相踩踏
- 单张 GPU 本来也不可能真并行

修法是在推理处加锁串行化，并把**排队等待时间**记进结果（``queue_wait`` 字段），这样"并发到底有没有用"就有数据可依，而不是凭感觉。

### 2.6 中文编码：两端都强制 UTF-8

Windows 上这是必踩的坑：

- **Qt5 默认消息处理器用 ``toLocal8Bit()``**（中文机器上是 GBK），导致控制台、重定向文件、日志收集器三者编码不一致 → 装了自定义 ``qInstallMessageHandler`` 显式输出 UTF-8
- **Python 3 默认用系统本地编码写 stdout/stderr** → 启动子进程时注入 ``PYTHONUTF8=1`` 与 ``PYTHONIOENCODING=utf-8``
- **MSVC 编译中文源码**需要 ``/utf-8`` 编译选项

### 2.7 国际化：源码中文 + Qt Linguist 英文

界面文本一律用 @@@@tr()@@@@ 包裹，由 lupdate 抽取到 @@@@.ts@@@@，翻译后经 lrelease 编译成 @@@@.qm@@@@：

@@@@@@
源码 tr("检测")  --lupdate-->  resources/i18n/fmd_en.ts  --人工翻译-->
                --lrelease-->  build/i18n/fmd_en.qm  --QTranslator-->  运行时生效
@@@@@@

几个实际决定：

- **源码语言就是中文**，所以 @@@@fmd_zh_CN.qm@@@@ 是空的，运行时靠 Qt 的"回退到源字符串"机制显示中文。
  这意味着 **中文界面不依赖任何翻译文件**，翻译缺失永远不会让界面变空。
- **只翻译用户可见文本**。JSON 字段名、@@@@setObjectName@@@@ 的值、QSettings 的键都是 ASCII，
  刻意没有包 @@@@tr()@@@@ —— 把 @@@@objectName@@@@ 翻译掉会直接让 QSS 选择器失效。
- **非 QObject 类**（如 @@@@Protocol@@@@、@@@DetectionItem@@@@ 这类没有 QObject 基类的类型）
  不能用裸 @@@@tr()@@@@，改用 @@@@QCoreApplication::translate("上下文", "...")@@@@。
- **切换语言需要重启应用**。手写 UI（非 .ui 文件）没有现成的 @@@@retranslateUi()@@@@，
  要支持热切换得给每个页面实现重翻译逻辑，成本与收益不成正比。工业软件里重启生效也是常见做法，
  所以「设置」页提供了「立即重启应用」按钮（@@@@QProcess::startDetached@@@@ + 关闭当前实例，
  并确保先停掉后端进程）。

覆盖情况：14 个 context、191 条字符串，英文翻译 191/191 完成。

### 2.8 Model/View 的使用边界

刻意**没有**到处都用自定义模型：

| 场景 | 方案 | 理由 |
|---|---|---|
| 历史记录（可能上千条，需频繁筛选排序） | ``QAbstractTableModel`` + ``QSortFilterProxyModel`` | 视图按需取数，筛选逻辑与数据解耦，一个源模型可挂多个代理 |
| 批量结果（一次生成、条目有限） | ``QTableWidget`` | 上自定义模型是过度设计 |
| 模型列表（几条到几十条） | ``QTableWidget`` | 同上 |

能在面试里说清"什么时候**不**需要 Model/View"，比到处套用更有说服力。

---

### 2.8 存储治理：原图保留策略

每检测一次就把原图存一份到 `data/uploads/YYYY/MM/DD/`。这个设计本身没问题
（历史详情要能回看原图），但**没有上限就是缺陷**：

排查期间跑了 2653 次检测，`uploads/` 累积到 **985 MB**。真实使用只会更糟。

所以加了两道闸，**只删原图、不删数据库记录**：

| 闸门 | 规则 | 环境变量 | 默认值 |
| --- | --- | --- | --- |
| 按时间 | 超过保留天数的日期目录整体删除 | `FMD_UPLOAD_RETENTION_DAYS` | 30 天 |
| 按容量 | 仍超上限时，从最旧的目录继续删 | `FMD_UPLOAD_MAX_MB` | 2048 MB |

为什么保留记录而删原图：检测框、类别、耗时这些**结构化结果比原图有价值得多**，
原图丢了只是详情页看不到图，统计与检索完全不受影响。

同时修掉两个泄漏：`delete_record` 与 `clear_all` 此前只删数据库行，**图片文件永久留在磁盘上**。

#### 两个性能坑（都踩过，结论反直觉）

**一、清理必须放后台线程。** 它位于 `serve_forever()` 之前，同步执行时服务在
整个清理期间不接受连接 —— 实测 2000 个文件会让 `/health` 推迟十几秒，
客户端直接判定"后端启动失败"。改用 daemon 线程后，`/health` 恢复为只受导入耗时影响。

**二、删除速度由环境决定，不由代码决定。** 曾以为是逐文件 `stat()` 拖慢的，
改成 `os.scandir` 单次遍历后**耗时纹丝不动**。做位置对照实验才看清：

| 目录 | 删除 2000 个小文件 | 单个 |
| --- | --- | --- |
| `%TEMP%` | 2.4 s | 1.2 ms |
| 项目 `data/uploads/` | 31.0 s | 15.5 ms |
| `client/` | 31.0 s | 15.5 ms |
| `C:\` 盘根目录下 | 30.4 s | 15.2 ms |

同一个脚本、同一块盘，**只有 `%TEMP%` 快** —— 差异来自 Windows Defender 的实时扫描
（TEMP 通常在排除列表里）。项目目录、数据目录、甚至盘符根目录速度完全一致，
说明与"路径在不在项目里"无关。

> **教训**：优化前先做对照实验确认瓶颈归属。这次差点把一个环境开销当成算法问题去
> "优化"，还在代码里写下了错误的归因注释。最终保留了 `os.scandir` 版本（它确实少一轮
> 系统调用），但注释改成了实测结论 —— **错误的注释比没有注释更有害**。

### 2.9 构建系统：为什么放弃 Ninja 改用 MSBuild

一开始用 Ninja（快、跨平台），但在**中文区域的 MSVC** 下遇到一个隐蔽的正确性问题：

Ninja 依赖 `build.ninja` 里的 `msvc_deps_prefix` 来识别 `cl.exe /showIncludes` 的输出行，
据此建立头文件依赖。CMake 探测到中文前缀后，把它写进 `rules.ninja`：

```
msvc_deps_prefix = 娉ㄦ剰: 鍖呭惈鏂囦欢:      # 乱码
```

这是「`注意: 包含文件:` 的 UTF-8 字节被当成 GBK 再转一次」的典型乱码。编译器实际输出的是
GBK 字节，两边对不上，**Ninja 把全部 include 行丢弃**。

**后果非常隐蔽**：改头文件不触发任何 `.cpp` 重编，不同编译单元对同一个类的内存布局理解
不一致。本项目中它依次表现为：

| 症状 | 误判方向 |
| --- | --- |
| 程序启动即崩，`0xC0000374` 堆损坏，无任何输出 | 以为新代码有内存 bug |
| `0xC0000005` 访问违例 | 以为对象生命周期有问题 |
| `LNK2019` 找不到刚加的函数（明明有定义） | 以为宏/命名空间写错 |
| `LNK2019` 找不到 `setEmptyHint` | 反复检查声明与定义 |

**诊断方法**（不要猜）：

1. `Select-String -Path build\build.ninja -Pattern msvc_deps_prefix` 看前缀是什么
2. 对比 `.obj` 与 `.h` 的时间戳 —— 头文件更新但 obj 没变，就是依赖追踪失效
3. 用 `cl /showIncludes` 手工编译一个小文件，确认编译器输出的实际编码

**修法**：改用 `-G "Visual Studio 17 2022"`。MSBuild 由编译器自身解析 `/showIncludes`，
不经过 Ninja 的前缀字符串匹配，不受区域设置影响。代价是构建略慢、产物路径变成多配置形式
（本项目用 `CMAKE_RUNTIME_OUTPUT_DIRECTORY` 固定在 `build/bin/` 规避）。

> **教训**：这类问题不该靠"每次改头文件就 clean build"绕过。
> 增量构建不可靠本身就是缺陷 —— 它会持续制造假的 bug 信号，浪费的时间远超修它的成本。

### 2.9 部署：为什么构建产物必须自带 Qt 运行时

这不是"锦上添花的打包步骤"，而是**让程序能跑起来的必要条件**。

现象：在开发机上直接双击 `build\fmd_client.exe`，弹窗报
「无法定位程序输入点 `?viewportSizeHint@QTableView@@MEBA?AVQSize@@XZ`」。

排查过程（不靠猜，按顺序验证）：

1. `dumpbin /DEPENDENTS fmd_client.exe` 拿到 exe 依赖的四个 Qt DLL
2. 按 Windows 的 DLL 搜索顺序（exe 目录 → System32 → PATH 逐条）逐个探测，
   打印每个 DLL **实际会被加载的完整路径**
3. 四个 DLL 全部指向 `D:\Qt\5.15.2\mingw81_64\bin\` —— MinGW 构建的 Qt，
   与 MSVC 编译的 exe **ABI 不兼容**，符号自然对不上

根因：该目录在本机 PATH 上，而 `build\` 目录里没有 Qt DLL。

修法：CMake 加 POST_BUILD 调 windeployqt，把 Qt DLL 与插件（platforms / imageformats 等）
拷到可执行文件旁边。此后无论 PATH 上有多少套别的 Qt 都不受影响。

> **教训**：这类问题在开发时极易被掩盖 —— 如果测试脚本每次都先
> `PATH=D:\Qt\...\msvc2019_64\bin;$PATH` 再运行，就等于每次都在替程序挡住这个坑。
> **测试要尽量贴近用户的实际运行方式。**

## 3. 线程模型

```
主线程 (Qt 事件循环)
  ├─ 所有 UI 绘制与交互
  ├─ QNetworkAccessManager 异步回调（不阻塞）
  └─ 接收来自工作线程的信号（自动 QueuedConnection）

QThreadPool (maxThreadCount = CPU 核数 - 1)
  ├─ ImageLoaderTask   单图页：文件读取 + 解码
  └─ ImageLoaderTask   批量页：只读不解码（省掉无用的解码开销）

BatchController 调度器
  ├─ 预读上限 / 在途上限（两级背压）
  └─ 完成一个补一个
```

**关键点**：网络 I/O 本身是异步事件驱动的，不需要线程；真正需要线程池的是**文件解码**这类 CPU 密集操作。把两者混为一谈是常见的过度设计。

---

## 4. 踩过的坑（都是真实发生的）

| 坑 | 现象 | 原因与修法 |
|---|---|---|
| **QUrl::setPath 编码问号** | ``/history?limit=50`` 请求返回 404 | ``setPath()`` 会把 ``?`` 百分号编码成 ``%3F``，查询串变成路径的一部分。必须拆开用 ``setPath()`` + ``setQuery()`` |
| **信号槽参数不匹配** | 编译期 static_assert 失败 | 槽的参数不能多于信号。``QStatusBar::showMessage(msg, timeout)`` 有两个参数，不能直接当槽，要用 lambda 适配 |
| **函数参数里的 class 关键字** | 报 ``fmd::QFormLayout`` 未定义 | 在 ``namespace fmd`` 里写 ``class QFormLayout *`` 会**新声明**一个 fmd 命名空间内的类型，而不是引用全局的 |
| **改动公共头文件后的陈旧目标文件** | 程序启动即崩（堆损坏 0xC0000374） | 给 ``DetectionResult`` 加字段后，部分编译单元仍用旧结构体布局 → ABI 不一致。**改公共数据结构后必须干净重建**。踩了两次 |
| **ThreadingHTTPServer + 非线程安全模型** | 批量并发时随机失败 | 见 2.5 |
| **Qt5 高 DPI 不生效** | 界面模糊 | Qt5 必须手动设 ``AA_EnableHighDpiScaling``，且要在 QApplication 构造**之前**（Qt6 才自动） |
| **运行时加载到错误的 Qt**（最严重） | 双击 exe 弹「无法定位程序输入点 ?viewportSizeHint@QTableView@@...」 | exe 链接的是 D:\Qt 的 MSVC 版 Qt，但本机 PATH 上有 D:\Qt\5.15.2\mingw81_64\bin（**MinGW 版**，ABI 不兼容）。Windows 的 DLL 搜索顺序是「exe 目录 > 系统目录 > PATH」，而 build 目录里没有 Qt DLL，于是沿 PATH 抓到了 MinGW 那套。**修法：构建后用 windeployqt 把 Qt 运行时拷到 exe 旁边**。见 2.9 |
| **用 CopyFromScreen 截图会误判布局** | 截图里右侧面板"不见了" | 做截图的 PowerShell 进程是 DPI-unaware 的，在 200% 缩放屏上拿到的是被虚拟化缩放的桌面。**修法：用 QWidget::grab() 让 Qt 自己渲染**（--screenshot 模式），或先看控件几何数据（--dump-layout）再下结论 |
| **普通 QWidget 设了 QSS 背景却不显示** | 统计卡片看着是"没有卡片" | QWidget 子类默认不绘制样式表的 background/border，必须 `setAttribute(Qt::WA_StyledBackground, true)` |
| **改头文件不触发重编**（最耗时） | 启动崩溃 / LNK2019，反复出现 | Ninja 在中文区域 MSVC 下 `msvc_deps_prefix` 编码错乱，依赖追踪整体失效。见 2.9 |

---

## 5. 目录结构

```
client/
├── CMakeLists.txt          # CMake 工程（对比 qmake 的取舍见下）
├── build.bat               # 一键构建（vcvars + cmake + ninja）
├── src/
│   ├── main.cpp            # 入口 + 自检/冒烟/基准测试模式
│   ├── MainWindow.{h,cpp}  # 导航 + 页面栈 + 后端生命周期
│   ├── core/               # 与界面无关的基础设施
│   │   ├── Protocol.{h,cpp}       # 数据契约，JSON 解析集中在此
│   │   ├── BackendClient.{h,cpp}  # 网络层（全异步）
│   │   ├── BackendProcess.{h,cpp} # QProcess 守护 + 崩溃自动重启
│   │   └── SseParser.{h,cpp}      # SSE 增量解析（可独立单测）
│   ├── models/
│   │   ├── HistoryModel.{h,cpp}   # QAbstractTableModel
│   │   └── HistoryProxy.{h,cpp}   # QSortFilterProxyModel
│   ├── workers/
│   │   ├── ImageLoaderTask.{h,cpp}  # QRunnable
│   │   └── BatchController.{h,cpp}  # 任务调度 + 背压
│   └── views/              # 页面与自定义图元
├── tests/                  # Qt Test 单元测试
└── resources/

server/
├── app.py                  # HTTP 门面（标准库，零依赖）
├── detector.py             # 推理内核
├── storage.py              # SQLite 历史库
└── llm.py                  # 大模型分析（含无密钥的模拟模式）
```

### 为什么用 CMake 而不是 qmake？

- 现代 C++ 生态默认用 CMake，第三方库（OpenCV、gRPC 等）的官方示例都是 CMake
- IDE 无关：Qt Creator / CLion / VS / VS Code 都能直接用
- ``find_package`` + target 化依赖，比 ``.pro`` 的手写路径更可维护
- **代价**：Qt5 时代 CMake 的 Qt 集成（``qt5_add_resources`` / ``qt5_add_translation``）不如 qmake 顺滑，且要显式处理 ``CMAKE_PREFIX_PATH``

---

## 6. 可测性设计

所有功能都有**无界面**的验证入口，可以在 CI 或远程无人值守跑：

```
fmd_client.exe --selftest [图片]        端到端：拉服务 → 健康检查 → 列模型 → 推理
fmd_client.exe --smoke-ui  [图片]       界面链路：主窗口 → 线程池解码 → 推理 → 回填
fmd_client.exe --smoke-batch <目录> <N> 批量调度：队列 / 背压 / 进度
fmd_client.exe --smoke-history          历史三级链路：列表 → 详情 → 原图
fmd_client.exe --smoke-settings <端口>  配置链路：QSettings → 进程 → 客户端
fmd_client.exe --smoke-llm              流式分析：SSE 增量解析
fmd_client.exe --benchmark <图片> <N>   性能基准
```

加上 ``ctest`` 里的 SseParser 单元测试（9 个用例，覆盖半帧、CRLF、坏帧、逐字节投喂等边界）。

> **半帧**是最值得单测的地方：TCP 是字节流，事件边界和 ``read()`` 的返回边界没有任何关系，靠手工点击几乎不可能复现。
