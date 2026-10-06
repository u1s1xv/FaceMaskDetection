<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="en_US">
<context>
    <name>DetectionItem</name>
    <message>
        <source>%1
置信度 %2
坐标 (%3, %4) - (%5, %6)</source>
        <translation>%1
Confidence %2
Box (%3, %4) - (%5, %6)</translation>
    </message>
</context>
<context>
    <name>LiveView</name>
    <message>
        <source>正确佩戴</source>
        <translation type="unfinished">Wearing correctly</translation>
    </message>
    <message>
        <source>未佩戴</source>
        <translation type="unfinished">Not wearing</translation>
    </message>
    <message>
        <source>佩戴不规范</source>
        <translation type="unfinished">Worn incorrectly</translation>
    </message>
</context>
<context>
    <name>Protocol</name>
    <message>
        <source>服务端返回失败但未给出原因</source>
        <translation>Server reported failure but gave no reason</translation>
    </message>
</context>
<context>
    <name>fmd::BackendClient</name>
    <message>
        <source>服务端结束了推流</source>
        <translation>The server closed the stream</translation>
    </message>
    <message>
        <source>已停止</source>
        <translation>Stopped</translation>
    </message>
    <message>
        <source>多次重连仍未收到画面</source>
        <translation>Still no frames after several reconnects</translation>
    </message>
</context>
<context>
    <name>fmd::BackendProcess</name>
    <message>
        <source>找不到服务端脚本 server/app.py，请检查路径或设置 FMD_SERVER_SCRIPT</source>
        <translation>Cannot find server/app.py. Check the path or set FMD_SERVER_SCRIPT</translation>
    </message>
    <message>
        <source>[启动] %1 %2</source>
        <translation>[start] %1 %2</translation>
    </message>
    <message>
        <source>服务进程启动失败: %1</source>
        <translation>Failed to start backend process: %1</translation>
    </message>
    <message>
        <source>无法启动服务进程: %1</source>
        <translation>Cannot launch backend process: %1</translation>
    </message>
    <message>
        <source>进程崩溃</source>
        <translation>process crashed</translation>
    </message>
    <message>
        <source>进程退出，退出码 %1</source>
        <translation>process exited with code %1</translation>
    </message>
    <message>
        <source>[守护] %1，%2 ms 后自动重启（第 %3 次）</source>
        <translation>[guard] %1; restarting in %2 ms (attempt %3)</translation>
    </message>
    <message>
        <source>[守护] 连续重启超过 5 次，停止自动重启</source>
        <translation>[guard] more than 5 consecutive restarts, giving up auto-restart</translation>
    </message>
    <message>
        <source>[守护] 服务进程已纳入作业对象，客户端退出时会一并终止</source>
        <translation>[guardian] Service process added to a job object; it will be terminated with the client</translation>
    </message>
    <message>
        <source>[守护] 警告：作业对象保护未生效，异常退出可能留下孤儿进程</source>
        <translation>[guardian] Warning: job object protection is inactive; an abnormal exit may leave an orphan process</translation>
    </message>
</context>
<context>
    <name>fmd::BackendStatusView</name>
    <message>
        <source>推理服务状态</source>
        <translation>Inference Service Status</translation>
    </message>
    <message>
        <source>连接状态</source>
        <translation>Connection</translation>
    </message>
    <message>
        <source>计算设备</source>
        <translation>Device</translation>
    </message>
    <message>
        <source>模型目录</source>
        <translation>Model directory</translation>
    </message>
    <message>
        <source>可用模型</source>
        <translation>Available models</translation>
    </message>
    <message>
        <source>刷新状态</source>
        <translation>Refresh Status</translation>
    </message>
    <message>
        <source>重启服务</source>
        <translation>Restart Service</translation>
    </message>
    <message>
        <source>服务端日志</source>
        <translation>Service Log</translation>
    </message>
    <message>
        <source>正在连接…</source>
        <translation>Connecting…</translation>
    </message>
    <message>
        <source>服务未就绪</source>
        <translation>Service not ready</translation>
    </message>
    <message>
        <source>已连接</source>
        <translation>Connected</translation>
    </message>
    <message>
        <source>（模型目录中没有 .pt 文件）</source>
        <translation>(no .pt files in the model directory)</translation>
    </message>
    <message>
        <source>连接失败：%1</source>
        <translation>Connection failed: %1</translation>
    </message>
