# FaceMaskDetection 任务规划 —— Qt5 上位机客户端

## 完成状态（A~G 已全部落地并验证）

| 阶段 | 状态 | 验证方式 |
| --- | --- | --- |
| A 打通管道 | 完成 | selftest 退出码 0 |
| B 单图检测 | 完成 | smoke-ui 退出码 0 |
| C 批量检测 | 完成 | smoke-batch 6/6 成功 |
| D 历史记录 | 完成 | smoke-history 退出码 0 |
| E 模型与设置 | 完成 | smoke-settings 退出码 0 |
| F LLM 流式 | 完成 | smoke-llm 收到 21 个内容块 |
| G 打磨交付 | 完成 | QSS / Qt Test 11 例 / i18n 191 条 / windeployqt / 两份文档 |

详见 docs/ARCHITECTURE.md 与 docs/BENCHMARK.md。

## 现状盘点

| 资产 | 状态 |
|---|---|
| 训练好的模型 | ✅ ``train3_20250701-105710_yolov12n_best.pt``，3 类，GPU 81ms，实测可用 |
| Python 推理内核 | ✅ ``services.py:290-616`` 约 320 行，纯 ultralytics + cv2，**逻辑不用改** |
| 构建环境 | ✅ Qt 5.15.2 msvc2019_64 + VS2022 + CMake + Ninja，**已编译运行通过** |
| Python 运行环境 | ✅ conda ``med-yolo``（3.12.11 / torch 2.7.1+cu126 / CUDA 可用） |
| C++ 客户端 | 🚧 骨架已通，业务待写 ← **接下来的全部工作** |

**结论：只差写 Qt 前端。** 唯一的前置是给 Python 开一道 HTTP 门。

---

## 阶段 A — 打通管道（先证明 C++ 能和 Python 说上话）

| # | 任务 | 产出 |
|---|---|---|
| A1 | ``server/app.py``：~150 行 FastAPI 门面，暴露 ``GET /health``、``GET /models``、``POST /detect`` | **唯一的 Python 工作** |
| A2 | ``BackendProcess``：QProcess 拉起/关闭/守护 Python 服务，崩溃自动重启 | 简历点：进程管理 |
| A3 | ``BackendClient``：QNetworkAccessManager 异步请求 + 超时/错误分类 | 简历点：网络编程 |
| A4 | 验证：按钮 → 显示后端健康状态与模型列表 | — |

**验收**：点按钮能拿到 Python 返回的模型列表。
**预估**：1~2 天

> A1 的做法：把 ``services.py:290-616`` **原样复制**成 ``server/detector.py``，改 3 行路径、删 2 行 Django 缓存，外面套个 FastAPI。

---

## 阶段 B — 单图检测（核心闭环）

| # | 任务 | 产出 |
|---|---|---|
| B1 | ``MainWindow``：导航侧栏 + QStackedWidget 页面切换 | — |
| B2 | ``DetectView`` 布局 + 拖拽上传（``dragEnterEvent`` / ``dropEvent``） | — |
| B3 | 参数面板：模型下拉 / conf / iou / imgsz | — |
| B4 | ``InferTask``（QRunnable）+ QThreadPool 异步推理 + 跨线程信号槽回传 | **简历点：多线程** |
| B5 | ``ImageCanvas``（QGraphicsView）：显示图 + 自绘检测框 + 缩放平移 | **简历点：图形视图** |
| B6 | 结果面板：三类计数 + 耗时 | — |

**验收**：拖图进去 → 界面全程不卡 → 出标注框与统计。
**预估**：3~5 天

---

## 阶段 C — 批量检测

| # | 任务 | 产出 |
|---|---|---|
| C1 | 多选文件 + 任务入队 | — |
| C2 | ``BatchController``：任务队列、**背压**、进度聚合、取消 | **简历点：任务调度** |
| C3 | 进度条 + 结果列表（成功/失败） | — |

**验收**：20 张批量处理全程 UI 可交互，可中途取消。
**预估**：2~3 天

---

## 阶段 D — 历史记录（Model/View 架构）

| # | 任务 | 产出 |
|---|---|---|
| D1 | 后端 ``GET /history`` + SQLite 落库 | — |
| D2 | ``HistoryModel``（QAbstractTableModel 自定义模型） | **简历点：Model/View** |
| D3 | ``HistoryProxy``（QSortFilterProxyModel 搜索/筛选/排序） | **简历点：代理模型** |
| D4 | 详情面板 + 删除 | — |

**验收**：1000+ 条记录滚动流畅。
**预估**：2~3 天

---

