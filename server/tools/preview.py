"""
实时预览 —— 一条命令在浏览器里看到摄像头的检测画面。

为什么需要它：
  阶段 1/2 的服务端部分没有界面，光看日志和 JSON 无法判断"到底对不对"。
  浏览器原生支持 MJPEG（multipart/x-mixed-replace），所以不需要写任何前端代码
  就能看到带检测框的实时画面 —— 这是最快的验证手段。

  注意：这只是**验证工具**，不是产品界面。产品界面是 Qt 客户端，
  服务端刻意不提供 Web UI（保持"HMI 与视觉管线分离"的分工）。

用法：
    python server/tools/preview.py                 # 用本机摄像头 0
    python server/tools/preview.py --source 1      # 用摄像头 1
    python server/tools/preview.py --source data/test_video/mask_demo.mp4
    python server/tools/preview.py --source rtsp://192.168.1.10:554/stream
    python server/tools/preview.py --no-browser    # 只打印地址

Ctrl+C 退出，会自动关闭视频源。
"""

import argparse
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SERVER_DIR = ROOT / "server"


def api(port, path, payload=None, timeout=60):
    url = "http://127.0.0.1:%d%s" % (port, path)
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method="POST" if data else "GET")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def wait_healthy(port, timeout=180.0):
    """等服务端就绪。首次启动要加载 torch/ultralytics，可能要十几秒。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            api(port, "/health", timeout=3)
            return True
        except Exception:                              # noqa: BLE001
            time.sleep(0.5)
    return False


def main():
    # 行缓冲：默认情况下 Python 重定向到文件时是全缓冲的，
    # 用户把输出重定向到日志后会"什么都看不到"，误以为程序没跑。
    try:
        sys.stdout.reconfigure(line_buffering=True)
        sys.stderr.reconfigure(line_buffering=True)
    except Exception:                                  # noqa: BLE001
        pass

    parser = argparse.ArgumentParser(description="实时预览（浏览器）")
    parser.add_argument("--source", default="0",
                        help="摄像头序号 / 视频文件路径 / RTSP 地址")
    parser.add_argument("--port", type=int, default=8756)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    # 解析相对路径（相对仓库根），让 --source data/test_video/x.mp4 这类写法可用
    source = args.source
    if not str(source).isdigit() and "://" not in str(source):
        candidate = (ROOT / source) if not Path(source).is_absolute() else Path(source)
        if candidate.exists():
            source = str(candidate)

    server_proc = None
    try:
        api(args.port, "/health", timeout=2)
        print("  复用已在运行的服务端（端口 %d）" % args.port)
    except Exception:                                  # noqa: BLE001
        print("  启动服务端（端口 %d）… 首次要加载模型，请稍候" % args.port)
        server_proc = subprocess.Popen(
            [sys.executable, "app.py", "--port", str(args.port)],
            cwd=str(SERVER_DIR),
        )
        if not wait_healthy(args.port):
            print("  [FAIL] 服务端 180 秒内未就绪")
            return 1

    print("  打开视频源: %s" % source)
    try:
        opened = api(args.port, "/cameras/open",
                     {"source": source, "name": Path(str(source)).name or str(source)})
    except urllib.error.HTTPError as exc:
        print("  [FAIL] 打不开: %s" % exc.read().decode("utf-8", "ignore"))
        return 1

    if not opened.get("success"):
        print("  [FAIL] %s" % opened.get("error"))
        return 1

    cam_id = opened["cam_id"]
    url = "http://127.0.0.1:%d/cameras/%s/stream.mjpg" % (args.port, cam_id)
    print("  视频源 id: %s   后端: %s" % (cam_id, opened["stats"].get("backend")))
    print()
    print("  ┌──────────────────────────────────────────────────────────┐")
    print("  │  在浏览器打开下面这个地址（Chrome/Edge/Firefox 都行）：   │")
    print("  └──────────────────────────────────────────────────────────┘")
    print()
    print("      %s" % url)
    print()

    if not args.no_browser:
        try:
            webbrowser.open(url)
            print("  已尝试自动打开浏览器。若没弹出，手动复制上面的地址。")
        except Exception:                              # noqa: BLE001
            print("  自动打开浏览器失败，请手动复制地址。")

    print()
    print("  实时状态（Ctrl+C 退出）：")
    print("    %-8s %-10s %-10s %-10s %-8s" %
          ("采集FPS", "推理ms", "端到端ms", "JPEG KB", "已处理"))
    try:
        while True:
            time.sleep(2)
            st = api(args.port, "/cameras/%s/stats" % cam_id)
            live = st.get("live", {})
            print("    %-8.1f %-10.1f %-10.1f %-10.1f %-8d" % (
                st["stats"]["fps"], live.get("infer_ms", 0), live.get("e2e_ms", 0),
                live.get("jpeg_kb", 0), live.get("processed", 0)))
    except KeyboardInterrupt:
        print()
        print("  正在关闭视频源…")
    finally:
        try:
            api(args.port, "/cameras/%s/close" % cam_id, {}, timeout=10)
            print("  视频源已关闭")
        except Exception:                              # noqa: BLE001
            pass
        if server_proc is not None:
            print("  停止服务端…")
            server_proc.terminate()
            try:
                server_proc.wait(timeout=8)
            except subprocess.TimeoutExpired:
                server_proc.kill()
    return 0


if __name__ == "__main__":
    sys.exit(main())