</context>
<context>
    <name>fmd::BatchController</name>
    <message>
        <source>批量开始：%1 个文件，最大并发 %2</source>
        <translation>Batch started: %1 file(s), max concurrency %2</translation>
    </message>
    <message>
        <source>已请求取消：不再派发新任务，在途的 %1 个会跑完</source>
        <translation>Cancellation requested: no new jobs dispatched; %1 in-flight job(s) will finish</translation>
    </message>
    <message>
        <source>批量结束：成功 %1，失败 %2%3</source>
        <translation>Batch finished: %1 succeeded, %2 failed%3</translation>
    </message>
    <message>
        <source>（已取消）</source>
        <translation> (cancelled)</translation>
    </message>
    <message>
        <source>读取失败 %1：%2</source>
        <translation>Read failed %1: %2</translation>
    </message>
    <message>
        <source>请求失败 %1：%2</source>
        <translation>Request failed %1: %2</translation>
    </message>
</context>
<context>
    <name>fmd::BatchView</name>
    <message>
        <source>批量参数</source>
        <translation>Batch Parameters</translation>
    </message>
    <message>
        <source>模型</source>
        <translation>Model</translation>
    </message>
    <message>
        <source>置信度</source>
        <translation>Confidence</translation>
    </message>
    <message>
        <source>尺寸</source>
        <translation>Size</translation>
    </message>
    <message>
        <source>并发</source>
        <translation>Concurrency</translation>
    </message>
    <message>
        <source>添加图片…</source>
        <translation>Add Images…</translation>
    </message>
    <message>
        <source>添加文件夹…</source>
        <translation>Add Folder…</translation>
    </message>
    <message>
        <source>开始批量检测</source>
        <translation>Start Batch</translation>
    </message>
    <message>
        <source>取消</source>
        <translation>Cancel</translation>
    </message>
    <message>
        <source>清空列表</source>
        <translation>Clear List</translation>
    </message>
    <message>
        <source>尚未添加文件</source>
        <translation>No files added yet</translation>
    </message>
    <message>
        <source>文件</source>
        <translation>File</translation>
    </message>
    <message>
        <source>状态</source>
        <translation>Status</translation>
    </message>
    <message>
        <source>目标数</source>
        <translation>Objects</translation>
    </message>
    <message>
        <source>正确</source>
        <translation>Correct</translation>
    </message>
    <message>
        <source>未佩戴</source>
        <translation>Not wearing</translation>
    </message>
    <message>
        <source>不规范</source>
        <translation>Incorrect</translation>
    </message>
    <message>
        <source>耗时</source>
        <translation>Time</translation>
    </message>
    <message>
        <source>（自动选择 best）</source>
        <translation>(auto: pick best)</translation>
    </message>
    <message>
        <source>选择图片（可多选）</source>
        <translation>Select images (multiple allowed)</translation>
    </message>
    <message>
        <source>图片 (*.jpg *.jpeg *.png *.bmp *.webp)</source>
        <translation>Images (*.jpg *.jpeg *.png *.bmp *.webp)</translation>
    </message>
    <message>
        <source>选择包含图片的文件夹</source>
        <translation>Select a Folder Containing Images</translation>
    </message>
    <message>
        <source>待处理</source>
        <translation>Pending</translation>
    </message>
    <message>
        <source>已添加 %1 个文件（双击某行可在单图页查看）</source>
        <translation>%1 file(s) added (double-click a row to view it on the single-image page)</translation>
    </message>
    <message>
        <source>请先添加图片</source>
        <translation>Please add images first</translation>
    </message>
    <message>
        <source>排队中</source>
        <translation>Queued</translation>
    </message>
    <message>
        <source>完成</source>
        <translation>Done</translation>
    </message>
    <message>
        <source>失败</source>
        <translation>Failed</translation>
    </message>
    <message>
        <source>%1
错误：%2</source>
        <translation>%1
Error: %2</translation>
    </message>
    <message>
        <source>进度 %1/%2 — 成功 %3，失败 %4</source>
        <translation>Progress %1/%2 — %3 succeeded, %4 failed</translation>
    </message>
    <message>
        <source>%1 — 成功 %2，失败 %3</source>
        <translation>%1 — %2 succeeded, %3 failed</translation>
    </message>
    <message>
        <source>已取消</source>
        <translation>Cancelled</translation>
    </message>
    <message>
        <source>批量完成</source>
        <translation>Batch complete</translation>
    </message>
    <message>
        <source>选中左侧任意一行，查看该图片的检测结果</source>
        <translation>Select any row on the left to see that image&apos;s detection result</translation>
    </message>
    <message>
        <source>%1