## 阶段 E — 模型管理 / 设置

| # | 任务 | 产出 |
|---|---|---|
| E1 | 模型列表页 + 元数据展示 | — |
| E2 | QSettings 持久化（服务地址、默认参数、API key） | — |
| E3 | 设置页 | — |

**预估**：1~2 天

---

## 阶段 F — LLM 流式分析 + PDF

| # | 任务 | 产出 |
|---|---|---|
| F1 | 后端 ``POST /llm/analyze`` 流式接口 | — |
| F2 | ``SseParser``：``readyRead`` 增量解析，**处理半帧/粘包** | **简历点：协议解析** |
| F3 | 流式渲染（打字机效果） | — |
| F4 | PDF 导出 | — |

**验收**：分析结果逐字出现，不是等 10 秒一次性弹出。
**预估**：2~3 天

---

## 阶段 G — 打磨与简历产出

| # | 任务 | 产出 |
|---|---|---|
| G1 | QSS 主题美化 | — |
| G2 | Qt Linguist 中英双语 | 简历点：国际化 |
| G3 | Qt Test 单元测试 | 简历点：测试 |
| G4 | ``windeployqt`` 打包 | 简历点：部署 |
| G5 | **BENCHMARK**：base64 vs QSharedMemory 大图传输实测 | **★ 面试王牌** |
| G6 | ``docs/ARCHITECTURE.md`` | 面试时给面试官看 |

**预估**：3~5 天

---

## 总预估：约 15~25 个工作日

**简历最小可用版本 = A + B**（约 5~7 天）。做完就能写进简历；C 之后是加深。

---

## 面试题库映射

| 面试官会问 | 你项目里的答案 |
|---|---|
| Qt 事件循环是什么？ | 主线程 ``exec()`` 驱动事件队列；推理放 worker 就是为了不阻塞它 |
| 信号槽底层原理？连接类型区别？ | moc 元对象系统；跨线程必须 ``QueuedConnection``（接收者线程亲和性） |
| 多线程有几种方式？怎么选？ | QThread 子类 / ``moveToThread`` / QThreadPool+QRunnable；选线程池因为任务短时同质 |
| 网络编程怎么处理粘包/拆包？ | SSE 流式解析要处理不完整帧 —— **阶段 F 真实踩坑** |
| 界面卡顿怎么排查？ | 事件循环阻塞；QElapsedTimer 定位 |
| Qt 内存管理？ | 对象树/父子对象；QSharedMemory 生命周期与 detach |
| 大文件怎么传？ | **base64 vs 共享内存实测对比** ← 阶段 G5 |
| 为什么用 CMake 不用 qmake？ | 现代 C++ 生态、依赖管理、IDE 无关 |
| 为什么 Qt5 不用 Qt6？ | 工业存量 + LTS 成熟度；主动讲开源版无新补丁的代价 |
| 跨语言怎么协作？ | 为什么双进程而非 pybind11（崩溃隔离/GIL/部署体积/热更新）—— **有数字** |

**不要写**：Qt Quick/QML、串口、Modbus、OPC UA —— 没做就别写。

---

## Qt5 陷阱备忘

| 陷阱 | 说明 |
|---|---|
| PATH 上的 qmake 是 Anaconda 的 | 必须 ``CMAKE_PREFIX_PATH=D:/Qt/5.15.2/msvc2019_64`` 显式指定 |
| 高 DPI 要手动开 | ``AA_EnableHighDpiScaling`` 须在 QApplication 构造**之前**；Qt6 才自动 |
| ``QNetworkReply::error()`` | 5.15 已废弃 → ``errorOccurred()`` |
| ``QRegExp`` | 已废弃 → ``QRegularExpression`` |
| ``QString::SkipEmptyParts`` | 已废弃 → ``Qt::SkipEmptyParts`` |
| CMake 函数名 | Qt5：``qt5_add_resources`` / ``qt5_add_translation`` |
| MSVC 中文乱码 | 源码必须 ``/utf-8``（骨架已加） |

---

## 待办（与前端无关，想起来再说）

- [ ] **吊销 SiliconFlow API key**：``api_views.py:24`` 硬编码的 ``sk-pzpw...`` 已随代码进 git 历史（原仓库 5 人可见）
- [ ] 仓库瘦身：``db.sqlite3``、``logs/*.log``、大文件（两个字体 25.7MB、4 个 ``.pt``）是否走 LFS
- [ ] 删 ``django_frontend/``（等 Qt 客户端跑通后再删）
- [ ] 删爬虫数据里的 ``.keep`` 干扰项（可选）