该图片还没有检测结果（未处理或已失败）</source>
        <translation>%1

No detection result for this image yet (not processed, or failed)</translation>
    </message>
    <message>
        <source>#%1  %2  置信度 %3  框(%4,%5)-(%6,%7)</source>
        <translation>#%1  %2  conf %3  box(%4,%5)-(%6,%7)</translation>
    </message>
    <message>
        <source>（未检测到目标）</source>
        <translation type="unfinished">(no objects detected)</translation>
    </message>
    <message>
        <source>%1 ｜ 共 %2 个目标 ｜ 记录 #%3</source>
        <translation>%1 | %2 targets | record #%3</translation>
    </message>
    <message>
        <source>无法加载预览：%1</source>
        <translation>Cannot load preview: %1</translation>
    </message>
    <message>
        <source>批量检测</source>
        <translation type="unfinished">Batch</translation>
    </message>
    <message>
        <source>一次添加多张图片或整个文件夹，客户端按设定并发数排队调度，服务端串行推理。
双击结果表中的任意一行可跳转到单图页查看原图。</source>
        <translation>Add several images or a whole folder at once. The client queues them by the configured concurrency; the server runs inference serially.
Double-click any row to open the original image on the single-image page.</translation>
    </message>
</context>
<context>
    <name>fmd::DetectView</name>
    <message>
        <source>图像</source>
        <translation>Image</translation>
    </message>
    <message>
        <source>把图片拖到这里，或点击「打开图片」</source>
        <translation type="vanished">Drop an image here, or click &quot;Open Image&quot;</translation>
    </message>
    <message>
        <source>推理参数</source>
        <translation>Inference Parameters</translation>
    </message>
    <message>
        <source>模型</source>
        <translation>Model</translation>
    </message>
    <message>
        <source>置信度阈值</source>
        <translation>Confidence threshold</translation>
    </message>
    <message>
        <source>IOU 阈值</source>
        <translation>IoU threshold</translation>
    </message>
    <message>
        <source>推理尺寸</source>
        <translation>Inference size</translation>
    </message>
    <message>
        <source>使用服务端渲染图</source>
        <translation>Use server-rendered image</translation>
    </message>
    <message>
        <source>打开图片</source>
        <translation>Open Image</translation>
    </message>
    <message>
        <source>开始检测</source>
        <translation>Detect</translation>
    </message>
    <message>
        <source>检测结果</source>
        <translation>Detection Result</translation>
    </message>
    <message>
        <source>正确佩戴</source>
        <translation>Wearing correctly</translation>
    </message>
    <message>
        <source>未佩戴</source>
        <translation>Not wearing</translation>
    </message>
    <message>
        <source>佩戴不规范</source>
        <translation>Worn incorrectly</translation>
    </message>
    <message>
        <source>目标总数</source>
        <translation>Total objects</translation>
    </message>
    <message>
        <source>处理耗时</source>
        <translation>Processing time</translation>
    </message>
    <message>
        <source>AI 智能分析…</source>
        <translation>AI Analysis…</translation>
    </message>
    <message>
        <source>对当前这条检测记录调用大模型做合规性分析</source>
        <translation>Run LLM compliance analysis on this detection record</translation>
    </message>
    <message>
        <source>（自动选择 best）</source>
        <translation>(auto: pick best)</translation>
    </message>
    <message>
        <source>选择图片</source>
        <translation>Select Image</translation>
    </message>
    <message>
        <source>图片 (*.jpg *.jpeg *.png *.bmp *.webp);;所有文件 (*.*)</source>
        <translation>Images (*.jpg *.jpeg *.png *.bmp *.webp);;All files (*.*)</translation>
    </message>
    <message>
        <source>正在推理中，请稍候…</source>
        <translation>Inference in progress, please wait…</translation>
    </message>
    <message>
        <source>正在加载 %1 …</source>
        <translation>Loading %1 …</translation>
    </message>
    <message>
        <source>%1
%2 × %3 像素，%4 KB</source>
        <translation>%1
%2 × %3 px, %4 KB</translation>
    </message>
    <message>
        <source>解码耗时 %1 ms — 点击「开始检测」</source>
        <translation>Decoded in %1 ms — click &quot;Detect&quot;</translation>
    </message>
    <message>
        <source>已加载 %1</source>
        <translation>Loaded %1</translation>
    </message>
    <message>
        <source>加载失败：%1</source>
        <translation>Load failed: %1</translation>
    </message>
    <message>
        <source>加载 %1 失败：%2</source>
        <translation>Failed to load %1: %2</translation>
    </message>
    <message>
        <source>请先选择一张图片</source>
        <translation>Please select an image first</translation>
    </message>
    <message>
        <source>正在推理…（首次调用要加载模型，可能数秒）</source>
        <translation>Running inference… (first call loads the model and may take seconds)</translation>
    </message>
    <message>
        <source>推理失败：%1</source>
        <translation>Inference failed: %1</translation>
    </message>
    <message>
        <source>服务端渲染图（%1 KB）</source>
        <translation>Server-rendered image (%1 KB)</translation>
    </message>
    <message>
        <source>客户端自绘 %1 个检测框 — 滚轮缩放，悬停查看置信度</source>
        <translation>%1 box(es) drawn client-side — scroll to zoom, hover for confidence</translation>
    </message>
    <message>
        <source>检测完成：%1 个目标，耗时 %2 s</source>
        <translation>Detection complete: %1 object(s) in %2 s</translation>
    </message>
    <message>
        <source>这条结果没有落库记录，无法做历史关联分析</source>
        <translation>This result was not saved to history, so record-linked analysis is unavailable</translation>
    </message>
    <message>
        <source>#%1  %2  置信度 %3</source>
        <translation>#%1  %2  confidence %3</translation>
    </message>
    <message>
        <source>（未检测到目标）</source>
        <translation>(no objects detected)</translation>
    </message>
    <message>
        <source>请求失败：%1</source>
        <translation>Request failed: %1</translation>
    </message>
    <message>
        <source>推理请求失败：%1</source>
        <translation>Inference request failed: %1</translation>
    </message>
    <message>
        <source>单图检测</source>
        <translation>Single Image</translation>
    </message>
    <message>
        <source>拖入或打开一张图片，调用本地推理服务检测口罩佩戴情况。每次检测都会自动存入历史记录。</source>
        <translation>Drop in or open an image; the local inference service detects mask usage. Every detection is stored in history automatically.</translation>
    </message>
    <message>
        <source>把图片拖到这里，或点击右侧「打开图片」</source>
        <translation>Drop an image here, or click &quot;Open Image&quot; on the right</translation>
    </message>
    <message>
        <source>支持 JPG / PNG / BMP / WebP</source>
        <translation>Supports JPG / PNG / BMP / WebP</translation>
    </message>
</context>
<context>
    <name>fmd::HistoryModel</name>
    <message>
        <source>记录 #%1
文件：%2
模型：%3
图像：%4×%5
耗时：%6 ms
排队：%7 ms</source>
        <translation>Record #%1
File: %2
Model: %3
Image: %4×%5
Inference: %6 ms
Queued: %7 ms</translation>
    </message>
    <message>
        <source>文件名</source>
        <translation>File name</translation>
    </message>
    <message>
        <source>尺寸</source>
        <translation>Size</translation>
    </message>
    <message>
        <source>目标数</source>
        <translation>Objects</translation>
    </message>
    <message>
        <source>正确</source>
        <translation>Correct</translation>
    </message>
    <message>
        <source>未佩戴</source>
        <translation>Not wearing</translation>
    </message>
    <message>
        <source>不规范</source>
        <translation>Incorrect</translation>
    </message>
    <message>
        <source>推理 ms</source>
        <translation>Infer ms</translation>
    </message>
    <message>
        <source>排队 ms</source>
        <translation>Queue ms</translation>
    </message>
    <message>
        <source>时间</source>
        <translation>Time</translation>
    </message>
</context>
<context>
    <name>fmd::HistoryView</name>
    <message>
        <source>刷新</source>
        <translation>Refresh</translation>
    </message>
    <message>
        <source>搜索文件名 / 时间 / ID…</source>
        <translation>Search file name / time / ID…</translation>
    </message>
    <message>
        <source>只看违规</source>
        <translation>Violations only</translation>
    </message>
    <message>
        <source>筛选出存在「未佩戴口罩」或「佩戴不规范」的记录</source>
        <translation>Show only records containing &quot;no mask&quot; or &quot;worn incorrectly&quot;</translation>
    </message>
    <message>
        <source>删除选中</source>
        <translation>Delete Selected</translation>
    </message>
    <message>
        <source>选中一行查看详情</source>
        <translation>Select a row to view details</translation>
    </message>
    <message>
        <source>显示 %1 / 共 %2 条</source>
        <translation>Showing %1 of %2</translation>
    </message>
    <message>
        <source>已加载 %1 条历史记录（共 %2 条）</source>
        <translation>Loaded %1 history record(s) (of %2)</translation>
    </message>
    <message>
        <source>确认删除</source>
        <translation>Confirm Delete</translation>
    </message>
    <message>
        <source>确定要删除记录 #%1 吗？此操作不可撤销。</source>
        <translation>Delete record #%1? This cannot be undone.</translation>
    </message>
    <message>
        <source>记录 #%1 已删除</source>
        <translation>Record #%1 deleted</translation>
    </message>
    <message>
        <source>已删除记录 #%1</source>
        <translation>Deleted record #%1</translation>
    </message>
    <message>
        <source>%1 失败：%2</source>
        <translation>%1 failed: %2</translation>
    </message>
    <message>
        <source>正在加载记录 #%1 …</source>
        <translation>Loading record #%1 …</translation>
    </message>
    <message>
        <source>历史记录</source>
        <translation type="unfinished">History</translation>
    </message>
    <message>
        <source>每次检测都会自动入库。支持按文件名、时间、ID 搜索，也可以只看存在违规的记录。
选中一行可在下方查看该次检测的标注结果。</source>
        <translation>Every detection is stored automatically. Search by file name, time or ID, or show only violations.
Select a row to see that detection&apos;s annotated result below.</translation>
    </message>
</context>
<context>
    <name>fmd::ImageLoaderTask</name>
    <message>
        <source>无法打开文件：%1</source>
        <translation>Cannot open file: %1</translation>
    </message>
    <message>
        <source>文件为空</source>
        <translation>File is empty</translation>
    </message>
    <message>
        <source>图片解码失败：%1</source>
        <translation>Image decode failed: %1</translation>
    </message>
</context>
<context>
    <name>fmd::LiveView</name>
    <message>
        <source>实时监控</source>
        <translation>Live Monitor</translation>
    </message>
    <message>
        <source>接入 USB 摄像头、RTSP 网络流或视频文件，服务端边采集边推理，画面以 MJPEG 推送到这里。
检测框由服务端绘制在画面上 —— 这样框和画面永远同步，不会出现&quot;框在画面外飘&quot;。</source>
        <translation>Connect a USB camera, RTSP stream or video file. The server captures and infers continuously and pushes frames here over MJPEG.
Boxes are drawn server-side, so they always stay in sync with the picture — no boxes drifting off the image.</translation>
    </message>
    <message>
        <source>摄像头</source>
        <translation>Camera</translation>
    </message>
    <message>
        <source>刷新</source>
        <translation type="unfinished">Refresh</translation>
    </message>
    <message>
        <source>或指定源</source>
        <translation>Or a source</translation>
    </message>
    <message>
        <source>视频文件路径 / rtsp://…</source>
        <translation>Video file path / rtsp://…</translation>
    </message>
    <message>
        <source>打开</source>
        <translation>Open</translation>
    </message>
    <message>
        <source>关闭</source>
        <translation>Close</translation>
    </message>
    <message>
        <source>尚未接入视频源</source>
        <translation>No video source connected</translation>
    </message>
    <message>
        <source>画面</source>
        <translation>Video</translation>
    </message>
    <message>
        <source>分辨率</source>
        <translation>Resolution</translation>
    </message>
    <message>
        <source>接收帧率</source>
        <translation>Receive rate</translation>
    </message>
    <message>
        <source>码率</source>
        <translation>Bitrate</translation>
    </message>
    <message>
        <source>累计帧数</source>
        <translation>Frames received</translation>
    </message>
    <message>
        <source>推理</source>
        <translation>Inference</translation>
    </message>
    <message>
        <source>推理耗时</source>
        <translation>Inference time</translation>
    </message>
    <message>
        <source>端到端延迟</source>
        <translation>End-to-end latency</translation>
    </message>
    <message>
        <source>单帧大小</source>
        <translation>Frame size</translation>
    </message>
    <message>
        <source>当前画面目标</source>
        <translation>Targets in view</translation>
    </message>
    <message>
        <source>正确佩戴</source>
        <translation type="unfinished">Wearing correctly</translation>
    </message>
    <message>
        <source>未佩戴</source>
        <translation type="unfinished">Not wearing</translation>
    </message>
    <message>
        <source>佩戴不规范</source>
        <translation type="unfinished">Worn incorrectly</translation>
    </message>
    <message>
        <source>没有可用的摄像头。可以改为在右侧填入视频文件路径或 RTSP 地址。</source>
        <translation>No camera available. Enter a video file path or RTSP URL in the field instead.</translation>
    </message>
    <message>
        <source>正在打开摄像头 %1 …</source>
        <translation>Opening camera %1 …</translation>
    </message>
    <message>
        <source>正在打开 %1 …</source>
        <translation>Opening %1 …</translation>
    </message>
    <message>
        <source>摄像头 %1（%2 %3x%4）</source>
        <translation>Camera %1 (%2 %3x%4)</translation>
    </message>
    <message>
        <source>（未检测到摄像头）</source>
        <translation>(no camera detected)</translation>
    </message>
    <message>
        <source>已接入 %1（%2，后端 %3）</source>
        <translation>Connected to %1 (%2, backend %3)</translation>
    </message>
    <message>
        <source>视频源 %1 已接入</source>
        <translation>Video source %1 connected</translation>
    </message>
    <message>
        <source>视频源已关闭</source>
        <translation>Video source closed</translation>
    </message>
    <message>
        <source>视频源 %1 已关闭</source>
        <translation>Video source %1 closed</translation>
    </message>
    <message>
        <source>正在接收 %1 的画面…</source>
        <translation>Receiving frames from %1 …</translation>
    </message>
    <message>
        <source>画面已停止：%1</source>
        <translation>Video stopped: %1</translation>
    </message>
    <message>
        <source>推流中断：%1</source>
        <translation>Stream interrupted: %1</translation>
    </message>
    <message>
        <source>操作失败：%1</source>
        <translation>Operation failed: %1</translation>
    </message>
    <message>
        <source>打开视频源失败</source>
        <translation>Failed to open the video source</translation>
    </message>
    <message>
        <source>%1 FPS</source>
        <translation>%1 FPS</translation>
    </message>
    <message>
        <source>%1 KB/s</source>
        <translation>%1 KB/s</translation>
    </message>
    <message>
        <source>%1 ms</source>
        <translation>%1 ms</translation>
    </message>
    <message>
        <source>%1 KB</source>
        <translation>%1 KB</translation>
    </message>
    <message>
        <source>%1  置信度 %2  框(%3,%4)-(%5,%6)</source>
        <translation>%1  conf %2  box(%3,%4)-(%5,%6)</translation>
    </message>
    <message>
        <source>（当前画面没有检测到目标）</source>
        <translation>(no target detected in the current view)</translation>
    </message>
    <message>
        <source>镜像画面</source>
        <translation>Mirror</translation>
    </message>
    <message>
        <source>桌面应用的惯例是镜像（像照镜子），视频会议的本地预览也是如此。
工业监控场景建议关掉 —— 画面左右与现场一致，指挥&quot;往左一点&quot;才不会说反。
镜像由服务端绘制，不会影响检测结果。</source>
        <translation>Desktop apps conventionally mirror the preview (like a mirror), as do video-call apps.
For industrial monitoring it is better to turn this off so that left and right match the site — otherwise &quot;move a bit to the left&quot; is reversed.
Mirroring is applied server-side and does not affect detection results.</translation>
    </message>
    <message>
        <source>画面已镜像</source>
        <translation>Picture mirrored</translation>
    </message>
    <message>
        <source>画面已取消镜像</source>
        <translation>Mirroring disabled</translation>
    </message>
</context>
<context>
    <name>fmd::LlmAnalysisDialog</name>
    <message>
        <source>AI 智能分析 — 记录 #%1</source>
        <translation>AI Analysis — Record #%1</translation>
    </message>
    <message>
        <source>分析模型</source>
        <translation>Analysis model</translation>
    </message>
    <message>
        <source>分析要求（可自定义提示词）</source>
        <translation>Analysis request (custom prompt allowed)</translation>
    </message>
    <message>
        <source>请分析本次口罩检测结果，评估合规性并给出改进建议。</source>
        <translation>Analyze this mask detection result, assess compliance and suggest improvements.</translation>
    </message>
    <message>
        <source>开始分析</source>
        <translation>Start Analysis</translation>
    </message>
    <message>
        <source>另存为文本…</source>
        <translation>Save as Text…</translation>
    </message>
    <message>
        <source>准备就绪</source>
        <translation>Ready</translation>
    </message>
    <message>
        <source>已配置 API Key，将调用真实大模型</source>
        <translation>API key configured; the real LLM will be called</translation>
    </message>
    <message>
        <source>正在流式接收…</source>
        <translation>Streaming…</translation>
    </message>
    <message>
        <source>流式接收中（模拟模式）— 模型 %1</source>
        <translation>Streaming (mock mode) — model %1</translation>
    </message>
    <message>
        <source>流式接收中 — 模型 %1</source>
        <translation>Streaming — model %1</translation>
    </message>
    <message>
        <source>分析完成</source>
        <translation>Analysis complete</translation>
    </message>
    <message>
        <source>分析失败：%1</source>
        <translation>Analysis failed: %1</translation>
    </message>
    <message>
        <source>保存分析结果</source>
        <translation>Save Analysis Result</translation>
    </message>
    <message>
        <source>文本文件 (*.txt)</source>
        <translation>Text files (*.txt)</translation>
    </message>
    <message>
        <source>保存失败：%1</source>
        <translation>Save failed: %1</translation>
    </message>
    <message>
        <source>已保存到 %1</source>
        <translation>Saved to %1</translation>
    </message>
</context>
<context>
    <name>fmd::MainWindow</name>
    <message>
        <source>[错误] %1 请求失败: %2</source>
        <translation>[error] %1 request failed: %2</translation>
    </message>
    <message>
        <source>[守护] 手动重启服务…</source>
        <translation>[guard] restarting service manually…</translation>
    </message>
    <message>
        <source>FaceMaskDetection — 智能口罩检测系统</source>
        <translation>FaceMaskDetection — Mask Detection System</translation>
    </message>
    <message>
        <source>检测</source>
        <translation>Detect</translation>
    </message>
    <message>
        <source>批量检测</source>
        <translation>Batch</translation>
    </message>
    <message>
        <source>历史记录</source>
        <translation>History</translation>
    </message>
    <message>
        <source>模型管理</source>
        <translation>Models</translation>
    </message>
    <message>
        <source>设置</source>
        <translation>Settings</translation>
    </message>
    <message>
        <source>后端：未连接</source>
        <translation>Backend: disconnected</translation>
    </message>
    <message>
        <source>就绪</source>
        <translation>Ready</translation>
    </message>
    <message>
        <source>推理服务已拉起（%1）</source>
        <translation>Inference service launched (%1)</translation>
    </message>
    <message>
        <source>后端：%1</source>
        <translation>Backend: %1</translation>
    </message>
    <message>
        <source>[守护] %1 (exit=%2)</source>
        <translation>[guard] %1 (exit=%2)</translation>
    </message>
    <message>
        <source>后端：启动失败</source>
        <translation>Backend: failed to start</translation>
    </message>
    <message>
        <source>[错误] %1</source>
        <translation>[error] %1</translation>
    </message>
    <message>
        <source>后端：未就绪</source>
        <translation>Backend: not ready</translation>
    </message>
    <message>
        <source>多次探测未响应，请查看日志</source>
        <translation>No response after repeated probes; check the log</translation>
    </message>
    <message>
        <source>后端：已连接 (%1)</source>
        <translation>Backend: connected (%1)</translation>
    </message>
    <message>
        <source>推理服务就绪：%1 / PyTorch %2</source>
        <translation>Inference service ready: %1 / PyTorch %2</translation>
    </message>
    <message>
        <source>重启失败，请手动重新打开程序</source>
        <translation>Restart failed; please reopen the application manually</translation>
    </message>
    <message>
        <source>实时监控</source>
        <translation>Live Monitor</translation>
    </message>
</context>
<context>
    <name>fmd::ModelsView</name>
    <message>
        <source>（自动选择 *_best.pt）</source>
        <translation>(auto: pick *_best.pt)</translation>
    </message>
    <message>
        <source>当前默认模型</source>
        <translation>Current Default Model</translation>
    </message>
    <message>
        <source>重新扫描</source>
        <translation>Rescan</translation>
    </message>
    <message>
        <source>设为默认</source>
        <translation>Set as Default</translation>
    </message>
    <message>
        <source>权重文件</source>
        <translation>Weight file</translation>
    </message>
    <message>
        <source>体积 (MB)</source>
        <translation>Size (MB)</translation>
    </message>
    <message>
        <source>修改时间</source>
        <translation>Modified</translation>
    </message>
    <message>
        <source>共 %1 个权重</source>
        <translation>%1 weight file(s)</translation>
    </message>
    <message>
        <source>默认模型已切换为 %1</source>
        <translation>Default model switched to %1</translation>
    </message>
    <message>
        <source>模型管理</source>
        <translation type="unfinished">Models</translation>
    </message>
    <message>
        <source>扫描 yoloserver/models/checkpoints/ 下的权重文件。把训练好的 .pt 放进去后点「重新扫描」即可出现。</source>
        <translation>Scans weight files under yoloserver/models/checkpoints/. Drop a trained .pt there and click Rescan to make it appear.</translation>
    </message>
</context>
<context>
    <name>fmd::SettingsView</name>
    <message>
        <source>推理服务连接</source>
        <translation>Inference Service Connection</translation>
    </message>
    <message>
        <source>服务端口</source>
        <translation>Service port</translation>
    </message>
    <message>
        <source>留空则自动探测（环境变量 FMD_PYTHON &gt; 配置 &gt; conda med-yolo）</source>
        <translation>Leave empty to auto-detect (env FMD_PYTHON &gt; settings &gt; conda med-yolo)</translation>
    </message>
    <message>
        <source>Python 解释器</source>
        <translation>Python interpreter</translation>
    </message>
    <message>
        <source>留空则按 &lt;应用目录&gt;/../../server/app.py 探测</source>
        <translation>Leave empty to probe &lt;app dir&gt;/../../server/app.py</translation>
    </message>
    <message>
        <source>服务脚本</source>
        <translation>Server script</translation>
    </message>
    <message>
        <source>默认推理参数</source>
        <translation>Default Inference Parameters</translation>
    </message>
    <message>
        <source>（自动选择 best）</source>
        <translation>(auto: pick best)</translation>
    </message>
    <message>
        <source>默认模型</source>
        <translation>Default model</translation>
    </message>
    <message>
        <source>置信度阈值</source>
        <translation>Confidence threshold</translation>
    </message>
    <message>
        <source>IOU 阈值</source>
        <translation>IoU threshold</translation>
    </message>
    <message>
        <source>推理尺寸</source>
        <translation>Inference size</translation>
    </message>
    <message>
        <source>保存并重启服务</source>
        <translation>Save and Restart Service</translation>
    </message>
    <message>
        <source>保存</source>
        <translation>Save</translation>
    </message>
    <message>
        <source>[设置] 已保存（端口 %1）</source>
        <translation>[settings] saved (port %1)</translation>
    </message>
    <message>
        <source>选择 Python 解释器</source>
        <translation>Select Python Interpreter</translation>
    </message>
    <message>
        <source>可执行文件 (*.exe);;所有文件 (*.*)</source>
        <translation>Executables (*.exe);;All files (*.*)</translation>
    </message>
    <message>
        <source>选择服务端脚本</source>
        <translation>Select Server Script</translation>
    </message>
    <message>
        <source>Python 脚本 (*.py);;所有文件 (*.*)</source>
        <translation>Python scripts (*.py);;All files (*.*)</translation>
    </message>
    <message>
        <source>界面语言</source>
        <translation>UI language</translation>
    </message>
    <message>
        <source>语言</source>
        <translation>Language</translation>
    </message>
    <message>
        <source>源码以中文编写，中文无需翻译文件；英文由 Qt Linguist 的 .ts/.qm 提供。
切换语言需要重建界面，保存后可点下方按钮立即重启应用。</source>
        <translation>Source strings are written in Chinese, so Chinese needs no translation file; English comes from Qt Linguist .ts/.qm files.
Switching language rebuilds the UI — after saving, use the button below to restart immediately.</translation>
    </message>
    <message>
        <source>立即重启应用</source>
        <translation>Restart now</translation>
    </message>
    <message>
        <source>设置</source>
        <translation type="unfinished">Settings</translation>
    </message>
    <message>
        <source>配置推理服务的连接方式与默认推理参数。修改后点「保存」生效；改动端口或解释器时请用「保存并重启服务」。</source>
        <translation>Configure how the client reaches the inference service and the default inference parameters. Click Save to apply; use &quot;Save and Restart Service&quot; when changing the port or interpreter.</translation>
    </message>
</context>
<context>
    <name>fmd::VideoWidget</name>
    <message>
        <source>尚未开始实时预览
选择摄像头后点击「打开」</source>
        <translation>No live preview yet
Choose a camera and click &quot;Open&quot;</translation>
    </message>
</context>
</TS>
